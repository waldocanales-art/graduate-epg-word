"""Regresión HAWKS V6.1: porcentajes, CSV y diagnóstico privado."""
import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from standalone.main import generation_health_v5, index_health_v5, observations_csv_v6
from standalone.turnitin_filename_v6 import extract_scores
from standalone.batch_v6 import audit_group


class TurnitinClues(unittest.TestCase):
    def test_distinguishes_ai_and_similarity(self):
        scores = extract_scores("Turnitin_38%IA_18%SIMILITUD.pdf")
        self.assertEqual(scores["ai_percentages_named"], [38])
        self.assertEqual(scores["similarity_percentages_named"], [18])
        self.assertEqual(scores["unclassified_percentages_named"], [])
        self.assertFalse(scores["content_verified"])

    def test_ai_not_falsely_marked_as_similarity(self):
        docs = [{
            "id": "TURNITIN_1", "name": "Turnitin_38%IA.pdf",
            "pdf_url": "https://drive.google.com/file/d/example_source_123/view"
        }]
        result = audit_group("29", "Equipo", "Maestría", "F4", docs)
        codes = [x["code"] for x in result["issues"]]
        self.assertIn("TURNITIN_IA_SUPERA_30_HISTORICO", codes)
        self.assertNotIn("TURNITIN_SUPERA_20_HISTORICO", codes)
        self.assertFalse(result["ready_for_institutional_release"])

    def test_legacy_ambiguous_percent_is_marked_inferred(self):
        scores = extract_scores("30%turnitin_TI_01-09-2026.pdf")
        self.assertEqual(scores["similarity_percentages_named"], [30])
        self.assertTrue(scores["similarity_inferred_from_filename"])


class PrivateDiagnostics(unittest.TestCase):
    def test_health_details_need_authorization(self):
        with patch.dict(os.environ, {"DOCUMENTOS_V3_API_KEY": "right"}):
            for fn in (generation_health_v5, index_health_v5):
                with self.assertRaises(HTTPException) as error:
                    fn("wrong")
                self.assertEqual(error.exception.status_code, 401)

    def test_export_csv_is_authenticated(self):
        with patch.dict(os.environ, {"DOCUMENTOS_V3_API_KEY": "right"}):
            with self.assertRaises(HTTPException) as error:
                observations_csv_v6("29", "wrong")
            self.assertEqual(error.exception.status_code, 401)

    def test_csv_includes_real_issue_rows(self):
        report = {
            "group_id": "29", "phase": "F5",
            "issues": [{"code": "SIN_FUENTE", "severity": "PENDIENTE", "detail": "Documento no localizado"}]
        }
        with patch.dict(os.environ, {"DOCUMENTOS_V3_API_KEY": "right"}):
            with patch("standalone.main._v6_report", return_value=report):
                response = observations_csv_v6("29", "right")
        self.assertIn(b"SIN_FUENTE", response.body)
        self.assertIn(b"PENDIENTE", response.body)
        self.assertIn("attachment", response.headers["content-disposition"])


if __name__ == "__main__":
    unittest.main()
