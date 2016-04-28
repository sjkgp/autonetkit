import unittest
import autonetkit


class TestDmEdge(unittest.TestCase):
    def setUp(self):
        self.anm_house = autonetkit.topos.house()
        self.anm_mixed = autonetkit.topos.mixed()
        self.anm_multi = autonetkit.topos.multi_edge()

    def test_repr(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        e1_anm = self.anm_mixed['phy'].edge("r1", "r2")
        e1 = nidb.edge(e1_anm)
        self.assertEqual(e1, ('r1', 'r2', 0))

    def test_raw_interfaces(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        result = nidb.node("r1").raw_interfaces
        expected_result = {0: {'category': 'loopback', 'description': None},
                           1: {'category': 'physical', 'description': 'r1 to sw1'},
                           2: {'category': 'physical', 'description': 'r1 to r2'},
                           3: {'category': 'physical', 'description': 'r1 to r3'}}
        self.assertDictEqual(expected_result, result)

    def test_is_multigraph(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        self.assertTrue(nidb.is_multigraph())

    def test_src(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        e1_anm = self.anm_mixed['phy'].edge("r1", "r2")
        e1 = nidb.edge(e1_anm)
        r1 = nidb.node('r1')
        self.assertEqual(e1.src, r1)

    def test_src_int(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        e1_anm = self.anm_mixed['phy'].edge("r1", "r2")
        e1 = nidb.edge(e1_anm)
        self.assertEqual(str(e1.src_int), 'r1.r1 to r2')

    def test_dst_int(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        e1_anm = self.anm_mixed['phy'].edge("r1", "r2")
        e1 = nidb.edge(e1_anm)
        self.assertEqual(str(e1.dst_int), 'r2.r2 to r1')

    def test_eq(self):
        nidb = autonetkit.DeviceModel(self.anm_house)
        e1_anm = self.anm_house['phy'].edge("r1", "r2")
        e2_anm = self.anm_house['phy'].edge("r2", "r3")
        e1 = nidb.edge(e1_anm)
        e2 = nidb.edge(e2_anm)
        self.assertEqual(e1, e1)
        self.assertEqual(e1, e1_anm)
        self.assertFalse(e1 == e2)
        # And for multigraph case
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        e1_anm = self.anm_mixed['phy'].edge("r1", "r2")
        e2_anm = self.anm_mixed['phy'].edge("r1", "r3")
        e1 = nidb.edge(e1_anm)
        e2 = nidb.edge(e2_anm)
        self.assertEqual(e1,e1)
        self.assertEqual(e1, e1_anm)
        self.assertFalse(e1 == e2)

    def test_lt(self):
        nidb = autonetkit.DeviceModel(self.anm_house)
        e1_anm = self.anm_house['phy'].edge("r1", "r2")
        e2_anm = self.anm_house['phy'].edge("r2", "r3")
        e1 = nidb.edge(e1_anm)
        e2 = nidb.edge(e2_anm)
        self.assertLess(e1, e2)
        self.assertFalse(e2 < e1)

    def test_nonzero(self):
        nidb = autonetkit.DeviceModel(self.anm_house)
        e1_anm = self.anm_house['phy'].edge("r1", "r2")
        #e2_anm_nonexistent = self.anm_house['phy'].edge("r1", "r100")
        e1 = nidb.edge(e1_anm)
        #e2 = nidb.edge(e2_anm_nonexistent)
        self.assertTrue(e1)
        #self.assertFalse(e2)
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        e1_anm = self.anm_mixed['phy'].edge("r1", "r2")
        #e2_anm_nonexistent = self.anm_mixed['phy'].edge("r1", "r100")
        e1 = nidb.edge(e1_anm)
        #e2 = nidb.edge(e2_anm_nonexistent)
        self.assertTrue(e1.is_multigraph())
        self.assertTrue(e1)
        #self.assertFalse(e2)

    def test_dst(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        e1_anm = self.anm_mixed['phy'].edge("r1", "r2")
        e1 = nidb.edge(e1_anm)
        r2 = nidb.node('r2')
        self.assertEqual(e1.dst, r2)


if __name__ == '__main__':
    unittest.main()
