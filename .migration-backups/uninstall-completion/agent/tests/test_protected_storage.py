import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from storage import legacy_windows_cert as storage


class ProtectedStorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name, value in dict(CERT_DIR=str(self.root), CERT_FILE=str(self.root/'cert.json'),
                               KEY_FILE=str(self.root/'private.pem'),KEY_FILE_ENC=str(self.root/'private.pem.dpapi')).items():
            p=patch.object(storage,name,value);p.start();self.addCleanup(p.stop)

    def protection(self):
        return patch.object(storage,'_dpapi_encrypt',side_effect=lambda b:b'protected:'+b), patch.object(storage,'_dpapi_decrypt',side_effect=lambda b:b.removeprefix(b'protected:'))

    def test_dpapi_failure_writes_nothing(self):
        with patch.object(storage,'_dpapi_encrypt',return_value=None):
            with self.assertRaises(OSError): storage.save_cert({'cert_id':'a'},'secret')
        self.assertEqual(list(self.root.iterdir()),[])

    def test_verification_failure_preserves_existing_credential(self):
        a,b=self.protection()
        with a,b: storage.save_cert({'cert_id':'a'},'first')
        with patch.object(storage,'_dpapi_encrypt',return_value=b'bad'),patch.object(storage,'_dpapi_decrypt',return_value=None):
            with self.assertRaises(OSError): storage.save_cert({'cert_id':'b'},'second')
        a,b=self.protection()
        with a,b:
            self.assertEqual(storage.load_cert()['cert_id'],'a')
            self.assertEqual(storage._load_private_key_bytes(),b'first')
        self.assertFalse(Path(storage.KEY_FILE).exists())

    def test_protected_round_trip_and_replace_failure(self):
        a,b=self.protection()
        with a,b:
            storage.save_cert({'cert_id':'a'},'first')
            with patch.object(storage.os,'replace',side_effect=OSError('disk failure')):
                with self.assertRaises(OSError): storage.save_cert({'cert_id':'b'},'second')
            self.assertEqual(storage.load_cert()['cert_id'],'a')
            self.assertEqual(storage._load_private_key_bytes(),b'first')
        self.assertFalse(Path(storage.KEY_FILE).exists())

    def test_legacy_migration_verifies_before_deleting_plaintext(self):
        Path(storage.KEY_FILE).write_bytes(b'legacy')
        Path(storage.CERT_FILE).write_text(json.dumps({'cert_id':'legacy-id'}))
        with patch.object(storage,'_dpapi_encrypt',return_value=None):
            self.assertIsNone(storage.load_cert())
        self.assertTrue(Path(storage.KEY_FILE).exists())
        a,b=self.protection()
        with a,b:
            self.assertEqual(storage.load_cert()['cert_id'],'legacy-id')
            self.assertEqual(storage._load_private_key_bytes(),b'legacy')
        self.assertFalse(Path(storage.KEY_FILE).exists())
        self.assertFalse(Path(storage.CERT_FILE).exists())

    def test_failed_unprotect_never_uses_plaintext_fallback(self):
        Path(storage.KEY_FILE_ENC).write_bytes(b'bad')
        Path(storage.KEY_FILE).write_bytes(b'plaintext')
        with patch.object(storage,'_dpapi_decrypt',return_value=None):
            self.assertIsNone(storage._load_private_key_bytes())

@unittest.skipUnless(__import__('sys').platform=='win32','Requires native Windows DPAPI')
class NativeProtectedStorageTests(unittest.TestCase):
    setUp = ProtectedStorageTests.setUp
    def test_real_dpapi_bundle_roundtrip_and_corruption_fail_closed(self):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        pem=key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()).decode()
        storage.save_cert({'cert_id':'synthetic-native','pc_id':'synthetic-pc'},pem)
        self.assertEqual(storage.load_cert()['cert_id'],'synthetic-native')
        self.assertEqual(storage._load_private_key_bytes(),pem.encode())
        self.assertFalse(Path(storage.KEY_FILE).exists())
        path=Path(storage._bundle_path());data=bytearray(path.read_bytes());data[-1]^=1;path.write_bytes(data)
        self.assertIsNone(storage.load_cert());self.assertIsNone(storage._load_private_key_bytes())

class DpapiByteMarshallingTests(unittest.TestCase):
    def test_native_blob_preserves_high_bit_bytes(self):
        import ctypes
        from types import SimpleNamespace
        buffers=[]
        def transform(inp,*args):
            source=inp._obj
            raw=ctypes.string_at(source.pbData,source.cbData)
            output=args[-1]._obj
            buffer=ctypes.create_string_buffer(raw);buffers.append(buffer)
            output.cbData=len(raw)
            output.pbData=ctypes.cast(buffer,type(output.pbData))
            return 1
        native=SimpleNamespace(crypt32=SimpleNamespace(CryptProtectData=transform,CryptUnprotectData=transform),kernel32=SimpleNamespace(LocalFree=lambda _:None))
        with patch.object(ctypes,'windll',native,create=True):
            self.assertEqual(storage._dpapi_encrypt(b'\x00\x7f\x80\xff'),b'\x00\x7f\x80\xff')
            self.assertEqual(storage._dpapi_decrypt(b'\x00\x7f\x80\xff'),b'\x00\x7f\x80\xff')
