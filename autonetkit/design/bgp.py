import autonetkit.ank as ank_utils
import autonetkit.log as log

#@call_log


def build_ibgp_v4(anm):
    # TODO: remove the bgp layer and have just ibgp and ebgp
    # TODO: build from design rules, currently just builds from ibgp links in bgp layer
    # TODO: base on generic ibgp graph, rather than bgp graph
    g_bgp = anm['bgp']
    g_phy = anm['phy']
    g_ibgpv4 = anm.add_overlay("ibgp_v4", directed=True)
    ipv4_nodes = set(g_phy.routers("use_ipv4"))
    if len(ipv4_nodes) == 0:
        return
    nbunch = (n for n in g_bgp if n in ipv4_nodes)
    g_ibgpv4.copy_nodes_from(nbunch)
    retain=["ibgp_role", "hrr_cluster", "rr_cluster"]
    for attr in retain:
        ank_utils.copy_node_attr_from(g_bgp, g_ibgpv4, attr, nbunch=nbunch)
    ebunch = g_bgp.edges(type="ibgp")
    g_ibgpv4.copy_edges_from(ebunch)
    ank_utils.copy_edge_attr_from(g_bgp, g_ibgpv4, 'direction', ebunch=ebunch)


def build_ibgp_v6(anm):
    # TODO: remove the bgp layer and have just ibgp and ebgp
    # TODO: build from design rules, currently just builds from ibgp links in bgp layer
    # TODO: base on generic ibgp graph, rather than bgp graph
    g_bgp = anm['bgp']
    g_phy = anm['phy']
    g_ibgpv6 = anm.add_overlay("ibgp_v6", directed=True)
    ipv6_nodes = set(g_phy.routers("use_ipv6"))
    if len(ipv6_nodes) == 0:
        return
    nbunch = (n for n in g_bgp if n in ipv6_nodes)
    g_ibgpv6.copy_nodes_from(nbunch)
    retain=["ibgp_role", "hrr_cluster", "rr_cluster"]
    for attr in retain:
        ank_utils.copy_node_attr_from(g_bgp, g_ibgpv6, attr, nbunch=nbunch)
    ebunch = g_bgp.edges(type="ibgp")
    g_ibgpv6.copy_edges_from(ebunch)
    ank_utils.copy_edge_attr_from(g_bgp, g_ibgpv6, 'direction', ebunch=ebunch)


def build_ebgp_v4(anm):
    # TODO: remove the bgp layer and have just ibgp and ebgp
    # TODO: build from design rules, currently just builds from ibgp links in
    # bgp layer
    g_ebgp = anm['ebgp']
    g_phy = anm['phy']
    g_ebgpv4 = anm.add_overlay("ebgp_v4", directed=True)
    ipv4_nodes = set(g_phy.routers("use_ipv4"))
    if len(ipv4_nodes) == 0:
        return
    g_ebgpv4.copy_nodes_from(n for n in g_ebgp if n in ipv4_nodes)
    g_ebgpv4.copy_edges_from(g_ebgp.edges())
    ank_utils.copy_edge_attr_from(g_ebgp, g_ebgpv4, 'direction')


def build_ebgp_v6(anm):
    # TODO: remove the bgp layer and have just ibgp and ebgp
    # TODO: build from design rules, currently just builds from ibgp links in
    # bgp layer
    g_ebgp = anm['ebgp']
    g_phy = anm['phy']
    g_ebgpv6 = anm.add_overlay("ebgp_v6", directed=True)
    ipv6_nodes = set(g_phy.routers("use_ipv6"))
    if len(ipv6_nodes) == 0:
        return
    g_ebgpv6.copy_nodes_from(n for n in g_ebgp if n in ipv6_nodes)
    g_ebgpv6.copy_edges_from(g_ebgp.edges())
    ank_utils.copy_edge_attr_from(g_ebgp, g_ebgpv6, 'direction')

def build_ebgp(anm):
    g_l3 = anm['layer3']

    g_ebgp = anm.add_overlay("ebgp", directed=True)

    g_ebgp.copy_nodes_from(g_l3.routers())
    ank_utils.copy_int_attr_from(g_l3, g_ebgp, "multipoint")

    ebgp_edges = [e for e in g_l3.edges() if e.src.get('asn') != e.dst.get('asn')]
    new_edges = g_ebgp.copy_edges_from(ebgp_edges, bidirectional=True)
    for e in new_edges:
        e.set('type', 'ebgp')

def build_ibgp(anm):
    g_in = anm['input']
    g_bgp = anm['bgp']

    # TODO: build direct to ibgp graph - can construct combined bgp for vis
    #TODO: normalise input property

    ank_utils.copy_node_attr_from(g_in, g_bgp, "ibgp_role")
    ank_utils.copy_node_attr_from(
        g_in, g_bgp, "ibgp_l2_cluster", "hrr_cluster", default=None)
    ank_utils.copy_node_attr_from(
        g_in, g_bgp, "ibgp_l3_cluster", "rr_cluster", default=None)

    # TODO: add more detailed logging

    for n in g_bgp:
        # Tag with label to make logic clearer
        if n.get('ibgp_role') is None:
            n.set('ibgp_role', "Peer")

            # TODO: if top-level, then don't mark as RRC

    ibgp_nodes = [n for n in g_bgp if not n.get('ibgp_role') is "Disabled"]

    # Notify user of non-ibgp nodes
    non_ibgp_nodes = [n for n in g_bgp if n.get('ibgp_role') is "Disabled"]
    if 0 < len(non_ibgp_nodes) < 10:
        log.info("Skipping iBGP for iBGP disabled nodes: %s", non_ibgp_nodes)
    elif len(non_ibgp_nodes) >= 10:
        log.info("Skipping iBGP for more than 10 iBGP disabled nodes:"
                 "refer to visualization for resulting topology.")

    # warn for any nodes that have RR set but no rr_cluster, or HRR set and no
    # hrr_cluster
    rr_mismatch = [
        n for n in ibgp_nodes if n.get('ibgp_role') == "RR" and n.get('rr_cluster') is None]
    if len(rr_mismatch):
        log.warning("Some routers are set as RR but have no rr_cluster: %s. Please specify an rr_cluster for peering."
                    % ", ".join(str(n) for n in rr_mismatch))

    hrr_mismatch = [
        n for n in ibgp_nodes if n.get('ibgp_role') == "HRR" and n.get('hrr_cluster') is None]
    if len(hrr_mismatch):
        log.warning("Some routers are set as HRR but have no hrr_cluster: %s. Please specify an hrr_cluster for peering."
                    % ", ".join(str(n) for n in hrr_mismatch))

    for _, asn_devices in ank_utils.groupby("asn", ibgp_nodes):
        asn_devices = list(asn_devices)

        # iBGP peer peers with
        peers = [n for n in asn_devices if n.get('ibgp_role') == "Peer"]
        rrs = [n for n in asn_devices if n.get('ibgp_role') == "RR"]
        hrrs = [n for n in asn_devices if n.get('ibgp_role') == "HRR"]
        rrcs = [n for n in asn_devices if n.get('ibgp_role') == "RRC"]

        over_links = []
        up_links = []
        down_links = []

        # 0. RRCs can only belong to either an rr_cluster or a hrr_cluster
        invalid_rrcs = [r for r in rrcs if r.get('rr_cluster') is not None
                        and r.get('hrr_cluster') is not None]
        if len(invalid_rrcs):
            message = ", ".join(str(r) for r in invalid_rrcs)
            log.warning("RRCs can only have either a rr_cluster or hrr_cluster set. "
                        "The following have both set, and only the rr_cluster will be used: %s", message)

        # TODO: do we also want to warn for RRCs with no cluster set? Do we also exclude these?
        # TODO: do we also want to warn for HRRs and RRs with no cluster set?
        # Do we also exclude these?

        # 1. Peers:
        # 1a. Peers connect over to peers
        over_links += [(s, t) for s in peers for t in peers]
        # 1b. Peers connect over to RRs
        over_links += [(s, t) for s in peers for t in rrs]

        # 2. RRs:
        # 2a. RRs connect over to Peers
        over_links += [(s, t) for s in rrs for t in peers]
        # 2b. RRs connect over to RRs
        over_links += [(s, t) for s in rrs for t in rrs]
        # 2c. RRs connect down to RRCs in same rr_cluster
        down_links += [(s, t) for s in rrs for t in rrcs
                       if s.get('rr_cluster') == t.get('rr_cluster') != None]
        # 2d. RRs connect down to HRRs in the same rr_cluster
        down_links += [(s, t) for s in rrs for t in hrrs
                       if s.get('rr_cluster') == t.get('rr_cluster') != None]

        # 3. HRRs
        # 3a. HRRs connect up to RRs in the same rr_cluster
        up_links += [(s, t) for s in hrrs for t in rrs
                     if s.get('rr_cluster') == t.get('rr_cluster') != None]
        # 3b. HRRs connect down to RRCs in same hrr_cluster (providing RRC has
        # no rr_cluster set)
        down_links += [(s, t) for s in hrrs for t in rrcs
                       if s.get('hrr_cluster') == t.get('hrr_cluster') != None
                       and t.get('rr_cluster') is None]

        # 4. RRCs
        # 4a. RRCs connect up to RRs in the same rr_cluster (regardless if RRC
        # has hrr_cluster set)
        up_links += [(s, t) for s in rrcs for t in rrs
                     if s.get('rr_cluster') == t.get('rr_cluster') != None]
        # 3b. RRCs connect up to HRRs in same hrr_cluster (providing RRC has no
        # rr_cluster set)
        up_links += [(s, t) for s in rrcs for t in hrrs
                     if s.get('hrr_cluster') == t.get('hrr_cluster') != None
                     and s.get('rr_cluster') is None]

        # Remove self-links
        over_links = [(s.loopback_zero, t.loopback_zero) for s, t in over_links if s != t]
        up_links = [(s.loopback_zero, t.loopback_zero) for s, t in up_links if s != t]
        down_links = [(s.loopback_zero, t.loopback_zero) for s, t in down_links if s != t]

        new_edges = g_bgp.create_edges_from(over_links)
        for e in new_edges:
            e.set('type', 'ibgp')
            e.set('direction', 'over')
        new_edges = g_bgp.create_edges_from(up_links)
        for e in new_edges:
            e.set('type', 'ibgp')
            e.set('direction', 'up')
        new_edges = g_bgp.create_edges_from(down_links)
        for e in new_edges:
            e.set('type', 'ibgp')
            e.set('direction', 'down')

def build_bgp(anm):
    """Build iBGP end eBGP overlays"""
    # eBGP
    g_in = anm['input']
    g_l3 = anm['layer3']

    if not anm['phy'].data.enable_routing:
        log.info("Routing disabled, not configuring BGP")
        return

    build_ebgp(anm)
    build_ebgp_v4(anm)
    build_ebgp_v6(anm)

    """TODO: remove from here once compiler updated"""
    g_bgp = anm.add_overlay("bgp", directed=True)
    g_bgp.copy_nodes_from(g_l3.routers())
    edges_to_add = [e for e in g_l3.edges()
                    if e.src in g_bgp and e.dst in g_bgp]
    g_bgp.copy_edges_from(edges_to_add, bidirectional=True)
    ank_utils.copy_int_attr_from(g_l3, g_bgp, "multipoint")

    # remove ibgp links

    """TODO: remove up to here once compiler updated"""
    ank_utils.copy_node_attr_from(
        g_in, g_bgp, "custom_config_bgp", dst_attr="custom_config")

    # log.info("Building eBGP")
    ebgp_nodes = [d for d in g_bgp if any(
        edge.get('type') == 'ebgp' for edge in d.edges())]
    g_bgp.update(ebgp_nodes, ebgp=True)

    for ebgp_edge in g_bgp.edges(type="ebgp"):
        for interface in ebgp_edge.interfaces():
            interface.set('ebgp', True)

    for edge in g_bgp.edges(type='ibgp'):
        # TODO: need interface querying/selection. rather than hard-coded ids
        # TODO: create a new port (once API allows) rarher than binding to
        # loopback zero
        edge.bind_interface(edge.src, 0)

    # TODO: need to initialise interface zero to be a loopback rather than physical type
    # TODO: wat is this for?
    for node in g_bgp:
        for interface in node.interfaces():
            interface.set('multipoint', any(e.get('multipoint') for e in interface.edges()))

    # log.info("Building iBGP")
    build_ibgp(anm)
    build_ibgp_v4(anm)
    build_ibgp_v6(anm)
