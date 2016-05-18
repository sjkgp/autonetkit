import autonetkit.ank as ank_utils

def build_layer1(anm):
    import autonetkit.design.layer1
    autonetkit.design.layer1.build_layer1(anm)

def build_layer2(anm):
    import autonetkit.design.layer2
    autonetkit.design.layer2.build_layer2(anm)

def build_layer3(anm):
    """ l3_connectivity graph: switch nodes aggregated and exploded"""
    g_in = anm['input']
    gl2_conn = anm['layer2_conn']
    g_l3 = anm.add_overlay("layer3")
    g_l3.copy_nodes_from(gl2_conn)
    ank_utils.copy_node_attr_from(gl2_conn, g_l3, 'label')
    nbunch = g_in.switches()
    g_l3.copy_nodes_from(nbunch)
    ank_utils.copy_node_attr_from(g_in, g_l3, 'asn', nbunch=nbunch)
    g_l3.add_edges_from(gl2_conn.edges())

    switches = g_l3.switches()

    ank_utils.aggregate_nodes(g_l3, switches)
    exploded_edges = ank_utils.explode_nodes(g_l3,
                                             switches)

    # explode each seperately?
    for edge in exploded_edges:
        edge.set('multipoint', True)
        edge.src_int.set('multipoint', True)
        edge.dst_int.set('multipoint', True)