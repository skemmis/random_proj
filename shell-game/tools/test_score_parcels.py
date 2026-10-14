"""Tests for the "how hidden" score: python3 -m unittest discover shell-game/tools"""
import unittest

from score_parcels import build, is_entity

BASE = {"lng": "-118.26", "lat": "34.08", "units": "1", "value": "1500000", "last_sale_price": "", "homeowner_exemption": ""}


def parcel(ain, owner, mail, state="CA", use="single_family", hox=""):
    return {**BASE, "ain": ain, "owner": owner, "mail_address": mail, "mail_state": state,
            "situs_address": f"{ain} ECHO PARK AVE", "use": use, "homeowner_exemption": hox}


def run(parcels, entities=()):
    return {f["properties"]["id"]: f["properties"] for f in build(parcels, list(entities))["features"]}


class EntityTest(unittest.TestCase):
    def test_companies_and_trusts(self):
        self.assertEqual(is_entity("1520 ECHO PARK LLC"), "company")
        self.assertEqual(is_entity("SUNSET HOLDINGS L.P."), "company")
        self.assertEqual(is_entity("GLASSELL PARK LAND TRUST"), "trust")
        self.assertIsNone(is_entity("GARCIA FAMILY TRUST"))
        self.assertIsNone(is_entity("SMITH JOHN AND JANE"))


class ScoreTest(unittest.TestCase):
    def test_people_are_not_spots(self):
        self.assertEqual(run([parcel("1", "SMITH JOHN", "1 ECHO PARK AVE", hox="1")]), {})

    def test_non_residential_skipped(self):
        self.assertEqual(run([parcel("1", "ACME LLC", "1209 ORANGE ST", "DE", use="commercial")]), {})

    def test_small_local_landlord_stays_common(self):
        out = run([parcel("1", "MY DUPLEX LLC", "200 N ALVARADO ST", "CA")],
                  [{"owner": "MY DUPLEX LLC", "formed_in": "DE", "layers": "0"}])
        self.assertEqual(out["1"]["rarity"], "Common")
        self.assertIn("Looks like a small local landlord", out["1"]["why"])

    def test_registered_agent_network_scores_high(self):
        ps = [parcel(str(i), f"ECHO {i} LLC", "1209 ORANGE ST", "DE") for i in range(30)]
        ents = [{"owner": f"ECHO {i} LLC", "formed_in": "DE", "layers": "3", "dead_end": "registered_agent"} for i in range(30)]
        out = run(ps, ents)
        self.assertEqual(out["0"]["rarity"], "Legendary")
        self.assertTrue(any("29 other homes" in w for w in out["0"]["why"]))

    def test_no_names_in_output(self):
        out = run([parcel("1", "SECRET PERSON HOLDINGS LLC", "1209 ORANGE ST", "DE")])
        self.assertNotIn("SECRET", repr(out))

    def test_offshore_leaks_flag(self):
        out = run([parcel("1", "BLUE LLC", "PO BOX 9", "NY")],
                  [{"owner": "BLUE LLC", "formed_in": "VG", "layers": "2", "flags": "offshore_leaks"}])
        self.assertEqual(out["1"]["rarity"], "Legendary")


if __name__ == "__main__":
    unittest.main()
