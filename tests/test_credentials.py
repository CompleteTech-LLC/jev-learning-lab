"""Credential UI tests use dummy data and mocked transports, never an account."""
from __future__ import annotations
import contextlib
import getpass
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import warnings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import jev_runtime as rt

DUMMY = 'UNIT-TEST-DUMMY-CREDENTIAL-NOT-A-REAL-KEY'

class CredentialTests(unittest.TestCase):
    def interact(self, lab, reader):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), patch('urllib.request.urlopen') as net:
            result = rt.prompt_for_api_key(lab, reader=reader)
            net.assert_not_called()
        self.assertNotIn(DUMMY, out.getvalue())
        return result, out.getvalue()

    def test_entered_key_explicitly_selects_live_without_network(self):
        lab = rt.TutorialLab()
        mode, output = self.interact(lab, lambda prompt: DUMMY)
        self.assertEqual(mode, 'live')
        self.assertEqual(lab.mode, 'live')
        self.assertEqual(lab._session_api_key, DUMMY)
        self.assertIn('not yet been verified', output)
        self.assertEqual(lab.live_attempts, 0)

    def test_empty_input_keeps_offline(self):
        lab = rt.TutorialLab()
        mode, _ = self.interact(lab, lambda prompt: '   ')
        self.assertEqual(mode, 'offline')
        self.assertEqual(lab._session_api_key, '')

    def test_plain_setter_does_not_authorize_live(self):
        lab = rt.TutorialLab()
        lab.set_api_key(DUMMY)
        self.assertEqual(lab.mode, 'offline')

    def test_memory_key_not_written_to_environment(self):
        lab = rt.TutorialLab()
        with patch.dict(os.environ, {'TYPESAFE_API_KEY':'EXTERNAL-KEY'}):
            self.interact(lab, lambda prompt: DUMMY)
            self.assertEqual(os.environ['TYPESAFE_API_KEY'], 'EXTERNAL-KEY')

    def test_invalid_keys_fail_closed(self):
        for value in ('has space', 'bad\0key', 'bad\x7fkey', 'nonascii-\u03bb', 'x'*4097, None):
            with self.subTest(value_type=type(value).__name__):
                lab = rt.TutorialLab('live', True)
                lab.set_api_key(DUMMY)
                mode, _ = self.interact(lab, lambda prompt, value=value: value)
                self.assertEqual(mode, 'offline')
                self.assertEqual(lab._session_api_key, '')

    def test_cancel_discards_old_key(self):
        for exc in (KeyboardInterrupt, EOFError):
            lab = rt.TutorialLab('live', True)
            lab.set_api_key(DUMMY)
            def reader(prompt):
                raise exc()
            mode, _ = self.interact(lab, reader)
            self.assertEqual(mode, 'offline')
            self.assertEqual(lab._session_api_key, '')

    def test_no_plaintext_getpass_fallback(self):
        lab = rt.TutorialLab()
        def reader(prompt):
            warnings.warn('Masked input unavailable', getpass.GetPassWarning)
            raise AssertionError('A warning must become an exception before reading')
        mode, output = self.interact(lab, reader)
        self.assertEqual(mode, 'offline')
        self.assertIn('No key was read', output)

    def test_normal_reader_uses_getpass(self):
        lab = rt.TutorialLab()
        out = io.StringIO()
        with patch('getpass.getpass', return_value=DUMMY) as reader, \
             contextlib.redirect_stdout(out), patch('urllib.request.urlopen') as net:
            rt.prompt_for_api_key(lab)
        reader.assert_called_once()
        self.assertIn('charges may apply', reader.call_args.args[0])
        net.assert_not_called()
        self.assertNotIn(DUMMY, out.getvalue())

    def test_reentry_preserves_usage_and_ledger(self):
        lab = rt.TutorialLab()
        lab.live_attempts = 4
        lab.records.append({'case':'previous'})
        self.interact(lab, lambda prompt: DUMMY)
        self.assertEqual(lab.live_attempts, 4)
        self.assertEqual(lab.max_live_calls, 10)
        self.assertEqual(lab.records, [{'case':'previous'}])

    def test_clear_disables_live_without_resetting_accounting(self):
        lab = rt.TutorialLab('live', True)
        lab.set_api_key(DUMMY)
        lab.live_attempts = 3
        lab.clear_api_key()
        self.assertEqual(lab._session_api_key, '')
        self.assertEqual(lab.mode, 'offline')
        self.assertEqual(lab.live_attempts, 3)

    def test_cleared_key_does_not_fall_back_to_environment(self):
        lab = rt.TutorialLab('live', True)
        lab.clear_api_key()
        with patch.dict(os.environ, {'TYPESAFE_API_KEY':'EXTERNAL-KEY'}), \
             patch('urllib.request.urlopen') as net:
            with self.assertRaises(RuntimeError):
                lab._post({'model':rt.MODEL})
            net.assert_not_called()

    def test_session_key_reaches_auth_header_not_logs_or_payload(self):
        lab = rt.TutorialLab('live', True)
        lab.set_api_key(DUMMY)
        questions = {'q':rt.noul('Is the fictional report explicit?')}
        raw = {'model':rt.MODEL,'answers':{'q':rt.fx_noul(.9)},'usage':None}
        response = io.BytesIO(json.dumps(raw).encode())
        with patch.dict(os.environ, {'TYPESAFE_API_KEY':'EXTERNAL-KEY'}), \
             patch('urllib.request.urlopen', return_value=response) as net:
            lab.ask('credential-test', 'A fictional report.', questions)
        request = net.call_args.args[0]
        self.assertEqual(request.get_header('Authorization'), 'Bearer '+DUMMY)
        self.assertNotIn(DUMMY, request.data.decode())
        self.assertNotIn(DUMMY, json.dumps(lab.requests))
        self.assertNotIn(DUMMY, json.dumps(lab.records))
        self.assertNotIn(DUMMY, repr(lab))

    def test_logo_bytes_match_verified_upstream(self):
        data = (ROOT/'assets/completetech_logo.jpg').read_bytes()
        self.assertEqual(hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest(),
                         '1325b5a410c5dc4c8af75fce515a188714262c25')

    def test_portable_logo_and_no_saved_widget_secret_state(self):
        nb = json.loads((ROOT/'JEV_Learning_Lab.ipynb').read_text())
        self.assertNotIn('widgets', nb.get('metadata', {}))
        source = ''.join(nb['cells'][0]['source'])
        self.assertIn('data:image/jpeg;base64,', source)
        self.assertIn('INNOVATION AT EVERY INTEGRATION', source)
        key_cells = [c for c in nb['cells'] if 'api-key-entry' in c.get('metadata', {}).get('tags', [])]
        self.assertEqual(len(key_cells),1)
        self.assertIn('prompt_for_api_key(lab)', ''.join(key_cells[0]['source']))

if __name__ == '__main__':
    unittest.main()
