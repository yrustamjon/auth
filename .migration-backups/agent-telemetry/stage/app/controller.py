"""
windows/bioguard_api.py â€” pywebview JS API

TUZATISHLAR:
  1. _admin_token â€” __init__ da bo'sh string sifatida initiallanadi
  2. _face_polling va _finger_polling â€” alohida flaglar (konflikt yo'q)
  3. start_session xatosida retry taklif qilinadi
  4. relock_system + start_session oflayn holatda UI qotib qolmaydi
"""

import json
import logging
import threading
import time

from api.camera import check_camera
from api.client import get_default_client
from core.auth.errors import AuthenticationError
from core.auth.manager import AuthenticationManager
from core.auth.models import AuthContext, AuthenticationPolicy
from core.cert import is_activated
from core.config import DEMO_MODE, DEV_MODE, DEVICE_UUID, USERNAME
from core.network.errors import BackendApiError, BackendResponseError
from core.offline import verify_offline, has_offline_creds
from platform_adapters.base import PlatformAdapter
from platform_adapters.factory import get_platform_adapter
from providers.face import BioGuardFaceProvider
from providers.remote_approval import RemoteApprovalProvider


LOGGER = logging.getLogger(__name__)


class BioGuardAPI:

    def __init__(
        self,
        window_ref,
        *,
        api_client=None,
        authentication_manager: AuthenticationManager | None = None,
        platform_adapter: PlatformAdapter | None = None,
    ):
        self._window        = window_ref
        self._api_client = api_client or get_default_client()
        self._authentication = authentication_manager or AuthenticationManager([
            BioGuardFaceProvider(self._api_client),
            RemoteApprovalProvider(self._api_client),
        ])
        self._platform = platform_adapter or get_platform_adapter()
        self._session_id    = None
        self._username = USERNAME
        self._face_polling  = False   # FIX: alohida flag (yuz uchun)
        self._finger_polling = False  # FIX: alohida flag (barmoq izi uchun)
        self._polling       = False   # umumiy (eski kodni buzmaslik uchun)
        self._timeout       = 300
        self._admin_token   = ""      # FIX: __init__ da initiallanadi
        self._internet_monitor_started = False
        self._unlock_scheduled = False
        self._enrollment_required = False

    # â”€â”€ Config â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def get_config(self) -> str:
        from core.offline import has_personal_offline
        return json.dumps({
            "username":             self._username,
            "pc_id":                DEVICE_UUID,
            "camera_ok":            check_camera(),
            "dev_mode":             DEV_MODE,
            "demo_mode":            DEMO_MODE,
            "activated":            is_activated() and not self._enrollment_required,
            "online":               self._api_client.is_online(),
            "has_offline":          has_offline_creds(),
            "has_personal_offline": has_personal_offline(),
        })

    # â”€â”€ Sessiya (doc 03) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def start_session(self):
        """
        FIX: Xato bo'lsa onError o'rniga onSessionError chaqiriladi
        â€” UI retry tugmasi ko'rsatadi, qotib qolmaydi.
        Oflayn holatda: onOfflineMode chaqiriladi.
        """
        def _run():
            self._session_id = None
            # Oldin internet bor-yo'qligini tekshir
            if not self._api_client.is_online():
                # Oflayn rejim â€” UI oflayn forma ko'rsatadi
                self._js("App.onOfflineMode()")
                return
            try:
                data = self._api_client.start_session(USERNAME, DEVICE_UUID)
                username = data.get('username', USERNAME)
                if not isinstance(username, str) or not username.strip():
                    raise ValueError('Backend session username required')
                self._username = username
                self._session_id = data.get("session_id", "")
                self._unlock_scheduled = False
                if "timeout" in data:
                    self._timeout = int(data["timeout"])
                if not self._internet_monitor_started:
                    self.start_internet_monitor()
                self._js(f"App.onSessionReady('{self._session_id}')")
            except BackendResponseError as error:
                try:
                    response = json.loads(error.response_body or "{}")
                except (TypeError, json.JSONDecodeError):
                    response = {}
                if not isinstance(response, dict):
                    response = {}
                if error.status_code == 409 and response.get("code") == "AGENT_ENROLLMENT_REQUIRED":
                    self._enrollment_required = True
                    self._face_polling = False
                    self._finger_polling = False
                    self._js("App.onEnrollmentRequired()")
                    return
                else:
                    message = response.get("detail") or str(error)
                self._js(f"App.onSessionError('{self._esc(str(message))}')")
            except Exception as e:
                # FIX: retry taklif qilinadi
                self._js(f"App.onSessionError('{self._esc(str(e))}')")
        threading.Thread(target=_run, daemon=True).start()

    # â”€â”€ Yuz â€” webcam (doc 03) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def capture_face(self, image_b64: str):
        def _run():
            try:
                self._js("App.setStatus('verifying', 'Analyzing face...')")
                result = self._authentication.authenticate(
                    AuthContext(
                        user_id=self._username,
                        device_id=DEVICE_UUID,
                        session_id=self._session_id,
                        metadata={"image": image_b64},
                    ),
                    self._provider_policy("bioguard_face"),
                    requested_provider_id="bioguard_face",
                )
                self._handle_auth_result({
                    "status": result.status,
                    **result.metadata,
                })
            except (AuthenticationError, BackendApiError) as error:
                LOGGER.warning("Face authentication failed: %s", type(error).__name__)
                self._js(f"App.onFaceRetry('{self._esc(str(error))}')")
            except Exception as error:
                LOGGER.exception("Unexpected face authentication failure")
                self._js(f"App.onFaceRetry('{self._esc(str(error))}')")
        threading.Thread(target=_run, daemon=True).start()

    # â”€â”€ Yuz â€” telefon QR (doc 03) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def start_face_qr_poll(self):
        if not self._session_id:
            self._js("App.onError('No session')")
            return
        qr_url = self._remote_approval_url("face")
        if qr_url is None:
            return
        self._js(f"App.renderFaceQR('{qr_url}')")
        # FIX: _face_polling â€” barmoq izi polling ni to'xtatmaydi
        self._face_polling = True
        threading.Thread(target=self._face_qr_poll_loop, daemon=True).start()

    def _face_qr_poll_loop(self):
        self._remote_poll_loop("face", "_face_polling", "App.updateFaceTimer")

    # â”€â”€ Barmoq izi â€” telefon QR (doc 03) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def start_finger_poll(self):
        if not self._session_id:
            self._js("App.onError('No session')")
            return
        qr_url = self._remote_approval_url("fingerprint")
        if qr_url is None:
            return
        self._js(f"App.renderQR('{qr_url}')")
        # FIX: _finger_polling â€” yuz polling ni to'xtatmaydi
        self._finger_polling = True
        threading.Thread(target=self._poll_loop, daemon=True).start()

    def stop_face_poll(self):
        self._face_polling = False

    def stop_finger_poll(self):
        # FIX: faqat barmoq izi polling ni to'xtatadi
        self._finger_polling = False

    def _poll_loop(self):
        self._remote_poll_loop("fingerprint", "_finger_polling", "App.updateTimer")

    def _remote_poll_loop(self, approval_type: str, polling_flag: str, timer_callback: str):
        elapsed, limit = 0, 120
        while getattr(self, polling_flag) and elapsed < limit:
            try:
                result = self._authentication.authenticate(
                    self._remote_context(approval_type),
                    self._provider_policy("remote_approval"),
                    requested_provider_id="remote_approval",
                )
                if result.success:
                    setattr(self, polling_flag, False)
                    self._complete_verification()
                    return
                if result.status == "expired":
                    setattr(self, polling_flag, False)
                    self._js("App.onQRExpired()")
                    return
                if result.status in ("blocked_user", "blocked_device"):
                    setattr(self, polling_flag, False)
                    self._handle_blocked(result.status)
                    return
            except (AuthenticationError, BackendApiError) as error:
                LOGGER.warning("Remote approval polling failed: %s", type(error).__name__)
            except Exception:
                LOGGER.exception("Unexpected remote approval polling failure")
            time.sleep(2)
            elapsed += 2
            self._js(f"{timer_callback}({limit - elapsed})")
        if getattr(self, polling_flag):
            setattr(self, polling_flag, False)
            self._js("App.onQRExpired()")

    def _remote_context(self, approval_type: str) -> AuthContext:
        return AuthContext(
            user_id=self._username,
            device_id=DEVICE_UUID,
            session_id=self._session_id,
            metadata={"approval_type": approval_type},
        )

    def _remote_approval_url(self, approval_type: str) -> str | None:
        context = self._remote_context(approval_type)
        try:
            provider = self._authentication.select_provider(
                self._provider_policy("remote_approval"),
                requested_provider_id="remote_approval",
            )
            approval_url = getattr(provider, "approval_url", None)
            if not callable(approval_url):
                raise AuthenticationError("Selected provider cannot render remote approval")
            return approval_url(context)
        except (AuthenticationError, BackendApiError) as error:
            LOGGER.warning("Remote approval cannot start: %s", type(error).__name__)
            self._js(f"App.onError('{self._esc(str(error))}')")
            return None

    @staticmethod
    def _provider_policy(provider_id: str) -> AuthenticationPolicy:
        """Legacy flows remain explicit single-provider choices in Phase 2."""
        return AuthenticationPolicy(
            allowed_provider_ids=frozenset({provider_id}),
            authentication_priority=(provider_id,),
            allow_fallback=False,
        )

    # â”€â”€ Aktivatsiya (doc 02) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def activate_org(self, activation_code: str):
        def _run():
            try:
                from core.activation import activate_org
                self._js("App.onSetupStatus('Serverga ulanmoqda...')")
                activate_org(activation_code, force=self._enrollment_required)
                self._enrollment_required = False
                self._js("App.onActivated()")
            except Exception as e:
                self._js(f"App.onSetupError('{self._esc(str(e))}')")
        threading.Thread(target=_run, daemon=True).start()

    def activate_personal(self, email: str, password: str):
        def _run():
            try:
                from core.activation import activate_personal
                self._js("App.onSetupStatus('Serverga ulanmoqda...')")
                activate_personal(email, password, force=self._enrollment_required)
                self._enrollment_required = False
                self._js("App.onActivated()")
            except Exception as e:
                self._js(f"App.onSetupError('{self._esc(str(e))}')")
        threading.Thread(target=_run, daemon=True).start()

    # â”€â”€ Personal offline â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def set_personal_offline_password(self, password: str):
        def _run():
            try:
                from core.offline import set_personal_offline_password
                set_personal_offline_password(password)
                self._js("App.onPersonalOfflineSet()")
            except Exception as e:
                self._js(f"App.onPersonalOfflineError('{self._esc(str(e))}')")
        threading.Thread(target=_run, daemon=True).start()

    def personal_offline_login(self, password: str):
        def _run():
            from core.offline import verify_personal_offline
            if verify_personal_offline(password):
                self._complete_verification()
            else:
                self._js("App.onOfflineRetry('Parol noto\\'g\\'ri')")
        threading.Thread(target=_run, daemon=True).start()

    # â”€â”€ Internet monitoring (doc 06) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def start_internet_monitor(self):
        """Biometrik jarayonida internet uzilsa offline ekraniga o'tadi."""
        if self._internet_monitor_started:
            return
        self._internet_monitor_started = True

        def _monitor():
            was_online = True
            while True:
                time.sleep(5)
                online = self._api_client.is_online()
                if was_online and not online:
                    self._js("App.onInternetLost()")
                elif not was_online and online:
                    self._js("App.onInternetRestored()")
                was_online = online
        threading.Thread(target=_monitor, daemon=True).start()

    # â”€â”€ Offline login (doc 06) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def offline_login(self, username: str, password: str):
        def _run():
            if self._api_client.is_online():
                self._js("App.onOfflineRetry('Internet mavjud â€” oddiy biometrik ishlating')")
                return
            if verify_offline(username, password):
                self._complete_verification()
            else:
                self._js("App.onOfflineRetry('Login yoki parol noto\\'g\\'ri')")
        threading.Thread(target=_run, daemon=True).start()

    # â”€â”€ Auto-lock (doc 04) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def start_autolock_monitor(self):
        def _on_warn(seconds_left):
            self._js(f"App.onAutolockWarning({seconds_left})")

        def _on_lock():
            threading.Thread(target=self._platform.lock_session, daemon=True).start()

        self._platform.start_autolock(self._timeout, _on_warn, _on_lock)

    def extend_session(self):
        """'Davom etish' â€” auto-lock timer reset."""
        stop_autolock()
        self.start_autolock_monitor()

    # â”€â”€ Device polling â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def start_device_poll(self):
        from core.device_poll import start_device_poll

        def _on_relock(status: str):
            from core.device_poll import stop_device_poll
            stop_device_poll()

            if status == "blocked_device":
                self._js("App.onBlocked('Bu qurilma administrator tomonidan o\\'chirildi')")
            elif status == "blocked_user":
                self._js("App.onBlocked('Hisobingiz administrator tomonidan bloklandi')")
            elif status == "revoked":
                self._js("App.onBlocked('PC sertifikati bekor qilindi. IT ga murojaat qiling')")
            else:
                self._js("App.onBlocked('Qurilma yoki hisob o\\'chirildi')")

            time.sleep(2)
            threading.Thread(target=self._platform.lock_session, daemon=True).start()

        start_device_poll(_on_relock, interval=30)

    # â”€â”€ Qulfni ochish â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def hide_lock(self):
        self._unlock_scheduled = False
        self._platform.unlock_session()
        self._window.hide()
        from services.disable_manager import set_lock_state
        set_lock_state("unlocked")
        self.start_autolock_monitor()
        self.start_device_poll()

    # â”€â”€ Admin panel â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def admin_login(self, password: str):
        def _run():
            try:
                from core.offline import verify_admin_password, get_admin_token
                if verify_admin_password(password):
                    token = get_admin_token()
                    # FIX: __init__ da allaqachon "" ga set â€” bu yerda yangilaydi
                    self._admin_token = token
                    self._js(f"App.onAdminLoginOk('{self._esc(token)}')")
                else:
                    self._js("App.onAdminLoginFail('Parol noto\\'g\\'ri')")
            except Exception as e:
                self._js(f"App.onAdminLoginFail('{self._esc(str(e))}')")
        threading.Thread(target=_run, daemon=True).start()

    def get_lan_peers(self) -> str:
        try:
            from services.lan_server import get_peers
            return json.dumps(get_peers())
        except Exception:
            return "[]"

    def refresh_lan_peer(self, ip: str) -> str:
        def _run():
            try:
                import urllib.request
                req = urllib.request.Request(
                    f"http://{ip}:7749/status",
                    method="GET"
                )
                with urllib.request.urlopen(req, timeout=3) as r:
                    info = json.loads(r.read())
                    info["ip"] = ip
                    from services.lan_server import _update_peer
                    _update_peer(info)
                    data = json.dumps(info)
                    self._js(f"App.onPeerUpdated('{self._esc(data)}')")
            except Exception:
                self._js(f"App.onPeerOffline('{ip}')")
        threading.Thread(target=_run, daemon=True).start()

    def lan_command(self, ip: str, cmd: str):
        def _run():
            try:
                import urllib.request
                # FIX: _admin_token __init__ da "" ga set â€” getattr kerak emas
                token   = self._admin_token
                payload = json.dumps({"cmd": cmd, "token": token}).encode()
                req = urllib.request.Request(
                    f"http://{ip}:7749/command",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=5) as r:
                    result = json.loads(r.read())
                    ok = result.get("ok", False)
                self._js(f"App.onLanResult('{ip}', '{cmd}', {'true' if ok else 'false'})")
            except Exception:
                self._js(f"App.onLanResult('{ip}', '{cmd}', false)")
        threading.Thread(target=_run, daemon=True).start()

    def lan_command_all(self, cmd: str):
        def _run():
            try:
                from services.lan_server import get_peers
                import urllib.request
                # FIX: _admin_token __init__ da "" ga set
                token = self._admin_token
                peers = get_peers()
                for p in peers:
                    ip = p.get("ip", "")
                    if not ip or p.get("state") == "offline":
                        continue
                    try:
                        payload = json.dumps({"cmd": cmd, "token": token}).encode()
                        req = urllib.request.Request(
                            f"http://{ip}:7749/command",
                            data=payload,
                            headers={"Content-Type": "application/json"},
                            method="POST",
                        )
                        with urllib.request.urlopen(req, timeout=5) as r:
                            pass
                    except Exception:
                        pass
                self._js("App.onLanAllDone()")
            except Exception as e:
                self._js(f"App.onError('{self._esc(str(e))}')")
        threading.Thread(target=_run, daemon=True).start()

    def set_admin_password(self, password: str):
        def _run():
            try:
                from core.offline import set_admin_password
                set_admin_password(password)
                self._js("App.onAdminPasswordSet()")
            except Exception as e:
                self._js(f"App.onAdminPasswordError('{self._esc(str(e))}')")
        threading.Thread(target=_run, daemon=True).start()

    def dev_unlock(self):
        self.hide_lock()

    def dev_exit(self):
        from services.telemetry import stop_telemetry
        stop_telemetry('prerelease_exit')
        self._platform.stop_autolock()
        self._platform.unlock_session()
        self._window.destroy()

    # â”€â”€ Internal â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def _handle_auth_result(self, data: dict):
        status = data.get("status", "")
        if status == "verified":
            self._complete_verification()
        elif status == "blocked_user":
            self._js("App.onBlocked('Hisobingiz bloklangan, IT ga murojaat')")
        elif status == "blocked_device":
            self._js("App.onBlocked('Bu qurilma o\\'chirilgan')")
        else:
            msg = self._esc(data.get("detail", "Biometric not recognized"))
            self._js(f"App.onFaceRetry('{msg}')")

    def _handle_blocked(self, status: str):
        if status == "blocked_user":
            self._js("App.onBlocked('Hisobingiz bloklangan, IT ga murojaat')")
        else:
            self._js("App.onBlocked('Bu qurilma o\\'chirilgan')")

    def _complete_verification(self):
        if self._unlock_scheduled:
            return
        self._unlock_scheduled = True
        self._js("App.onVerified()")

        def _unlock():
            time.sleep(3)
            try:
                self.hide_lock()
            except Exception:
                pass
            finally:
                self._unlock_scheduled = False

        threading.Thread(target=_unlock, daemon=True).start()

    def _js(self, code: str):
        try:
            self._window.evaluate_js(code)
        except Exception:
            pass

    @staticmethod
    def _esc(s: str) -> str:
        return s.replace("'", "\\'").replace("\n", " ")


