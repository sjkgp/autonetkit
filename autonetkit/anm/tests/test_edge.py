import unittest
import autonetkit

class TestNmEdge(unittest.TestCase):
    def setUp(self):
        self.anm_house = autonetkit.topos.house()
        self.anm_mixed = autonetkit.topos.mixed()
        self.anm_multi = autonetkit.topos.multi_edge()

    def test_hash(self):
        edge = self.anm_multi['phy'].edge("r1", "r2")
        self.assertEqual(hash(edge), -5246091905943233080)

    def test_is_multigraph(self):
        edge = self.anm_multi['phy'].edge("r1", "r2")
        self.assertTrue(edge.is_multigraph())
        edge = self.anm_multi['phy'].edge("r2", "r3")
        self.assertTrue(edge.is_multigraph())
        e1 = self.anm_house['phy'].edge("r1", "r2")
        self.assertFalse(e1.is_multigraph())

    def test_is_parallel(self):
        edge = self.anm_multi['phy'].edge("r1", "r2")
        self.assertTrue(edge.is_parallel())
        edge = self.anm_multi['phy'].edge("r2", "r3")
        self.assertFalse(edge.is_parallel())

    def test_eq(self):
        e1 = self.anm_house['phy'].edge("r1", "r2")
        e2 = self.anm_house['phy'].edge("r1", "r2")
        self.assertEqual(e1, e2)
        # Can also compare across layers
        e2 = self.anm_house['input'].edge("r1", "r2")
        self.assertEqual(e1, e2)
        # For multi-edge graphs can specify the key
        e1 = self.anm_multi['phy'].edge("r1", "r2", 0)
        e2 = self.anm_multi['phy'].edge("r1", "r2", 1)
        self.assertFalse(e1 == e2)

    def test_overlay(self):
        e1 = self.anm_house['phy'].edge("r1", "r2")
        self.assertEqual(str(e1._overlay()), 'phy')

    def test_lt(self):
        e1 = self.anm_house['phy'].edge("r1", "r2")
        e2 = self.anm_house['phy'].edge("r1", "r3")
        self.assertLess(e1, e2)
        self.assertFalse(e2 < e1)

    def test_nonzero(self):
        e1 = self.anm_house['phy'].edge("r1", "r2")
        self.assertTrue(e1)
        # For a non-existent link, will return False
        # (NOTE: doesn't throw exception)
        e2 = self.anm_house['phy'].edge("r1", "r5")
        self.assertFalse(e2)

    def test_raw_interfaces(self):
        e1 = self.anm_house['phy'].edge("r1", "r2")
        result = e1.raw_interfaces
        expected_result = {'r1': 1, 'r2': 1}
        self.assertDictEqual(expected_result, result)
        e2 = self.anm_house['phy'].edge("r1", "r3")
        result = e2.raw_interfaces
        expected_result = {'r1': 2, 'r3': 1}
        self.assertDictEqual(expected_result, result)

    def test_data(self):
        e1 = self.anm_house['phy'].edge("r1", "r2")
        expected_result = {'_ports': {'r1': 1, 'r2': 1},
                           'raw_interfaces': {}}
        self.assertDictEqual(e1._data, expected_result)
        e2 = self.anm_house['phy'].edge("r1", "r3")
        expected_result = {'_ports': {'r1': 2, 'r3': 1},
                           'raw_interfaces': {}}
        self.assertDictEqual(e2._data, expected_result)

    def test_src(self):
        edge = self.anm_house['phy'].edge("r1", "r2")
        r1 = self.anm_house['phy'].node("r1")
        self.assertEqual(edge.src, r1)

    def test_dst(self):
        edge = self.anm_house['phy'].edge("r1", "r2")
        r2 = self.anm_house['phy'].node("r2")
        self.assertEqual(edge.dst, r2)

    def test_apply_to_interfaces(self):
        edge = self.anm_house['phy'].edge("r1", "r2")
        edge.src_int.set('color', "blue")
        edge.dst_int.set('color', "blue")
        self.assertEqual(edge.src_int.get('color'), 'blue')
        self.assertEqual(edge.dst_int.get('color'), 'blue')
        edge.set('color', "red")
        edge.apply_to_interfaces("color")
        self.assertEqual(edge.src_int.get('color'), 'red')
        self.assertEqual(edge.dst_int.get('color'), 'red')

    def test_src_int(self):
        edge = self.anm_house['phy'].edge("r1", "r2")
        self.assertEqual(str(edge.src_int), 'eth0.r1')

    def test_dst_int(self):
        edge = self.anm_house['phy'].edge("r1", "r2")
        self.assertEqual(str(edge.dst_int), 'eth0.r2')

    def test_interfaces(self):
        edge = self.anm_house['phy'].edge("r1", "r2")
        result = [str(i) for i in edge.interfaces()]
        expected_result = ['eth0.r1', 'eth0.r2']
        self.assertListEqual(expected_result, result)

    def test_dump(self):
        e2 = self.anm_house['phy'].edge("r1", "r3")
        expected_result = "{'_ports': {'r1': 2, 'r3': 1}, 'raw_interfaces': {}}"
        self.assertEqual(e2.dump(), expected_result)

    def test_get(self):
        edge = self.anm_house['phy'].edge("r1", "r2")
        edge.set('color', "red")
        self.assertEqual(edge.get("color"), 'red')

    def test_set(self):
        edge = self.anm_house['phy'].edge("r1", "r2")
        edge.set('color', "blue")
        self.assertEqual(edge.get('color'), 'blue')
        edge.set("color", "red")
        self.assertEqual(edge.get('color'), 'red')

if __name__ == '__main__':
    unittest.main()
