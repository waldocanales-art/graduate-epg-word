import unittest
from standalone.group_number_contract import (
    GroupLookupError, SingleDocumentBlocked, normalize_group_number,
    group_document_menu, select_single_document
)


class GroupNumberContractTest(unittest.TestCase):
    def test_operator_only_needs_group_number(self):
        self.assertEqual("29", normalize_group_number(" 0029 "))
        with self.assertRaises(GroupLookupError):
            normalize_group_number("EPG-29")
        with self.assertRaises(GroupLookupError):
            normalize_group_number("29,30")

    def test_one_action_one_document(self):
        menu = group_document_menu("29", {
            "group_id":"29",
            "documents":[
                {"document_id":"metadata","status":"LISTO_PARA_GENERAR","kind":"METADATA_1"},
                {"document_id":"jurada","status":"PENDIENTE_FUENTE","kind":"DECLARACION_JURADA"}
            ]
        })
        selected = select_single_document(menu, "metadata")
        self.assertEqual("metadata", selected["document_id"])
        self.assertEqual("GENERATE_ONE_DOCUMENT", selected["action"])
        self.assertEqual(2, menu["total"])
        with self.assertRaises(SingleDocumentBlocked):
            select_single_document(menu,"jurada")

    def test_does_not_choose_between_ambiguous_drives(self):
        with self.assertRaises(GroupLookupError):
            group_document_menu("29", {"group_id":"29","collision":True})

    def test_original_preserved_instead_of_resigned(self):
        menu = group_document_menu(29, {
            "group_id":"29",
            "documents":[{"document_id":"acta","kind":"ACTA_SUSTENTACION",
                          "status":"ORIGINAL_EN_DRIVE","source_ref":"verified-source-id"}]
        })
        self.assertEqual("DOWNLOAD_ORIGINAL",select_single_document(menu,"acta")["action"])


if __name__ == "__main__":
    unittest.main()
