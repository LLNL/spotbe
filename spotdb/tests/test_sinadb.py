import spotdb

from spotdb.sinadb import SpotSinaDB
from spotdb.caliutil import read_caliper_file

import os
import unittest

class SinaDBTest(unittest.TestCase):
    def setUp(self):
        self.db = SpotSinaDB(":memory:")
        datadir = os.path.join(os.path.dirname(__file__), "data")

        for f in [ "0.cali", "1.cali", "2.cali", "3.cali" ]:
            obj = read_caliper_file(datadir+'/lulesh_timeseries/'+f)
            self.db.add(obj)
    

    def test_sinadb_metadata(self):
        self.assertGreaterEqual(self.db.version(), 1)

        g = self.db.get_global_attribute_metadata()

        self.assertEqual(g["launchdate"     ]["type"], "date")
        self.assertEqual(g["problem_size"   ]["type"], "int")
        self.assertEqual(g["figure_of_merit"]["type"], "double")

        m = self.db.get_metric_attribute_metadata()

        self.assertEqual(m["avg#inclusive#sum#time.duration"]["type"], "double")
        self.assertEqual(m["avg#inclusive#sum#time.duration"]["unit"], "sec")
        self.assertEqual(m["avg#loop.iterations/time.duration"]["type"],  "double")
        self.assertEqual(m["avg#loop.iterations/time.duration"]["alias"], "Iter/s")


    def test_sinadb_runs(self):
        runs = self.db.get_all_run_ids()

        self.assertEqual(len(runs), 4)

        g = self.db.get_global_data(runs)

        self.assertSetEqual(set(runs), set(g.keys()))

        for r in runs:
            self.assertIn("launchdate", g[r])
            self.assertIn("figure_of_merit", g[r])
            self.assertEqual(g[r]["cluster"], "quartz")
        
        p = self.db.get_regionprofiles(runs)

        self.assertSetEqual(set(runs), set(p.keys()))

        for r in runs:
            self.assertIn("main/lulesh.cycle/LagrangeLeapFrog", p[r])
            self.assertIn("avg#inclusive#sum#time.duration", p[r]["main/lulesh.cycle/LagrangeLeapFrog"])


    def test_sinadb_timeseries(self):
        runs = self.db.get_all_run_ids()

        self.assertEqual(len(runs), 4)

        g = self.db.get_global_data(runs)
        t = self.db.get_channel_data("timeseries", runs)

        self.assertSetEqual(set(runs), set(t.keys()))

        for r in runs:
            self.assertEqual(g[r]["timeseries"], 1)
            self.assertTrue(len(t[r]) > 0)
            self.assertIn("block", t[r][0])
            self.assertIn("avg#loop.iterations/time.duration", t[r][0])


if __name__ == "__main__":
    unittest.main()
