import ast
import unittest
import autonetkit


class TestDmInterface(unittest.TestCase):
    def setUp(self):
        self.anm_house = autonetkit.topos.house()
        self.anm_mixed = autonetkit.topos.mixed()
        self.anm_multi = autonetkit.topos.multi_edge()

    def test_hash(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        test_node = nidb.node("r1")
        eth0 = test_node.interface(1)
        self.assertEqual(hash(eth0), 2346446788448031185)

    def test_eq(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        test_node = nidb.node("r1")
        eth0 = test_node.interface(1)
        self.assertEqual(eth0, eth0)

    def test_lt(self):
        g_phy = self.anm_house['phy']
        test_node = g_phy.node("r1")
        eth0 = test_node.interface(1)
        self.assertFalse(eth0 < eth0)

    def test_is_bound(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        test_node = nidb.node("r1")
        eth0 = test_node.interface(1)
        loopback0 = test_node.interface(0)
        self.assertTrue(eth0.is_bound)
        self.assertFalse(loopback0.is_bound)

    def test_repr(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        test_node = nidb.node("r1")
        eth0 = test_node.interface(1)
        self.assertEqual(repr(eth0), 'r1.r1 to sw1')

    def test_nonzero(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        test_node = nidb.node("r1")
        eth0 = test_node.interface(1)
        loopback0 = test_node.interface(0)
        eth1 = test_node.interface(2)
        self.assertTrue(eth1)
        self.assertTrue(eth0)
        self.assertTrue(loopback0)

    def test_str(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        test_node = nidb.node("r1")
        eth0 = test_node.interface(1)
        eth1 = test_node.interface(2)
        self.assertEqual(str(eth0), 'r1.r1 to sw1')
        self.assertEqual(str(eth1), 'r1.r1 to r2')

    def test_node(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        test_node = nidb.node("r1")
        loopback0 = test_node.interface(0)
        expected_result = {'Network': None, '_ports': {0: {'category': 'loopback', 'description': None},
                                                       1: {'category': 'physical', 'description': 'r1 to sw1'},
                                                       2: {'category': 'physical', 'description': 'r1 to r2'},
                                                       3: {'category': 'physical', 'description': 'r1 to r3'}},
                           'update': None, 'syntax': None, 'host': None, 'device_type': 'router',
                           'graphics': {'y': 300, 'x': 500, 'device_type': 'router', 'device_subtype': None}, 'asn': 1,
                           'device_subtype': None, 'label': 'r1', 'platform': None}
        self.assertDictEqual(expected_result, loopback0._node)

    def test_port(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        test_node = nidb.node("r1")
        loopback0 = test_node.interface(0)
        expected_result = {'category': 'loopback',
                           'description': None}
        self.assertDictEqual(expected_result, loopback0._port)

    def test_is_loopback(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        test_node = nidb.node("r1")
        loopback0 = test_node.interface(0)
        self.assertTrue(loopback0.is_loopback)

    def test_is_physical(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        test_node = nidb.node("r1")
        eth0 = test_node.interface(1)
        self.assertTrue(eth0.is_physical)

    def test_description(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        test_node = nidb.node("r1")
        eth0 = test_node.interface(1)
        eth1 = test_node.interface(2)
        self.assertTrue(eth0.description, 'r1 to sw1')
        self.assertTrue(eth1.description, 'r1 to r2')

    def test_is_loopback_zero(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        test_node = nidb.node("r1")
        eth0 = test_node.interface(1)
        loopback0 = test_node.interface(0)
        self.assertTrue(loopback0.is_loopback_zero)
        self.assertFalse(eth0.is_loopback_zero)

    def test_node(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        test_node = nidb.node("r1")
        eth0 = test_node.interface(1)
        loopback0 = test_node.interface(0)
        eth1 = test_node.interface(2)
        self.assertEqual(eth0.node, test_node)
        self.assertEqual(eth1.node, test_node)
        self.assertEqual(loopback0.node, test_node)

    def test_dump(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        test_node = nidb.node("r1")
        eth1 = test_node.interface(2)
        result = eth1.dump()
        self.assertIsInstance(result, str)
        result = ast.literal_eval(result)
        expected_result = [('category', 'physical'),
                           ('description', 'r1 to r2')]
        self.assertListEqual(expected_result, result)

    def test_dict(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        test_node = nidb.node("r1")
        eth0 = test_node.interface(1)
        eth1 = test_node.interface(2)
        expected_result = {'category': 'physical', 'description': 'r1 to r2'}
        self.assertDictEqual(expected_result, eth1.dict())
        expected_result ={'category': 'physical', 'description': 'r1 to sw1'}
        self.assertDictEqual(expected_result, eth0.dict())

    def test_edges(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        test_node = nidb.node("r1")
        eth0 = test_node.interface(1)
        self.assertListEqual(eth0.edges(), [('r1', 'sw1', 0)])

    def test_neighbors(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        test_node = nidb.node("r1")
        eth0 = test_node.interface(1)
        result = [str(n) for n in eth0.neighbors()]
        expected_result = ['sw1.sw1 to r1']
        self.assertListEqual(expected_result, result)















if __name__ == '__main__':
    unittest.main()
