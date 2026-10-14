"""HAWKS V7: garantizar formato original de Liz y bloquear sustituciones."""
import os
import unittest
from unittest.mock import patch
from fastapi import HTTPException
from standalone import main
from standalone.liz_template_loader_v7 import validate_official_template
from standalone.drive_adapter_v6 import DriveConnectionError


class LizStrictTests(unittest.TestCase):
    def test_non_liz_template_rejected(self):
        with self.assertRaises(ValueError):
            validate_official_template(b"this is not a real Liz docx", 2)

    def test_unsupported_authors_blocked(self):
        with self.assertRaises(ValueError):
            validate_official_template(b"", 4)

    def test_missing_drive_must_never_trigger_reconstructed_layout(self):
        with patch("standalone.main.fetch_official_metadata_template",
                   side_effect=DriveConnectionError("Drive no autorizado")):
            with self.assertRaises(DriveConnectionError):
                main._render_verified_metadata("29", 2)

    def test_old_alternative_demo_removed(self):
        with self.assertRaises(HTTPException) as ctx:
            main.demo_metadata_v6(2)
        self.assertEqual(ctx.exception.status_code, 410)

    def test_no_new_word_button_without_original_liz(self):
        with patch.dict(os.environ, {"DOCUMENTOS_V3_API_KEY": "secret"}, clear=True):
            with patch("standalone.main.document_rows", return_value=[{
                "id": "METADATA_2", "name": "Metadatos",
                "can_generate_new": False, "can_download": False
            }]):
                with patch("standalone.main.eligible", return_value=True):
                    with patch("standalone.main.profiles", return_value={"29":{"authors":[{},{}]}}):
                        rows=main._v5_documents("29")
        self.assertFalse(rows[0]["can_generate_new"])


if __name__ == "__main__":
    unittest.main()
