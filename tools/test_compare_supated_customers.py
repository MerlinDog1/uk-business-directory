import unittest

from compare_supated_customers import compare, name, phone, postcode


class CustomerComparisonTests(unittest.TestCase):
    def test_unique_exact_name_and_postcode(self):
        overlay, _ = compare([{'id': 1, 'company': 'Acme Signs Ltd', 'address': 'SW1A 1AA'}],
                             [{'company': 'ACME Signs Limited', 'postcode': 'SW1A 1AA'}])
        self.assertEqual(overlay['matches'][0]['status'], 'confirmed')
        self.assertIn('same postcode', overlay['matches'][0]['reason'])

    def test_name_only_is_possible(self):
        overlay, _ = compare([{'id': 1, 'company': 'Acme Signs Ltd'}],
                             [{'company': 'ACME Signs Limited'}])
        self.assertEqual(overlay['matches'][0]['status'], 'possible')
        self.assertIn('no matching postcode or phone', overlay['matches'][0]['reason'])

    def test_duplicate_or_conflicting_postcodes_are_possible(self):
        directory = [{'id': 1, 'company': 'Acme Signs', 'address': 'London SW1A 1AA'},
                     {'id': 2, 'company': 'Beacon Signs', 'address': 'London SW1A 1AA'}]
        customers = [{'company': 'Acme Signs'}, {'company': 'Acme Signs Ltd'},
                     {'company': 'Beacon Signs', 'postcode': 'M1 1AA'}]
        overlay, review = compare(directory, customers)
        self.assertEqual([(x['id'], x['status']) for x in overlay['matches']], [(1, 'possible'), (2, 'possible')])
        self.assertIn('Acme Signs Ltd', overlay['matches'][0]['customer'])
        self.assertIn('postcode differs', overlay['matches'][1]['reason'])
        self.assertTrue(review[-1]['postcode_conflict'])

    def test_fuzzy_requires_corroboration_and_never_confirms(self):
        directory = [{'id': 7, 'company': 'Acme Signage', 'phone': '020 1234 5678'},
                     {'id': 8, 'company': 'Acme Signage Ltd'}]
        customers = [{'company': 'Acme Signages', 'phone_number': '+44 20 1234 5678'}]
        overlay, _ = compare(directory, customers)
        self.assertEqual([(x['id'], x['status']) for x in overlay['matches']], [(7, 'possible')])
        self.assertIn('same phone', overlay['matches'][0]['reason'])

    def test_different_business_with_shared_telephone_is_not_matched(self):
        overlay, _ = compare([{'id': 3, 'company': 'Acme Signs', 'phone': '020 1234 5678'}],
                             [{'company': 'Completely Different', 'phone_number': '02012345678'}])
        self.assertEqual(overlay['matches'], [])

    def test_indexed_candidates_keep_source_order_and_do_not_duplicate(self):
        directory = [{'id': 9, 'company': 'Acme Signage', 'address': 'SW1A 1AA', 'phone': '020 1234 5678'}]
        customers = [{'company': 'Acme Signages', 'postcode': 'SW1A 1AA'},
                     {'company': 'Acme Signage', 'postcode': 'SW1A 1AA', 'phone_number': '020 1234 5678'},
                     {'company': 'Unrelated', 'postcode': 'SW1A 1AA'},
                     {'company': '', 'phone_number': '020 1234 5678'}]
        overlay, review = compare(directory, customers)
        self.assertEqual(overlay['matches'][0]['status'], 'possible')
        self.assertEqual([row['customer_company'] for row in review], ['Acme Signages', 'Acme Signage'])
        self.assertEqual(overlay['matches'][0]['customer'], 'Acme Signages; Acme Signage')

    def test_normalization(self):
        self.assertEqual(name('A & B Signage, Ltd.'), 'a and b signage')
        self.assertEqual(phone('+44 20 1234 5678'), '02012345678')
        self.assertEqual(postcode('42 High Street, SW1A 1AA'), 'SW1A1AA')
        self.assertEqual(phone('123'), '')


if __name__ == '__main__':
    unittest.main()
