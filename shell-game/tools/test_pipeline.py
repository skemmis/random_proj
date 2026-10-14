"""Tests for the parcel download mapping and the owner-file join."""
import csv, io, unittest

from fetch_parcels import use_of
from join_owners import join, resolve, shared_addresses


def parcels():
    return [{"ain": a, "use": "single_family", "owner": "", "mail_address": "", "mail_state": "", "last_sale_price": ""}
            for a in ("5077001001", "5077001002", "5077001003")]


def owners(text, overrides=None):
    rd = csv.DictReader(io.StringIO(text))
    return rd, resolve(rd.fieldnames, overrides or {})


class UseCodeTest(unittest.TestCase):
    def test_codes(self):
        self.assertEqual(use_of("0100"), "single_family")
        self.assertEqual(use_of("010C"), "condo")
        self.assertEqual(use_of("010E"), "condo")
        self.assertEqual(use_of("0200"), "multi_family")
        self.assertEqual(use_of("0500"), "multi_family")
        self.assertIsNone(use_of("010V"))  # vacant land
        self.assertIsNone(use_of("1200"))  # store
        self.assertIsNone(use_of(None))


class JoinTest(unittest.TestCase):
    def test_assessor_roll_split_address(self):
        rd, cols = owners(
            "AIN,First Owner Name,Mail Address House No,Mail Address Street Name,Mail Address City and State,Mail Address Zip\n"
            "5077-001-001,ECHO HOLDINGS LLC,1209,ORANGE ST,WILMINGTON DE,19801\n")
        ps = parcels()
        self.assertEqual(join(ps, rd, cols), 1)
        self.assertEqual(ps[0]["owner"], "ECHO HOLDINGS LLC")
        self.assertEqual(ps[0]["mail_address"], "1209 ORANGE ST WILMINGTON DE 19801")
        self.assertEqual(ps[0]["mail_state"], "DE")
        self.assertEqual(ps[1]["owner"], "")

    def test_reseller_one_line_address(self):
        rd, cols = owners(
            "parcel_id,owner,mail_address1,mail_city,mail_state,sale_price\n"
            "5077001002,SILVER LAKE PROPERTIES LP,PO BOX 12,RENO,NV,\"$1,250,000\"\n")
        ps = parcels()
        join(ps, rd, cols)
        self.assertEqual(ps[1]["mail_address"], "PO BOX 12 RENO")
        self.assertEqual(ps[1]["mail_state"], "NV")
        self.assertEqual(ps[1]["last_sale_price"], "1250000")

    def test_override(self):
        rd, cols = owners("PARCEL,TAXPAYER,ADDR\n5077001003,X LLC,1 MAIN ST LOS ANGELES CA 90026\n",
                          {"ain": "PARCEL", "owner": "TAXPAYER", "mail_address": "ADDR"})
        ps = parcels()
        join(ps, rd, cols)
        self.assertEqual(ps[2]["mail_state"], "CA")

    def test_shared_addresses_count_companies_only(self):
        ps = parcels()
        for p, o in zip(ps, ["A LLC", "B LLC", "SMITH JOHN"]):
            p.update(owner=o, mail_address="1 SAME ST")
        self.assertEqual(shared_addresses(ps), [("1 SAME ST", 2)])


if __name__ == "__main__":
    unittest.main()
