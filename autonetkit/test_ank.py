import unittest
import netaddr
import networkx as nx
import autonetkit
import autonetkit.ank as ank_utils


class TestAnk(unittest.TestCase):
    def test_sn_preflen_to_network(self):
        result = ank_utils.sn_preflen_to_network('1', '2')
        expected_result = netaddr.IPNetwork('1.0.0.0/2')
        self.assertEqual(expected_result, result)
        result = ank_utils.sn_preflen_to_network('1', '4')
        expected_result = netaddr.IPNetwork('1.0.0.0/4')
        self.assertEqual(expected_result, result)
        result = ank_utils.sn_preflen_to_network('5', '4')
        expected_result = netaddr.IPNetwork('5.0.0.0/4')
        self.assertEqual(expected_result, result)

    def test_fqdn(self):
        anm = autonetkit.topos.house()
        r1 = anm['phy'].node("r1")
        self.assertEqual(ank_utils.fqdn(r1), 'r1.1')
        r2 = anm['phy'].node("r2")
        self.assertEqual(ank_utils.fqdn(r2), 'r2.1')

    def test_name_folder_safe(self):
        result = ank_utils.name_folder_safe('ank')
        self.assertEqual(result, 'ank')
        result = ank_utils.name_folder_safe('ank/repo')
        self.assertEqual(result, 'ank_repo')
        result = ank_utils.name_folder_safe('auto.net.kit.repo')
        self.assertEqual(result, 'auto_net_kit_repo')
        result = ank_utils.name_folder_safe('ank.folder')
        self.assertEqual(result, 'ank_folder')
        result = ank_utils.name_folder_safe('ank__repo')
        self.assertEqual(result, 'ank_repo')

    def test_set_node_default(self):
        anm = autonetkit.topos.house()
        g_phy = anm['phy']
        r1 = g_phy.node("r1")
        r2 = g_phy.node("r2")
        r3 = g_phy.node("r3")
        r4 = g_phy.node("r4")
        r5 = g_phy.node("r5")
        r1.set("color", "blue")
        result = [(n, n.get("color")) for n in g_phy]
        expected_result = [(r4, None), (r5, None), (r1, 'blue'), (r2, None), (r3, None)]
        self.assertListEqual(expected_result, result)
        ank_utils.set_node_default(g_phy, color="red")
        result = [(n, n.get("color")) for n in g_phy]
        expected_result = [(r4, 'red'), (r5, 'red'), (r1, 'blue'), (r2, 'red'), (r3, 'red')]
        self.assertListEqual(expected_result, result)
        # Can also set for a specific bunch of nodes
        nodes = ["r1", "r2", "r3"]
        ank_utils.set_node_default(g_phy, nodes, role="core")
        result = [(n, n.get("role")) for n in g_phy]
        expected_result = [(r4, None), (r5, None), (r1, 'core'), (r2, 'core'), (r3, 'core')]
        self.assertListEqual(expected_result, result)

    def test_copy_node_attr_from(self):
        anm = autonetkit.topos.house()
        g_in = anm['input']
        g_phy = anm['phy']
        result = [n.get("color") for n in g_phy]
        expected_result = [None, None, None, None, None]
        self.assertEqual(expected_result, result)
        ank_utils.set_node_default(g_in, color="red")
        ank_utils.copy_node_attr_from(g_in, g_phy, "color")
        result = [n.get("color") for n in g_phy]
        expected_result = ['red', 'red', 'red', 'red', 'red']
        self.assertListEqual(expected_result, result)
        # Can specify a default value if unset
        nodes = ["r1", "r2", "r3"]
        r1 = g_in.node('r1')
        r2 = g_in.node('r2')
        r3 = g_in.node('r3')
        r4 = g_in.node('r4')
        r5 = g_in.node('r5')
        ank_utils.set_node_default(g_in, nodes, role="core")
        ank_utils.copy_node_attr_from(g_in, g_phy, "role", default="edge")
        result = [(n, n.get("role")) for n in g_phy]
        expected_result = [(r4, 'edge'), (r5, 'edge'), (r1, 'core'),
                           (r2, 'core'), (r3, 'core')]

        self.assertListEqual(expected_result, result)
        # Can specify the remote attribute to set
        ank_utils.copy_node_attr_from(g_in, g_phy, "role",
                                 "device_role", default="edge")
        result = [(n, n.get('device_role')) for n in g_phy]
        expected_result = [(n, n.get('role') if n.get('role') else 'edge')
                           for n in g_in]
        self.assertListEqual(expected_result, result)
        # Can specify the type to cast to
        g_in.update(memory="32")
        ank_utils.copy_node_attr_from(g_in, g_phy, "memory", type=int)
        result = [n.get("memory") for n in g_phy]
        expected_result = [32, 32, 32, 32, 32]
        self.assertEqual(expected_result, result)

    def test_copy_int_attr_from(self):
        anm = autonetkit.topos.house()
        g_in = anm['input']
        g_phy = anm['phy']
        result = [iface.get('ospf_cost') for node in g_phy for iface in node]
        expected_result = [None, None, None, None, None, None, None, None,
                           None, None, None, None]
        self.assertListEqual(expected_result, result)
        for node in g_in:
            for interface in node:
                interface.set('ospf_cost', 10)
        ank_utils.copy_int_attr_from(g_in, g_phy, "ospf_cost")
        result = [iface.get('ospf_cost') for node in g_phy for iface in node]
        expected_result = [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10]
        self.assertListEqual(expected_result, result)

    def test_copy_edge_attr_from(self):
        anm = autonetkit.topos.house()
        g_in = anm['input']
        g_phy = anm['phy']
        r1 = g_in.node('r1')
        r2 = g_in.node('r2')
        r3 = g_in.node('r3')
        r4 = g_in.node('r4')
        r5 = g_in.node('r5')
        expected_result = [(r4, r5), (r4, r2), (r5, r3),
                           (r1, r2), (r1, r3), (r2, r3)]
        self.assertListEqual(expected_result, g_in.edges())
        self.assertListEqual(expected_result, g_phy.edges())
        g_in.edge("r1", "r2").set('color', "red")
        result = g_in.edges(color="red")
        expected_result = [(r1, r2)]
        self.assertListEqual(expected_result, result)
        ank_utils.copy_edge_attr_from(g_in, g_phy, 'color')
        result = g_phy.edges(color="red")
        expected_result = [(r1, r2)]
        self.assertListEqual(expected_result, result)
        # test for nbuch
        g_in.edge("r1", "r2").set('color', "blue")
        g_in.edge("r2", "r3").set('color', "blue")
        edge = g_in.edge("r2", "r3")
        ank_utils.copy_edge_attr_from(g_in, g_phy, 'color', ebunch=[edge])
        expected_result = [(r2, r3)]
        result = g_phy.edges(color="blue")
        self.assertListEqual(expected_result, result)
        ank_utils.copy_edge_attr_from(g_in, g_phy, 'color')
        expected_result = [(r1, r2), (r2, r3)]
        result = g_phy.edges(color="blue")
        self.assertListEqual(expected_result, result)

    def test_wrap_edges(self):
        anm = autonetkit.topos.house()
        g_phy = anm['phy']
        r1 = g_phy.node('r1')
        r2 = g_phy.node('r2')
        r3 = g_phy.node('r3')
        elist = [("r1", "r2"), ("r2", "r3")]
        edges = ank_utils.wrap_edges(g_phy, elist)
        # The edges are now NetworkModel edge objects
        expected_result = [(r1, r2), (r2, r3)]
        self.assertListEqual(expected_result, edges)

    def test_wrap_nodes(self):
        anm = autonetkit.topos.house()
        g_phy = anm['phy']
        r1 = g_phy.node('r1')
        r2 = g_phy.node('r2')
        r3 = g_phy.node('r3')
        nlist = ["r1", "r2", "r3"]
        nodes = ank_utils.wrap_nodes(g_phy, nlist)
        # The nodes are now NetworkModel node objects
        self.assertListEqual(nodes, [r1, r2, r3])
        # This is generally used in internal functions.
        # An alternative method is:f
        result = [g_phy.node(n) for n in nlist]
        self.assertListEqual(result, [r1, r2, r3])

    def test_in_edges(self):
        g = nx.MultiDiGraph()
        g.add_edges_from([(1, 2), (3, 4), (1, 6)])
        self.assertListEqual(g.out_edges(1), [(1, 2), (1, 6)])
        self.assertListEqual(g.in_edges(1), [])
        self.assertListEqual(g.in_edges(4), [(3, 4)])

    def test_split(self):
        anm = autonetkit.topos.house()
        g_phy = anm['phy']
        edge = g_phy.edge("r1", "r2")
        new_nodes = ank_utils.split_edge(g_phy, edge)
        r1 = g_phy.node('r1')
        r2 = g_phy.node('r2')
        r1_r2 = g_phy.node('r1_r2')
        self.assertListEqual(new_nodes, [r1_r2])
        result = [n.neighbors() for n in new_nodes]
        self.assertListEqual([[r1, r2]], result)
        # For multiple edges and specifying a prepend for the new nodes
        anm = autonetkit.topos.house()
        g_phy = anm['phy']
        edges = g_phy.node("r2").edges()
        new_nodes = ank_utils.split_edges(g_phy, edges, id_prepend="split_")
        split_r2_r4 = g_phy.node('split_r2_r4')
        split_r1_r2 = g_phy.node('split_r1_r2')
        split_r2_r3 = g_phy.node('split_r2_r3')
        expected_result = [split_r2_r4, split_r1_r2, split_r2_r3]
        self.assertListEqual(expected_result, new_nodes)
        result = [n.neighbors() for n in new_nodes]
        r3 = g_phy.node('r3')
        r4 = g_phy.node('r4')
        expected_result = [[r4, r2], [r1, r2], [r2, r3]]
        self.assertListEqual(expected_result, result)

    def test_explode_nodes(self):
        anm = autonetkit.topos.mixed()
        g_phy = anm['phy']
        r1 = g_phy.node('r1')
        r2 = g_phy.node('r2')
        switches = g_phy.switches()
        exploded_edges = ank_utils.explode_nodes(g_phy, switches)
        self.assertListEqual(exploded_edges, [(r1, r2)])
        # Or to explode a specific node
        anm = autonetkit.topos.house()
        g_phy = anm['phy']
        r1 = g_phy.node('r1')
        r2 = g_phy.node('r2')
        r3 = g_phy.node('r3')
        r4 = g_phy.node('r4')
        r5 = g_phy.node('r5')
        self.assertListEqual(g_phy.nodes(), [r4, r5, r1, r2, r3])
        result = sorted(g_phy.edges())
        expected_result = [(r1, r2), (r1, r3), (r2, r3), (r4, r2),
                           (r4, r5), (r5, r3)]
        self.assertListEqual(expected_result, result)
        exploded_edges = ank_utils.explode_node(g_phy, r2)
        expected_result = [(r1, r4), (r3, r4), (r1, r3)]
        self.assertListEqual(exploded_edges, expected_result)
        self.assertListEqual(g_phy.nodes(), [r4, r5, r1, r3])
        result = sorted(g_phy.edges())
        expected_result = [(r1, r3), (r4, r1), (r4, r3), (r4, r5), (r5, r3)]
        self.assertListEqual(expected_result, result)

    def test_label(self):
        anm = autonetkit.topos.house()
        g_phy = anm['phy']
        r1 = g_phy.node("r1")
        r2 = g_phy.node("r2")
        r5 = g_phy.node("r5")
        result = ank_utils.label(g_phy, [r1, r2, r5])
        self.assertListEqual(['r1', 'r2', 'r5'], result)

    def test_connected_subgraphs(self):
        anm = autonetkit.topos.house()
        g_phy = anm['phy']
        r1 = g_phy.node('r1')
        r2 = g_phy.node('r2')
        r3 = g_phy.node('r3')
        r4 = g_phy.node('r4')
        r5 = g_phy.node('r5')
        result = ank_utils.connected_subgraphs(g_phy)
        expected_result = [[r4, r5, r1, r2, r3]]
        self.assertListEqual(expected_result, result)
        edge_1 = g_phy.edge(r2, r4)
        edge_2 = g_phy.edge(r3, r5)
        edges = [edge_1, edge_2]
        g_phy.remove_edges_from(edges)
        result = ank_utils.connected_subgraphs(g_phy)
        expected_result = [[r1, r2, r3], [r4, r5]]
        self.assertListEqual(expected_result, result)

    def test_aggregate_nodes(self):
        anm = autonetkit.topos.house()
        g_phy = anm['phy']
        r2 = g_phy.node('r2')
        r3 = g_phy.node('r3')
        r5 = g_phy.node('r5')
        rlist = ['r4', 'r2']
        result = ank_utils.aggregate_nodes(g_phy, rlist)
        self.assertListEqual(result, [(r2, r5)])
        alist = ['r1', 'r2', 'r3', 'r4']
        result = ank_utils.aggregate_nodes(g_phy, alist)
        self.assertListEqual(result, [(r3, r5)])

    def test_most_frequent(self):
        rlist = ['r1', 'r2', 'r3', 'r1']
        self.assertEqual(ank_utils.most_frequent(rlist), 'r1')
        rlist = ['r1', 'r2', 'r3', 'r1', 'r3', 'r3']
        self.assertEqual(ank_utils.most_frequent(rlist), 'r3')

    def test_neigh_most_frequent(self):
        anm = autonetkit.topos.house()
        g_phy = anm['phy']
        self.assertEqual(ank_utils.neigh_most_frequent(g_phy, "r2", "asn"), 1)
        self.assertEqual(ank_utils.neigh_most_frequent(g_phy, "r5", "asn"), 1)

    def test_neigh_average(self):
        anm = autonetkit.topos.house()
        g_phy = anm['phy']
        self.assertEqual(ank_utils.neigh_average(g_phy, "r5", "asn"), 1.5)
        self.assertEqual(ank_utils.neigh_average(g_phy, "r3", "asn"), 1.3333333333333333)

    def test_neigh_equal(self):
        anm = autonetkit.topos.house()
        g_phy = anm['phy']
        self.assertFalse(ank_utils.neigh_equal(g_phy, "r2", "asn"))
        self.assertTrue(ank_utils.neigh_equal(g_phy, "r1", "asn"))

    def test_unique_attr(self):
        from sets import Set
        anm = autonetkit.topos.house()
        g_phy = anm['phy']
        self.assertSetEqual(ank_utils.unique_attr(g_phy, "asn"), Set([1, 2]))

    def test_groupby(self):
        anm = autonetkit.topos.house()
        g_phy = anm['phy']
        r1 = g_phy.node('r1')
        r2 = g_phy.node('r2')
        r3 = g_phy.node('r3')
        r4 = g_phy.node('r4')
        r5 = g_phy.node('r5')
        expected_result = {1: [r1, r2, r3], 2: [r4, r5]}
        self.assertDictEqual(expected_result, g_phy.groupby("asn"))

    def test_shortest_path(self):
        anm = autonetkit.topos.house()
        g_phy = anm['phy']
        r1 = g_phy.node('r1')
        r2 = g_phy.node('r2')
        r3 = g_phy.node('r3')
        r4 = g_phy.node('r4')
        r5 = g_phy.node('r5')
        self.assertListEqual(ank_utils.shortest_path(g_phy, 'r1', 'r2'), [r1, r2])
        self.assertListEqual(ank_utils.shortest_path(g_phy, 'r1', 'r4'), [r1, r2, r4])
        self.assertListEqual(ank_utils.shortest_path(g_phy, 'r1', 'r5'), [r1, r3, r5])

    def test_boundary_nodes(self):
        anm = autonetkit.topos.house()
        g_phy = anm['phy']
        r4 = g_phy.node('r4')
        r2 = g_phy.node('r2')
        rlist = ["r4", "r2"]
        self.assertListEqual(ank_utils.boundary_nodes(g_phy, rlist), [r4, r2, r2])

    def test_shallow_copy_nx_graph(self):
        G = nx.Graph()
        H = ank_utils.shallow_copy_nx_graph(G)
        self.assertIsInstance(H, nx.Graph)
        self.assertNotIsInstance(H, nx.DiGraph)
        self.assertNotIsInstance(H, nx.MultiGraph)
        self.assertNotIsInstance(H, nx.MultiDiGraph)
        G = nx.DiGraph()
        H = ank_utils.shallow_copy_nx_graph(G)
        self.assertIsInstance(H, nx.DiGraph)
        G = nx.MultiGraph()
        H = ank_utils.shallow_copy_nx_graph(G)
        self.assertIsInstance(H, nx.MultiGraph)
        G = nx.MultiDiGraph()
        H = ank_utils.shallow_copy_nx_graph(G)
        self.assertIsInstance(H, nx.MultiDiGraph)

    def test_neigh_attr(self):
        anm = autonetkit.topos.house()
        g_phy = anm['phy']
        genexp = ank_utils.neigh_attr(g_phy, "r2", "asn")
        result = [item for item in genexp]
        self.assertListEqual([2, 1, 1], result)


if __name__ == '__main__':
    unittest.main()
