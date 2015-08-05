import autonetkit
import autonetkit.log as log
import unittest


# class MyTest(unittest.TestCase):
def test():
    anm = autonetkit.NetworkModel()

    g_in = anm.add_overlay("input")
    nodes = ['r1', 'r2', 'r3', 'r4', 'r5']
    input_edges = [
        ("r1", "r2"), ("r2", "r4"), ("r3", "r4"), ("r3", "r5"), ("r1", "r3")]
    g_in.add_nodes_from(nodes)

    positions = {'r3': (107, 250), 'r5': (380, 290), 'r1': (
        22, 50), 'r2': (377, 9), 'r4': (571, 229)}
    for node in g_in:
        node.x = positions[node][0]
        node.y = positions[node][1]
        eth0 = node.add_interface("eth0")
        eth0.speed = 100

    input_interface_edges = [(g_in.node(src).interface(
        1), g_in.node(dst).interface(1)) for src, dst in input_edges]

    g_in.update(device_type="router", asn=1)
    g_in.update("r3", asn=2)
    g_in.update("r2", device_type="switch")
    g_in.add_edges_from(input_interface_edges)

    g_phy = anm['phy']
    g_phy.add_nodes_from(g_in, retain=["asn", "device_type", "x", "y"])
    g_phy.add_edges_from(g_in.edges())

    autonetkit.update_http(anm)
    # Should already work without adding the nodes
    nidb = autonetkit.DeviceModel(anm)

    nidb.add_nodes_from(g_phy, retain=["asn", "device_type", "x", "y"])
    nidb.add_edges_from(g_phy.edges())

    # test whether nodes are added in correctly from add_nodes_from
    # assert(nidb.node("r1") == r1)
    # assert(nidb.node("r2") == r2)
    # assert(nidb.node("r3") == r3)
    # assert(nidb.node("r4") == r4)
    # assert(nidb.node("r5") == r5)
    # assert(not nidb.node("r6") == r6)

    test_node = nidb.node("r1")

    # test NIDB node #1
    test_node = nidb.node("r1")
    assert(test_node.asn == 1)
    assert(test_node.device_type == "router")
    assert(test_node.is_l3device())
    assert(test_node.is_router())
    assert(not test_node.is_switch())
    assert(not test_node.is_server())
    assert(not test_node.is_firewall())
    assert(test_node.label == "r1")
    assert(test_node.id == "r1")
    assert(bool(test_node) == True)
    # assert(test_node.interface() == 'r1.r1 to r2')
    assert(test_node._next_int_id == 2)

    # test NIDB node #2
    test_node2 = nidb.node("r2")
    assert(test_node2.asn == 1)
    assert(test_node2.device_type == "switch")
    assert(not test_node2.is_l3device())
    assert(not test_node2.is_router())
    assert(test_node2.is_switch())
    assert(not test_node2.is_server())
    assert(test_node2.label == "r2")
    assert(test_node2.id == "r2")
    assert(bool(test_node2) == True)
    # assert(test_node.interface() == 'r1.r1 to r2')
    assert(test_node2._next_int_id == 2)

    # test NIDB node #3
    test_node = nidb.node("r3")
    assert(test_node.asn == 2)
    assert(test_node.device_type == "router")
    assert(test_node.is_router())

    # test loopback interface
    test_node = nidb.node("r1")
    loopback0 = test_node.interface(0)
    assert(not loopback0.is_bound)
    assert(loopback0.is_loopback)
    assert(not loopback0.is_physical)
    assert(loopback0.is_loopback_zero)
    assert(loopback0.description == 'loopback')
    assert(loopback0.node == 'r1')
    assert(not loopback0.node == 'r3')

    # test node interface
    eth0 = test_node.interface(1)
    assert(eth0.is_bound)
    assert(not eth0.is_loopback)
    assert(not eth0.is_loopback_zero)
    assert(eth0.is_physical)
    assert(eth0.description == "eth0")
    assert(eth0.node == "r1")
    assert(not eth0.node == "r2")
    # assert(eth0.dict() == "{'category': 'physical', 'description': 'eth0'}")
    # print eth0.edges()
    #TODO: these need to be the edges themselves, not strings
    assert(str(eth0.edges()) == "[(r1, r2, 0), (r1, r3, 0)]")
    assert(str(eth0.neighbors()) == "[r2.eth0, r3.eth0]")
    # graph data
    nidb.data.test = 123
    assert(nidb.data.test == 123)

    # graph level tests
    assert(nidb.node("r1").degree() == 2)
    assert(nidb.node("r3").degree() == 3)
    assert(nidb.name == 'nidb')
    assert(nidb.node(eth0) == "r1")
    #TODO: replace the string comparisons with the objects themselves
    assert(str(nidb.routers()) == "[r4, r5, r1, r3]")
    assert(str(nidb.l3devices()) == "[r4, r5, r1, r3]")
    assert(str(nidb.switches()) == "[r2]")
    # Check add_edges_from worked properly
    assert(str(list(nidb.edges())) ==
           "[(r4, r2, 0), (r4, r3, 0), (r5, r3, 0), (r1, r2, 0), (r1, r3, 0)]")
    # Comparison test
    r1 = nidb.node('r1')
    rb = nidb.node('r1')
    r2 = nidb.node('r2')
    assert(r1 == rb)
    assert(not r1 == r2)

    # Adding in edge test cases.
    #TODO: fix these so that they get the edge from the anm
    return

    edge_a1 = nidb.edge("r1", "r2")
    edge_a2 = nidb.edge("r1", "r2")
    assert(edge_a1 == edge_a2)
    edge_a3 = nidb.edge("r4", "r3")
    assert(edge_a3 == edge_a1)
    assert(bool(edge_a1) is True)

    assert(edge_a1 == ("r1", "r2"))
    assert(edge_a1 != ("r1", "r3"))

    added_edge = nidb.add_edge("r5", "r6")
    assert(nidb.edge("r5", "r6") is not None)

    # Adding node, then seeing if nodes are updated
    # Checks add_nodes_from
    nodes = ['r1', 'r2', 'r3', 'r4', 'r5', 'r6']
    g_in.add_nodes_from(nodes)
    g_phy.add_nodes_from(g_in, retain=["asn", "device_type", "x", "y"])
    nidb = autonetkit.DeviceModel(anm)
    nidb.add_nodes_from(g_phy, retain=["asn", "device_type", "x", "y"])
    r6 = nidb.node('r6')
    r5 = nidb.node('r5')
    assert(r6 in nidb)
    assert(r5 in nidb)

test()
