import os
import unittest
from unittest.mock import patch
from fastapi import HTTPException
from standalone.main import auth

class AuthenticationTests(unittest.TestCase):
    def test_missing_environment_fails_closed(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(HTTPException) as error:
                auth(None)
            self.assertEqual(error.exception.status_code, 503)

    def test_wrong_key_rejected(self):
        with patch.dict(os.environ, {"DOCUMENTOS_V3_API_KEY": "expected"}):
            with self.assertRaises(HTTPException) as error:
                auth("wrong")
            self.assertEqual(error.exception.status_code, 401)

    def test_correct_key_accepted(self):
        with patch.dict(os.environ, {"DOCUMENTOS_V3_API_KEY": "expected"}):
            self.assertIsNone(auth("expected"))

if __name__ == "__main__":
    unittest.main()
