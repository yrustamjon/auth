"""Asynchronous lifecycle state exposed to native setup; no filesystem copying."""
import threading
import json
from core.network.errors import BackendResponseError, BackendUnavailableError


def failure_message(error):
    if isinstance(error, BackendUnavailableError):
        return 'Serverga ulanib bo‘lmadi. Internetni tekshirib, qayta urinib ko‘ring. Oldingi amal holati saqlanadi.'
    if isinstance(error, BackendResponseError):
        try:
            payload=json.loads(error.response_body or '{}')
            code=payload.get('detail') if isinstance(payload,dict) else None
        except (ValueError,TypeError):
            code=None
        messages={
            'INVALID_REMOVAL_CODE':'O‘chirish kodi noto‘g‘ri yoki muddati tugagan. Org token emas, shu qurilma uchun admin panelida yaratilgan o‘chirish kodini kiriting.',
            'DEVICE_NOT_REMOVABLE':'Qurilma o‘chirish holatida. Avvalgi operatsiyani davom ettiring yoki admin panelida holatni tekshiring.',
            'ISSUER_NO_LONGER_AUTHORIZED':'Kodni bergan administratorning ruxsati bekor qilingan. Yangi ruxsat kerak.',
            'ENROLLMENT_CHANGED':'Qurilma aktivatsiyasi o‘zgargan. Joriy qurilma uchun yangi o‘chirish kodi kerak.',
            'OPERATION_NOT_FOUND':'Avvalgi o‘chirish operatsiyasi topilmadi. Yangi o‘chirish kodini kiriting.',
        }
        if isinstance(code,str) and code in messages:return messages[code]
    return 'Server yoki himoyalangan saqlash bilan muammo. Qayta urinib ko‘ring.'


class LifecycleBroker:
    def __init__(self, mode, activation, removal, target_sid, target_user):
        if mode not in {'install', 'uninstall'}:
            raise ValueError('Unsupported lifecycle mode')
        self.mode, self.activation, self.removal = mode, activation, removal
        self.value = {'state': 'idle', 'target_sid': target_sid, 'target_user': target_user}
        self.thread = None
        self.lock = threading.Lock()

    def snapshot(self):
        with self.lock:
            return dict(self.value)

    def join(self):
        if self.thread:
            self.thread.join(20)

    def dispatch(self, command, secret=''):
        if command == 'state':
            return self.snapshot()
        allowed = {'inspect', 'activate', 'verify'} if self.mode == 'install' else {'check', 'begin', 'resume', 'cleanup'}
        if command not in allowed:
            raise ValueError('Command not permitted in this lifecycle mode')
        if command == 'cleanup' and self.snapshot()['state'] != 'approved':
            raise ValueError('Online removal approval required')
        if self.thread and self.thread.is_alive():
            return self.snapshot()
        with self.lock:
            self.value['state'] = 'pending'
            self.value.pop('message', None)

        def work():
            try:
                if self.mode == 'install':
                    result = self.activation(secret if command == 'activate' else None)
                    state = 'ready'
                elif command == 'check':
                    result = self.removal.check(secret)
                    state = 'approved' if result.get('state') == 'removal_pending' else 'checked'
                elif command == 'begin':
                    result, state = self.removal.begin(secret), 'approved'
                    if result.get('state') != 'removal_pending':
                        raise ValueError('Unexpected removal state')
                elif command == 'resume':
                    result = self.removal.resume()
                    if result.get('state') not in {'removal_pending', 'removed'}:
                        raise ValueError('Removal not approved')
                    state = 'approved' if result['state'] == 'removal_pending' else 'removed'
                else:
                    result, state = self.removal.cleanup_and_complete(), 'removed'
                with self.lock:
                    self.value.update({key: value for key, value in result.items() if key in {'organization', 'device_uuid', 'operation_id'}})
                    self.value['state'] = state
                    if self.mode == 'uninstall' and state == 'approved':
                        self.value['message'] = 'Server o‘chirishga ruxsatni tasdiqladi. Shu operatsiya davom ettirilmoqda.'
                    elif self.mode == 'uninstall' and state == 'checked':
                        self.value['message'] = 'Kod tasdiqlandi. O‘chirish tugmasini bosing.'
            except Exception as error:
                # Backend error bodies can contain secrets. Expose only fixed UI
                # messages; the receipt retains recovery state independently.
                with self.lock:
                    self.value.update(state='error', message=failure_message(error))
        self.thread = threading.Thread(target=work, daemon=False)
        self.thread.start()
        return self.snapshot()
