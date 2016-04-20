import unittest
import autonetkit

class TestNmPort(unittest.TestCase):

    def setUp(self):
        self.anm_house = autonetkit.topos.house()
        self.anm_mixed = autonetkit.topos.mixed()
        self.anm_multi = autonetkit.topos.multi_edge()

    def test_hash(self):
        g_phy = self.anm_house['phy']
        test_node = g_phy.node("r1")
        eth0 = test_node.interface(1)
        self.assertEqual(hash(eth0), 2346446788448031185)

    def test_repr(self):
        g_phy = self.anm_house['phy']
        test_node = g_phy.node("r1")
        eth0 = test_node.interface(1)
        self.assertEqual(eth0.__repr__(), 'eth0.r1')

    def test_eq(self):
        g_phy = self.anm_house['phy']
        test_node = g_phy.node("r1")
        eth0 = test_node.interface(1)
        self.assertEqual(eth0, eth0)

    def test_nonzero(self):
        g_phy = self.anm_house['phy']
        test_node = g_phy.node("r1")
        eth0 = test_node.interface(1)
        self.assertTrue(eth0)

    def test_lt(self):
        g_phy = self.anm_house['phy']
        test_node = g_phy.node("r1")
        eth0 = test_node.interface(1)
        self.assertFalse(eth0 < eth0)

    def test_id(self):
        g_phy = self.anm_house['phy']
        test_node = g_phy.node("r1")
        eth0 = test_node.interface(1)
        self.assertEqual(eth0.id, 'eth0')

    def test_is_bound(self):
        g_phy = self.anm_house['phy']
        test_node = g_phy.node("r1")
        eth0 = test_node.interface(1)
        self.assertTrue(eth0.is_bound)

    def test_node(self):
        g_phy = self.anm_house['phy']
        test_node = g_phy.node("r1")
        eth0 = test_node.interface(1)
        expected_result = {'_ports': {0: {'category': 'physical',
                                          'description': None},
                                      1: {'category': 'physical',
                                          'description': 'r1 to r2',
                                          'id': 'eth0'},
                                      2: {'category': 'physical',
                                          'description': 'r1 to r3',
                                          'id': 'eth1'}},
                           'label': 'r1',
                           'device_type': 'router',
                           'y': 400,
                           'x': 350,
                           'asn': 1}
        self.assertDictEqual(expected_result, eth0._node)

    def test_interface(self):
        g_phy = self.anm_house['phy']
        test_node = g_phy.node("r1")
        loopback0 = test_node.interface(0)
        eth0 = test_node.interface(1)
        expected_result = {'category': 'physical',
                           'description': 'r1 to r2',
                           'id': 'eth0'}
        self.assertDictEqual(expected_result, eth0._interface)

    def test_phy(self):
        g_phy = self.anm_house['phy']
        test_node = g_phy.node("r1")
        eth0 = test_node.interface(1)
        eth1 = test_node.interface(2)
        self.assertEqual(str(eth0.phy), 'eth0.r1')
        self.assertEqual(str(eth1.phy), 'eth1.r1')

    def test_is_loopback(self):
        g_phy = self.anm_house['phy']
        test_node = g_phy.node("r1")
        eth0 = test_node.interface(1)
        self.assertFalse(eth0.is_loopback)
        loopback0 = test_node.interface(0)
        self.assertTrue(loopback0.is_loopback)

    def test_is_physical(self):
        g_phy = self.anm_house['phy']
        test_node = g_phy.node("r1")
        eth0 = test_node.interface(1)
        eth1 = test_node.interface(2)
        loopback0 = test_node.interface(0)
        self.assertTrue(eth0.is_physical)
        self.assertTrue(eth1.is_physical)
        self.assertFalse(loopback0.is_physical)

    def test_description(self):
        g_phy = self.anm_house['phy']
        test_node = g_phy.node("r1")
        eth0 = test_node.interface(1)
        self.assertEqual(eth0.description, 'r1 to r2')

    def test_is_loopback_zero(self):
        g_phy = self.anm_house['phy']
        test_node = g_phy.node("r1")
        eth0 = test_node.interface(1)
        loopback0 = test_node.interface(0)
        self.assertFalse(eth0.is_loopback_zero)
        self.assertTrue(loopback0.is_loopback_zero)

    def test_category(self):
        g_phy = self.anm_house['phy']
        test_node = g_phy.node("r1")
        eth0 = test_node.interface(1)
        loopback0 = test_node.interface(0)
        self.assertEqual(eth0.category, 'physical')
        self.assertEqual(loopback0.category, 'loopback')

    def test_node(self):
        g_phy = self.anm_house['phy']
        test_node = g_phy.node("r1")
        eth0 = test_node.interface(1)
        eth1 = test_node.interface(2)
        loopback0 = test_node.interface(0)
        self.assertEqual(eth0.node, test_node)
        self.assertEqual(eth1.node, test_node)
        self.assertEqual(loopback0.node, test_node)

    def test_dump(self):
        g_phy = self.anm_house['phy']
        test_node = g_phy.node('r1')
        loopback0 = test_node.interface(0)
        eth0 = test_node.interface(1)
        expected_result = "[('category', 'physical'), ('description', 'r1 to r2'), ('id', 'eth0')]"
        self.assertEqual(eth0.dump(), expected_result)

# TODO: get/set method testing

    def test_edges(self):
        g_phy = self.anm_house['phy']
        test_node = g_phy.node('r1')
        r2 = g_phy.node('r2')
        loopback0 = test_node.interface(0)
        eth0 = test_node.interface(1)
        self.assertListEqual(eth0.edges(), [(test_node, r2)])

    def test_neighbors(self):
        g_phy = self.anm_house['phy']
        test_node = g_phy.node("r1")
        eth0 = test_node.interface(1)
        eth1 = test_node.interface(2)
        result = [str(i) for i in eth0.neighbors()]
        self.assertListEqual(result, ['eth0.r2'])
        result = [str(i) for i in eth1.neighbors()]
        self.assertListEqual(result, ['eth0.r3'])



if __name__ == '__main__':
    unittest.main()
