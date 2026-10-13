import unittest
from standalone.evidence_resolver import resolve_existing_evidence


class ResolverTests(unittest.TestCase):
    def test_same_group_same_author_reuses_existing_evidence(self):
        result = resolve_existing_evidence("G-2", [{"author_id":"A"}], [
            {"group_id":"G-2","author_id":"A","kind":"signature","source_id":"source-s","provenance_verified":True},
            {"group_id":"G-2","author_id":"A","kind":"fingerprint","source_id":"source-f","provenance_verified":True},
        ])
        self.assertEqual([], result["exceptions"])
        self.assertEqual("RECOVERED_EXISTING",result["authors"]["A"]["signature"]["status"])

    def test_does_not_borrow_another_author_signature(self):
        result = resolve_existing_evidence("G-2", [{"author_id":"A"}], [
            {"group_id":"G-2","author_id":"B","kind":"signature","source_id":"S","provenance_verified":True}
        ])
        self.assertFalse(result["authors"]["A"]["signature"]["available"])

    def test_does_not_use_unverified_source(self):
        result=resolve_existing_evidence("G-2",[{"author_id":"A"}],[
            {"group_id":"G-2","author_id":"A","kind":"signature","source_id":"S","provenance_verified":False}
        ])
        self.assertFalse(result["authors"]["A"]["signature"]["available"])


if __name__ == "__main__":
    unittest.main()
