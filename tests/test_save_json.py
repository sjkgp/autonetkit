import autonetkit
from autonetkit import ank as ank_utils
import autonetkit.ank_json
import json


def setup_input():
    anm = autonetkit.NetworkModel()

    g_in = anm.add_overlay("input")

    r1 = g_in.create_node("r1")
    r2 = g_in.create_node("r2")
    r1.set('x', 100)
    r1.set('y', 100)
    r2.set('x', 250)
    r2.set('y', 250)
    g_in.update(device_type="router")
    g_in.update(asn=1)

    r1_eth0 = r1.add_interface("eth0", id="eth0")
    r2_eth0 = r2.add_interface("eth0", id="eth0")

    new_edge = g_in.create_edge(r1_eth0, r2_eth0)
    new_edge.set('type', 'physical')

    print g_in.edges()

    return anm


def test():

    from autonetkit.build_network import initialise, build_phy

    anm = setup_input()
    # apply_design_rules(anm)
    build_phy(anm)
    # trim out non-used values

    g_phy = anm["phy"]
    r1_phy = g_phy.node("r1")

    r1_phy_lo100 = r1_phy.add_interface(
        "Loopback100", id="Loopback100", category="logical")

    for iface in r1_phy.interfaces():
        print iface.dump()

    g_phy_live = anm.add_overlay("phy_live", multi_edge=True)
    g_phy_live.copy_nodes_from(anm['phy'])
    g_phy_live.copy_edges_from(anm['phy'].edges())
    g_phy_live.data.paths = []  # to store paths onto
    ank_utils.copy_int_attr_from(anm['phy'], anm['phy_live'], "id")

    for overlay_id in ("ospf_live", "eigrp_live", "rip_live", "isis_live"):
        g_overlay = anm.add_overlay(
            overlay_id, directed=True, multi_edge=True)
        g_overlay.copy_nodes_from(anm['phy'])

    for overlay_id in ("ibgp_v4_live", "ebgp_v4_live"):
        g_overlay = anm.add_overlay(overlay_id, directed=True,)
        g_overlay.copy_nodes_from(anm['phy'])

    print anm.overlays()

    g_ospf_live = anm["ospf_live"]
    print g_ospf_live.nodes()
    r1_ospf = g_ospf_live.node("r1")
    r2_ospf = g_ospf_live.node("r2")
    r1_eth0_ospf = r1_ospf.interface("eth0")
    r2_eth0_ospf = r2_ospf.interface("eth0")
    g_ospf_live.create_edge(r1_eth0_ospf, r2_eth0_ospf)

    r1_ospf_lo101 = r1_ospf.add_interface(
        "Loopback102", category="logical")

    # assert(r1_ospf_lo101.id == "Loopback101")

    # test with adding a virtual interface
    print "--"

    for iface in r1_ospf.interfaces():
        print iface.dump()

    autonetkit.update_vis(anm)

    body = autonetkit.ank_json.dumps(anm)

    data = json.loads(body)

    j_phy = data["phy"]
    for node in j_phy["nodes"]:
        print node
        for port, port_data in node["_ports"].items():
            print port_data
    j_ospf_live = data["ospf_live"]


    print "after"


    for iface in r1_phy.interfaces():
        print iface.dump()

    print "--"
    assert(r1_ospf_lo101.id == "Loopback102")
    for iface in r1_ospf.interfaces():
        print iface.dump()

    # send_visualization()
