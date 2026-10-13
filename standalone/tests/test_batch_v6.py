import io
import unittest
import zipfile
from standalone.batch_v6 import audit_group, build_control_zip


class GroupAuditTests(unittest.TestCase):
    def test_groups_without_catalog_must_not_be_marked_done(self):
        result = audit_group("110", "Grupo", "Maestría", "F5", [])
        self.assertFalse(result["ready_for_institutional_release"])
        self.assertEqual(result["new_documents_generated"], 0)
        self.assertIn("SIN_DOCUMENTOS_INDIVIDUALES", [v["code"] for v in result["issues"]])

    def test_turnitin_old_and_over_limit(self):
        docs = [
            {"id":"TRABAJO_1", "name":"TI_20-09-2026.docx", "word_url":"https://drive.google.com/file/d/test_document_id_123/view"},
            {"id":"TURNITIN_1", "name":"30%turnitin_TI_01-09-2026.pdf", "pdf_url":"https://drive.google.com/file/d/test_file_id_456/view"}
        ]
        result = audit_group("241", "Group", "Maestría", "F4", docs)
        codes = [v["code"] for v in result["issues"]]
        self.assertIn("TURNITIN_SUPERA_20_HISTORICO", codes)
        self.assertIn("TURNITIN_ANTERIOR_AL_TI", codes)

    def test_zip_has_machine_readable_validation_no_fake_documents(self):
        report=audit_group("29","Group","Maestría","F5",[])
        z=zipfile.ZipFile(io.BytesIO(build_control_zip(report)))
        self.assertIn("CONTROL/VALIDACION_CRUZADA.json",z.namelist())
        self.assertIn("CONTROL/OBSERVACIONES.csv",z.namelist())
        self.assertFalse(any(x.endswith(".docx") for x in z.namelist()))

if __name__=="__main__":
    unittest.main()
