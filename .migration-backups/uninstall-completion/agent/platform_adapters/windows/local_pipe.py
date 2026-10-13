"""Local, session-bound message pipes with bounded, cancellable I/O."""
import json
import queue
import struct
import threading
import time

import pywintypes
import win32api
import win32con
import win32event
import win32file
import win32pipe
import win32security
import win32ts

from services.local_protocol import (MAX_FRAME_BYTES, MAX_REQUESTS_PER_CONNECTION,
    PeerIdentity, ProtocolError, RequestHistory, decode_request, dispatch_request)
from platform_adapters.windows.service_security import pipe_sddl, _service_sid

HELLO = b'BIOGUARD/1'
IO_TIMEOUT = 5.0
PIPE_PREFIX = r'\\.\pipe\BioGuardAuthority-v1-'


def peer_identity(handle):
    # Windows impersonates the sender of the LAST READ message. Call after each read.
    win32pipe.ImpersonateNamedPipeClient(handle)
    token = None
    try:
        token = win32security.OpenThreadToken(win32api.GetCurrentThread(), win32con.TOKEN_QUERY, True)
        sid = win32security.GetTokenInformation(token, win32security.TokenUser)[0]
        session = win32security.GetTokenInformation(token, win32security.TokenSessionId)
        level = win32security.GetTokenInformation(token, win32security.TokenImpersonationLevel)
        if session <= 0 or level < win32security.SecurityIdentification:
            raise PermissionError('Noninteractive or anonymous peer')
        return PeerIdentity(session, win32security.ConvertSidToStringSid(sid))
    finally:
        try:
            win32security.RevertToSelf()
        except OSError as error:
            raise RuntimeError('Cannot revert client impersonation') from error
        finally:
            if token is not None:
                token.Close()


def interactive_sessions():
    result = {}
    for session in win32ts.WTSEnumerateSessions(None, 1, 0):
        number = session['SessionId']
        if number <= 0 or session['State'] not in (win32ts.WTSActive, win32ts.WTSConnected):
            continue
        username = win32ts.WTSQuerySessionInformation(None, number, win32ts.WTSUserName)
        if not username:
            continue
        domain = win32ts.WTSQuerySessionInformation(None, number, win32ts.WTSDomainName)
        sid, _, _ = win32security.LookupAccountName(None, domain + '\\' + username if domain else username)
        result[number] = PeerIdentity(number, win32security.ConvertSidToStringSid(sid))
    if len(result) > 64:
        raise RuntimeError('Session limit exceeded')
    return result


def _operation(handle, stop, start):
    overlapped = pywintypes.OVERLAPPED()
    overlapped.hEvent = win32event.CreateEvent(None, True, False, None)
    pending = False
    try:
        try:
            value = start(overlapped)
            if value == 535:
                return None, 0
            pending = True
        except pywintypes.error as error:
            if error.winerror == 535:  # ConnectNamedPipe: client connected before call
                return None, 0
            raise
        deadline = time.monotonic() + IO_TIMEOUT
        while win32event.WaitForSingleObject(overlapped.hEvent, 100) == win32event.WAIT_TIMEOUT:
            if stop.is_set() or time.monotonic() >= deadline:
                raise TimeoutError('Pipe operation cancelled or timed out')
        count = win32file.GetOverlappedResult(handle, overlapped, False)
        pending = False
        return value, count
    finally:
        if pending:
            try:
                win32file.CancelIoEx(handle, overlapped)
            except pywintypes.error:
                pass
            try:
                win32file.GetOverlappedResult(handle, overlapped, True)
            except pywintypes.error:
                pass
        overlapped.hEvent.Close()


def _read(handle, stop):
    value, count = _operation(handle, stop,
        lambda ov: win32file.ReadFile(handle, MAX_FRAME_BYTES + 1, ov))
    data = bytes(value[1])[:count]
    if not data or len(data) > MAX_FRAME_BYTES:
        raise ProtocolError('INVALID_FRAME')
    return data


def _write(handle, stop, value):
    payload = json.dumps(value, separators=(',', ':')).encode('utf-8')
    data = struct.pack('!I', len(payload)) + payload
    _, count = _operation(handle, stop, lambda ov: win32file.WriteFile(handle, data, ov))
    if count != len(data):
        raise OSError('Incomplete pipe write')


class NamedPipeServer:
    def __init__(self):
        self.failures = queue.Queue()

    def _connection(self, handle, stop, authority, expected):
        if _read(handle, stop) != HELLO or peer_identity(handle) != expected:
            raise PermissionError('Invalid handshake')
        _write(handle, stop, {'version': 1, 'generation': authority.generation,
                             'session_id': expected.session_id, 'user_sid': expected.user_sid})
        history = RequestHistory()
        for _ in range(MAX_REQUESTS_PER_CONNECTION):
            if stop.is_set():
                return
            frame = _read(handle, stop)
            peer = peer_identity(handle)
            if peer != expected or interactive_sessions().get(peer.session_id) != expected:
                raise PermissionError('Session identity changed')
            try:
                request = decode_request(frame)
                response = dispatch_request(request, peer, authority, history)
            except ProtocolError as error:
                _write(handle, stop, {'ok': False, 'error': str(error)})
                return
            _write(handle, stop, response)

    def _worker(self, stop, authority, expected):
        try:
            security = pywintypes.SECURITY_ATTRIBUTES()
            security.SECURITY_DESCRIPTOR = win32security.ConvertStringSecurityDescriptorToSecurityDescriptor(
                pipe_sddl(_service_sid(), expected.user_sid), 1)
            while not stop.is_set():
                # FIRST_PIPE_INSTANCE makes pre-created fake servers a detectable failure.
                handle = win32pipe.CreateNamedPipe(PIPE_PREFIX + str(expected.session_id),
                    win32pipe.PIPE_ACCESS_DUPLEX | win32file.FILE_FLAG_OVERLAPPED | 0x00080000,
                    win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE |
                    win32pipe.PIPE_WAIT | 0x8, 1, MAX_FRAME_BYTES, MAX_FRAME_BYTES, 5000, security)
                try:
                    try:
                        _operation(handle, stop, lambda ov: win32pipe.ConnectNamedPipe(handle, ov))
                        self._connection(handle, stop, authority, expected)
                    except (pywintypes.error, TimeoutError, ProtocolError, PermissionError):
                        # Untrusted client failure: close without authorizing anything.
                        pass
                finally:
                    handle.Close()
        except Exception as error:
            self.failures.put(error)

    def serve(self, stop_event, authority):
        workers = {}
        def retire(number):
            peer, stop, thread = workers.pop(number)
            stop.set()
            thread.join(IO_TIMEOUT + 2)
            if thread.is_alive():
                raise RuntimeError('Pipe worker failed to stop')
            authority.invalidate_session(number)
        try:
            while not stop_event.is_set():
                if not self.failures.empty():
                    raise self.failures.get()
                sessions = interactive_sessions()  # Errors fail service closed, never use stale cache.
                for number in list(workers):
                    if workers[number][0] != sessions.get(number):
                        retire(number)
                for number, peer in sessions.items():
                    if number not in workers:
                        stop = threading.Event()
                        thread = threading.Thread(target=self._worker,
                            args=(stop, authority, peer), daemon=True)
                        workers[number] = (peer, stop, thread)
                        thread.start()
                stop_event.wait(1)
        finally:
            # Signal all first so shutdown duration does not scale with session count.
            for _, stop, _ in workers.values():
                stop.set()
            for number in list(workers):
                retire(number)
