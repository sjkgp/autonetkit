import unittest
import autonetkit

class TestDmBase(unittest.TestCase):
    def setUp(self):
        self.anm_house = autonetkit.topos.house()
        self.anm_mixed = autonetkit.topos.mixed()
        self.anm_multi = autonetkit.topos.multi_edge()

    def test_repr(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        self.assertEqual(str(nidb),'nidb')

    def test_is_multigraph(self):
        nidb = autonetkit.DeviceModel(self.anm_house)
        self.assertTrue(nidb.is_multigraph())
        # TODO: does this make sense?
        # anm = autonetkit.topos.multi_edge()
        # self.assertTrue(nidb.is_multigraph())

    def test_save(self):
        nidb = autonetkit.DeviceModel(self.anm_house)
        nidb.save()
        # TODO: validate that the dump was saved

    def test_interface(self):
        nidb = autonetkit.DeviceModel(self.anm_house)
        test_node = nidb.node("r1")
        eth0 = test_node.interface(1)
        self.assertEqual(str(nidb.interface(eth0)), 'r1.r1 to r2')

    def test_name(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        self.assertEqual(nidb.name, 'nidb')

    def test_raw_graph(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        nidb.__setstate__('r1')
        self.assertEqual(nidb.raw_graph(), 'r1')

    def test_len(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        self.assertEqual(len(nidb), 5)

    def test_node(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        test_node = nidb.node("r1")
        eth0 = test_node.interface(1)
        self.assertEqual(nidb.node(eth0), test_node)

    def test_routers(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        r1 = nidb.node("r1")
        r2 = nidb.node("r2")
        r3 = nidb.node("r3")
        self.assertListEqual(nidb.routers(), [r1, r2, r3])

    def test_switches(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        sw1 = nidb.node('sw1')
        self.assertListEqual(nidb.switches(), [sw1])

    def test_servers(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        s1 = nidb.node('s1')
        self.assertListEqual(nidb.servers(), [s1])

    def test_l3devices(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        s1 = nidb.node('s1')
        r1 = nidb.node('r1')
        r2 = nidb.node('r2')
        r3 = nidb.node('r3')
        result = nidb.l3devices()
        expected_result = [s1, r1, r2, r3]
        self.assertListEqual(expected_result, result)

    def test_edges(self):
        anm = autonetkit.NetworkModel()
        g_phy = anm['phy']
        nidb = autonetkit.DeviceModel(anm)
        input_edges = [("r1", "r2"), ("r2", "r4"),
                       ("r3", "r4"), ("r3", "r5"),
                       ("r1", "r3")]
        nodes = ['r1', 'r2', 'r3', 'r4', 'r5']
        g_in = anm.add_overlay("input")
        g_in.add_nodes_from(nodes)
        r1 = g_in.node('r1')
        r2 = g_in.node('r2')
        r3 = g_in.node('r3')
        r4 = g_in.node('r4')
        r5 = g_in.node('r5')
        result = g_in.add_edges_from(input_edges)
        expected_result = [(r1, r2), (r2, r4), (r3, r4), (r3, r5), (r1, r3)]
        self.assertListEqual(expected_result, result)
        g_phy.add_nodes_from(g_in)
        result = g_phy.add_edges_from(g_in.edges())
        expected_result = [(r4, r2), (r4, r3), (r5, r3), (r1, r2), (r1, r3)]
        self.assertListEqual(expected_result, result)
        retain = ['label', 'host', 'platform', 'x', 'y', 'asn', 'device_type']
        nidb.add_nodes_from(g_phy, retain=retain)
        nidb.add_edges_from(g_phy.edges())
        result = list(nidb.edges())
        expected_result = [(r4, r2, 0), (r4, r3, 0),
                           (r5, r3, 0), (r1, r2, 0),
                           (r1, r3, 0)]
        self.assertListEqual(expected_result, result)

    def test_add_edges_from(self):
        anm = autonetkit.NetworkModel()
        g_phy = anm['phy']
        nidb = autonetkit.DeviceModel(anm)
        input_edges = [("r1", "r2"), ("r2", "r4"), ("r3", "r4"),
                       ("r3", "r5"), ("r1", "r3")]
        nodes = ['r1', 'r2', 'r3', 'r4', 'r5']
        g_in = anm.add_overlay("input")
        g_in.add_nodes_from(nodes)
        r1 = g_in.node('r1')
        r2 = g_in.node('r2')
        r3 = g_in.node('r3')
        r4 = g_in.node('r4')
        r5 = g_in.node('r5')
        result = g_in.add_edges_from(input_edges)
        expected_result = [(r1, r2), (r2, r4), (r3, r4), (r3, r5), (r1, r3)]
        self.assertListEqual(expected_result, result)
        g_phy.add_nodes_from(g_in)
        result = g_phy.add_edges_from(g_in.edges())
        expected_result = [(r4, r2), (r4, r3), (r5, r3), (r1, r2), (r1, r3)]
        self.assertListEqual(expected_result, result)
        retain = ['label', 'host', 'platform', 'x', 'y', 'asn', 'device_type']
        nidb.add_nodes_from(g_phy, retain=retain)
        nidb.add_edges_from(g_phy.edges())
        result = list(nidb.edges())
        expected_result = [(r4, r2, 0), (r4, r3, 0), (r5, r3, 0),
                           (r1, r2, 0), (r1, r3, 0)]
        self.assertListEqual(expected_result, result)

    def test_restore_latest(self):
        anm = autonetkit.topos.mixed()
        nidb = autonetkit.DeviceModel(anm)
        nidb.restore_latest()
        # WARNING No previous DeviceModel saved. Please compile new DeviceModel

    def test_data(self):
        anm = autonetkit.topos.mixed()
        nidb = autonetkit.DeviceModel(anm)
        self.assertIsInstance(nidb.data, autonetkit.nidb.device_model.DmGraphData)
        # DeviceModel data: {'topologies': defaultdict(<type 'dict'>, {}), 'timestamp': '20150421_143139'}

if __name__ == '__main__':
    unittest.main()
