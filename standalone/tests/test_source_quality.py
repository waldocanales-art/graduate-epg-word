import unittest
from standalone.source_quality import validate_expedient

class SourceValidation(unittest.TestCase):
    def test_missing_sources_are_not_approved(self):
        result=validate_expedient({"program_type":"TI","authors":[{"name":"Ejemplo","dni":"00000000"}]})
        self.assertFalse(result["ready"])
        self.assertIn("AUTHOR_SIGNATURE",{x["code"] for x in result["issues"]})
        self.assertIn("AUTHOR_FINGERPRINT",{x["code"] for x in result["issues"]})

    def test_multiple_authors_must_have_separate_evidence(self):
        result=validate_expedient({"program_type":"TI","authors":[{"name":"A","dni":"12345678","signature_source":"s1","fingerprint_source":"h1"},{"name":"B","dni":"87654321"}]})
        self.assertFalse(result["ready"])
        self.assertTrue(any("Autor 2" in x["detail"] for x in result["issues"]))

if __name__=="__main__":
    unittest.main()
