import autonetkit
import autonetkit.log as log


anm = autonetkit.NetworkModel()
g_phy = anm.add_overlay("phy")
for index in range(5):
    node_id = "r_%s" % index
    g_phy.create_node(node_id)

print g_phy.nodes()
for node in g_phy:
    print node
    print node._ports
    for interface in range(3):
        node.add_interface()

sw = g_phy.create_node("sw1")
sw.set('device_type', "switch")
dummy_iface = sw.add_interface()

for node in g_phy:
    for iface in node:
        g_phy.create_edge(dummy_iface, iface)
        print sw.edges()


for edge in g_phy.edges():
    print edge.get('_ports')
