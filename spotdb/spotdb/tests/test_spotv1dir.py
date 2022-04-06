import spotdb

from spotdb.calidirdb import SpotCaliperDirectoryDB

import os
import unittest

class CaliDirDBSpotV1Test(unittest.TestCase):
    def setUp(self):
        datadir = os.path.join(os.path.dirname(__file__), "data")
        self.db = SpotCaliperDirectoryDB(datadir+"/mixed")
    
        runs = self.db.get_all_run_ids()
        self.db.get_global_data(runs)


    def test_calidirdb_metadata(self):        
        g = self.db.get_global_attribute_metadata()

        self.assertEqual(g["launchdate"     ]["type"], "date")
        self.assertEqual(g["commit"         ]["type"], "string")
        self.assertEqual(g["figure_of_merit"]["type"], "double")

        m = self.db.get_metric_attribute_metadata()

        self.assertEqual(m["avg#inclusive#sum#time.duration"]["type"], "double")
        self.assertEqual(m["avg#inclusive#sum#time.duration"]["unit"], "sec")
        self.assertEqual(m["avg#loop.iterations/time.duration"]["type"],  "double")
        self.assertEqual(m["avg#loop.iterations/time.duration"]["alias"], "Iter/s")


    def test_calidirdb_runs(self):
        runs = { "spotv1-0", "spotv1-1" }

        self.assertTrue(runs <= set(self.db.get_all_run_ids()))

        g = self.db.get_global_data(runs)

        self.assertSetEqual(set(runs), set(g.keys()))

        for r in runs:
            self.assertIn("launchdate", g[r])
            self.assertIn("commit", g[r])
        
        p = self.db.get_regionprofiles(runs)

        self.assertSetEqual(set(runs), set(p.keys()))

        for r in runs:
            self.assertIn("main/lulesh.cycle/TimeIncrement", p[r])
            self.assertIn("avg#inclusive#sum#time.duration", p[r]["main/lulesh.cycle/TimeIncrement"])


if __name__ == "__main__":
    unittest.main()
