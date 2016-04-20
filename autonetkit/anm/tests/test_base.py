import logging
import unittest
import autonetkit

class TestOverlayBase(unittest.TestCase):

    def setUp(self):
        self.anm_house = autonetkit.topos.house()
        self.anm_mixed = autonetkit.topos.mixed()
        self.anm_multi = autonetkit.topos.multi_edge()

    def test_repr(self):
        self.assertEqual(str(self.anm_house['phy']), 'phy')

    def test_is_multigraph(self):
        self.assertFalse(self.anm_house['phy'].is_multigraph())
        self.assertTrue(self.anm_multi['phy'].is_multigraph())

    def test_is_directed(self):
        self.assertFalse(self.anm_house['phy'].is_directed())
        self.assertFalse(self.anm_multi['phy'].is_directed())

    def test_contains(self):
        self.assertIn("r1", self.anm_house['phy'])
        self.assertNotIn("test",self.anm_house['phy'])

    def test_interface(self):
        g_phy = self.anm_house['phy']
        eth0 = test_node = g_phy.node("r1")
        test_node = g_phy.node("r1")
        eth0 = test_node.interface(1)
        self.assertEqual(str(g_phy.interface(eth0)), 'eth0.r1')

    def test_edge(self):
        g_phy = self.anm_house['phy']
        e_r1_r2 = g_phy.edge("r1", "r2")
        # Can also find from an edge
        e_r1_r2_input = self.anm_house['input'].edge(e_r1_r2)
        # And for multi-edge graphs can specify key
        e1 = self.anm_multi['phy'].edge("r1", "r2", 0)
        e2 = self.anm_multi['phy'].edge("r1", "r2", 1)
        self.assertNotEqual(e1, e2)
        autonetkit.update_http(self.anm_house)
        eth0_r1 = self.anm_house["phy"].node("r1").interface("eth0")
        eth3_r1 = self.anm_house["phy"].node("r1").interface("eth3")
        eth0_r2 = self.anm_house["phy"].node("r2").interface("eth0")
        self.assertTrue(self.anm_house["phy"].has_edge(eth0_r1, eth0_r2))
        self.assertFalse(self.anm_house["phy"].has_edge(eth3_r1, eth0_r2))

    def test_getitem(self):
        g_phy = self.anm_house['phy']
        self.assertIsNone(g_phy.__getitem__('1'))
        self.assertEqual(str(g_phy.__getitem__('r1')), 'r1')

    def test_node(self):
        g_phy = self.anm_house['phy']
        r1 = g_phy.node("r1")
        self.assertIsInstance(r1, autonetkit.anm.NmNode)
        r1_input = self.anm_house['input'].node(r1)
        self.assertIsInstance(r1_input, autonetkit.anm.NmNode)

    def test_overlay(self):
        g_phy = self.anm_house['phy']
        g_input = g_phy.overlay('input')
        self.assertEqual(g_input._overlay_id, 'input')
        self.assertIsInstance(g_input, autonetkit.anm.NmGraph)

    def test_name(self):
        g_phy = self.anm_house['phy']
        self.assertEqual(g_phy.name, 'phy')

    def test_nonzero(self):
        g_phy = self.anm_house['phy']
        self.assertTrue(g_phy)

    def test_node_label(self):
        g_phy = self.anm_house['phy']
        self.assertEqual(g_phy.node_label('r1'), 'r1')
        self.assertEqual(g_phy.node_label('r2'), 'r2')

    def test_has_edge(self):
        g_phy = self.anm_house['phy']
        r1 = g_phy.node("r1")
        r2 = g_phy.node("r2")
        r5 = g_phy.node("r5")
        self.assertTrue(g_phy.has_edge(r1, r2))
        self.assertFalse(g_phy.has_edge(r1, r5))
        e_r1_r2 = self.anm_house['input'].edge(r1, r2)
        self.assertTrue(g_phy.has_edge(e_r1_r2))

    def test_iter(self):
        anm = autonetkit.topos.multi_as()
        g_phy = anm["phy"]
        result = [str(node) for node in list(sorted(g_phy))]
        # TODO: write function which would retrieve all objects defined in list by str
        expected_result = ['r1', 'r2', 'r3', 'r4', 'r5', 'r6', 'r7', 'r8', 'r9', 'r10']
        self.assertListEqual(expected_result, result)

    def test_len(self):
        anm = autonetkit.topos.multi_as()
        g_phy = anm["phy"]
        result = [str(node) for node in g_phy.nodes()]
        expected_result = ['r4', 'r5', 'r6', 'r7', 'r1', 'r2', 'r3', 'r8', 'r9', 'r10']
        self.assertListEqual(expected_result, result)
        self.assertEqual(len(g_phy), 10)

    def test_nodes(self):
        anm = autonetkit.topos.multi_as()
        g_phy = anm["phy"]
        result = [str(node) for node in g_phy.nodes()]
        expected_result = ['r4', 'r5', 'r6', 'r7', 'r1', 'r2', 'r3', 'r8', 'r9', 'r10']
        self.assertListEqual(expected_result, result)
        result = [str(node) for node in g_phy.nodes(asn=1)]
        expected_result = ['r4', 'r5', 'r1', 'r2', 'r3']
        self.assertListEqual(expected_result, result)
        result = [str(node) for node in g_phy.nodes(asn=3)]
        expected_result = ['r7', 'r8', 'r9', 'r10']
        self.assertListEqual(result, expected_result)
        result = [str(node) for node in g_phy.nodes(asn=1, ibgp_role="RR")]
        expected_result = ['r4', 'r5']
        self.assertListEqual(expected_result, result)
        result = [str(node) for node in g_phy.nodes(asn=1, ibgp_role="RRC")]
        expected_result = ['r1', 'r2', 'r3']
        self.assertListEqual(expected_result, result)

    def test_routers(self):
        result = self.anm_mixed['phy'].routers()
        expected_result = ['r1', 'r2', 'r3']
        self.assertListEqual(expected_result, result)

    def test_switches(self):
        result = self.anm_mixed['phy'].switches()
        switch = self.anm_mixed['phy'].node('sw1')
        self.assertListEqual(result, [switch])

    def test_servers(self):
        result = self.anm_mixed['phy'].servers()
        server = self.anm_mixed['phy'].node('s1')
        self.assertListEqual(result, [server])

    def test_l3devices(self):
        result = self.anm_mixed['phy'].l3devices()
        expected_result = ['s1', 'r1', 'r2', 'r3']
        self.assertListEqual(expected_result, result)

    def test_device(self):
        g_phy = self.anm_house['phy']
        self.assertEqual(g_phy.device('r1'), g_phy.node('r1'))
        self.assertEqual(g_phy.device('r2'), g_phy.node('r2'))

    def test_groupby(self):
        g_phy = self.anm_house['phy']
        result = g_phy.groupby("asn")
        r1 = g_phy.node('r1')
        r2 = g_phy.node('r2')
        r3 = g_phy.node('r3')
        r4 = g_phy.node('r4')
        r5 = g_phy.node('r5')
        expected_result = {1: [r1, r2, r3], 2: [r4, r5]}
        self.assertDictEqual(expected_result, result)
        # Can also specify a subset to work from
        nodes = [n for n in g_phy if n.degree() > 2]
        result = g_phy.groupby("asn", nodes=nodes)
        expected_result = {1: [r2, r3]}
        self.assertDictEqual(expected_result, result)

    def test_filter(self):
        g_phy = self.anm_house['phy']
        result = [str(node) for node in g_phy.filter()]
        expected_result = ['r4', 'r5', 'r1', 'r2', 'r3']
        self.assertListEqual(expected_result, result)
        self.assertListEqual(g_phy.filter("r1"), ['r', '1'])
        self.assertListEqual(g_phy.filter("r"), ['r'])
        self.assertListEqual(g_phy.filter("r3"), ['r', '3'])
        self.assertListEqual(g_phy.filter("1"), ['1'])
        self.assertListEqual(g_phy.filter("4"), ['4'])

    def test_edges(self):
        g_phy = self.anm_house['phy']
        r1 = g_phy.node('r1')
        r2 = g_phy.node('r2')
        r3 = g_phy.node('r3')
        r4 = g_phy.node('r4')
        r5 = g_phy.node('r5')
        result = g_phy.edges()
        expected_result = [(r4, r5), (r4, r2), (r5, r3), (r1, r2), (r1, r3), (r2, r3)]
        self.assertListEqual(expected_result, result)
        g_phy.edge("r1", "r2").set('color', "red")
        result = g_phy.edges(color = "red")
        self.assertListEqual(result, [(r1, r2)])




if __name__ == '__main__':
    unittest.main()





