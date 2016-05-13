import autonetkit.log as log
import autonetkit.ank as ank_utils

# TODO: extract the repeated code and use the layer2  and layer3 graphs


def build_igp(anm):
    build_ospf(anm)
    build_eigrp(anm)
    build_isis(anm)
    build_rip(anm)

    # Build a protocol summary graph
    g_igp = anm.add_overlay("igp")
    igp_protocols = ["ospf", "eigrp", "isis", "rip"]
    for protocol in igp_protocols:
        g_protocol = anm[protocol]
        g_igp.add_nodes_from(g_protocol, igp=protocol)
        g_igp.add_edges_from(g_protocol.edges(), igp=protocol)

#@call_log


def build_ospf(anm):
    """
    Build OSPF graph.

    Allowable area combinations:
    0 -> 0
    0 -> x (x!= 0)
    x -> 0 (x!= 0)
    x -> x (x != 0)

    Not-allowed:
    x -> x (x != y != 0)

    """
    import netaddr
    g_in = anm['input']
    g_l3 = anm['layer3']
    g_phy = anm['phy']
    # add regardless, so allows quick check of node in anm['ospf'] in compilers
    g_ospf = anm.add_overlay("ospf")

    if not any(n.get('igp') == "ospf" for n in g_phy):
        g_ospf.log.debug("No OSPF nodes")
        return

    if not anm['phy'].data.enable_routing:
        g_ospf.log.info("Routing disabled, not configuring OSPF")
        return

    ospf_nodes = [n for n in g_l3 if n['phy'].get('igp') == "ospf"]
    g_ospf.add_nodes_from(ospf_nodes)
    g_ospf.add_edges_from(g_l3.edges(), warn=False)
    ank_utils.copy_int_attr_from(g_l3, g_ospf, "multipoint")

    for node in g_ospf:
        for interface in node.physical_interfaces():
            interface.set('cost', 1)

    ank_utils.copy_node_attr_from(g_in, g_ospf, "ospf_area", dst_attr="area")
    ank_utils.copy_node_attr_from(
        g_in, g_ospf, "custom_config_ospf", dst_attr="custom_config")

    g_ospf.remove_edges_from([link for link in g_ospf.edges(
    ) if link.src.get('asn') != link.dst.get('asn')])  # remove inter-AS links

    area_zero_ip = netaddr.IPAddress("0.0.0.0")
    area_zero_int = 0
    area_zero_ids = {area_zero_ip, area_zero_int}
    default_area = area_zero_int
    if any(router.get('area') == "0.0.0.0" for router in g_ospf):
        # string comparison as hasn't yet been cast to IPAddress
        default_area = area_zero_ip

    for router in g_ospf:
        if not router.get('area') or router.get('area') == "None":
            router.set('area', default_area)
            # check if 0.0.0.0 used anywhere, if so then use 0.0.0.0 as format
        else:
            try:
                router.set('area', int(router.get('area')))
            except ValueError:
                try:
                    router.set('area', netaddr.IPAddress(router.get('area')))
                except netaddr.core.AddrFormatError:
                    router.log.warning("Invalid OSPF area %s. Using default"
                                       " of %s" % (router.get('area'), default_area))
                    router.set('area', default_area)

    # TODO: use interfaces throughout, rather than edges
    for router in g_ospf:
        # and set area on interface
        for edge in router.edges():
            if edge.get('area'):
                continue  # allocated (from other "direction", as undirected)
            if router.get('area') == edge.dst.get('area'):
                edge.set('area', router.get('area'))  # intra-area
                continue

            if router.get('area') in area_zero_ids or edge.dst.get('area') in area_zero_ids:
                # backbone to other area
                if router.get('area') in area_zero_ids:
                    # router in backbone, use other area
                    edge.set('area', edge.dst.get('area'))
                else:
                    # router not in backbone, use its area
                    edge.set('area', router.get('area'))

    for router in g_ospf:
        areas = {edge.get('area') for edge in router.edges()}
        router.set('areas', list(areas))  # edges router participates in

        if len(areas) in area_zero_ids:
            router.set('type', "backbone") # no ospf edges (eg single node in AS)
        elif len(areas) == 1:
            # single area: either backbone (all 0) or internal (all nonzero)
            if len(areas & area_zero_ids):
                # intersection has at least one element -> router has area zero
                router.set('type', 'backbone')
            else:
                router.set('type', 'internal')

        else:
            # multiple areas
            if len(areas & area_zero_ids):
                # intersection has at least one element -> router has area zero
                router.set('type', 'backbone ABR')
            elif router.get('area') in area_zero_ids:
                router.log.debug(
                    "Router belongs to area %s but has no area zero interfaces",
                    router.get('area'))
                router.set('type', 'backbone ABR')
            else:
                router.log.warning(
                    "spans multiple areas but is not a member of area 0")
                router.set('type', 'INVALID')

    if (any(area_zero_int in router.get('areas') for router in g_ospf) and
            any(area_zero_ip in router.get('areas') for router in g_ospf)):
        router.log.warning("Using both area 0 and area 0.0.0.0")

    for link in g_ospf.edges():
        if not link.get('cost'):
            link.set('cost', 1)

    # map areas and costs onto interfaces
    # TODO: later map them directly rather than with edges - part of
    # the transition
    for edge in g_ospf.edges():
        for interface in edge.interfaces():
            interface.set('cost', edge.get('cost'))
            interface.set('area', edge.get('area'))
            interface.set('multipoint', edge.get('multipoint'))

    for router in g_ospf:
        router.loopback_zero.set('area', router.get('area'))
        router.loopback_zero.set('cost', 0)
        router.set('process_id', router.get('asn'))

def ip_to_net_ent_title_ios(ip_addr):
    """ Converts an IP address into an OSI Network Entity Title
    suitable for use in IS-IS on IOS
    """
    try:
        ip_words = ip_addr.words
    except AttributeError:
        import netaddr  # try to cast to IP Address
        ip_addr = netaddr.IPAddress(ip_addr)
        ip_words = ip_addr.words

    log.debug("Converting IP to OSI ENT format")
    area_id = "49"
    ip_octets = "".join("%03d" % int(
        octet) for octet in ip_words)  # single string, padded if needed
    return ".".join([area_id, ip_octets[0:4], ip_octets[4:8], ip_octets[8:12],
                     "00"])

def build_eigrp(anm):
    """Build eigrp overlay"""
    g_in = anm['input']
    # add regardless, so allows quick check of node in anm['isis'] in compilers
    g_l3 = anm['layer3']
    g_eigrp = anm.add_overlay("eigrp")
    g_phy = anm['phy']

    if not any(n.get('igp') == "eigrp" for n in g_phy):
        log.debug("No EIGRP nodes")
        return

    if not anm['phy'].data.enable_routing:
        g_eigrp.log.info("Routing disabled, not configuring EIGRP")
        return

    eigrp_nodes = [n for n in g_l3 if n['phy'].get('igp') == "eigrp"]
    g_eigrp.add_nodes_from(eigrp_nodes)
    g_eigrp.add_edges_from(g_l3.edges(), warn=False)
    ank_utils.copy_int_attr_from(g_l3, g_eigrp, "multipoint")

    ank_utils.copy_node_attr_from(
        g_in, g_eigrp, "custom_config_eigrp", dst_attr="custom_config")

# Merge and explode switches
    ank_utils.aggregate_nodes(g_eigrp, g_eigrp.switches())
    exploded_edges = ank_utils.explode_nodes(g_eigrp,
                                             g_eigrp.switches())
    for edge in exploded_edges:
        edge.set('multipoint', True)

    g_eigrp.remove_edges_from(
        [link for link in g_eigrp.edges() if link.src.get('asn') != link.dst.get('asn')])

    for node in g_eigrp:
        node.set('process_id', node.get('asn'))

    for link in g_eigrp.edges():
        link.set('metric', 1)  # default

    for edge in g_eigrp.edges():
        for interface in edge.interfaces():
            interface.set('metric', edge.get('metric'))
            interface.set('multipoint', edge.get('multipoint'))

def build_network_entity_title(anm):
    g_isis = anm['isis']
    g_ipv4 = anm['ipv4']
    for node in g_isis.routers():
        ip_node = g_ipv4.node(node)
        node.set('net', ip_to_net_ent_title_ios(ip_node.get('loopback')))


def build_rip(anm):
    """Build rip overlay"""
    g_in = anm['input']
    g_l3 = anm['layer3']
    g_rip = anm.add_overlay("rip")
    g_phy = anm['phy']

    if not any(n.get('igp') == "rip-v2" for n in g_phy):
        log.debug("No rip nodes")
        return

    if not anm['phy'].data.enable_routing:
        g_rip.log.info("Routing disabled, not configuring RIP")
        return

    rip_nodes = [n for n in g_l3 if n['phy'].get('igp') == "rip-v2"]
    g_rip.add_nodes_from(rip_nodes)
    g_rip.add_edges_from(g_l3.edges(), warn=False)
    ank_utils.copy_int_attr_from(g_l3, g_rip, "multipoint")

    ank_utils.copy_node_attr_from(
        g_in, g_rip, "custom_config_rip", dst_attr="custom_config")

    g_rip.remove_edges_from(
        [link for link in g_rip.edges() if link.src.get('asn') != link.dst.get('asn')])

    for node in g_rip:
        node.set('process_id', node.get('asn'))

    for link in g_rip.edges():
        link.set('metric', 1)  # default

    for edge in g_rip.edges():
        for interface in edge.interfaces():
            interface.set('metric', edge.get('metric'))
            interface.set('multipoint', edge.get('multipoint'))


def build_isis(anm):
    """Build isis overlay"""
    g_in = anm['input']
    # add regardless, so allows quick check of node in anm['isis'] in compilers
    g_l3 = anm['layer3']
    g_phy = anm['phy']
    g_isis = anm.add_overlay("isis")

    if not any(n.get('igp') == "isis" for n in g_phy):
        g_isis.log.debug("No ISIS nodes")
        return

    if not anm['phy'].data.enable_routing:
        g_isis.log.info("Routing disabled, not configuring ISIS")
        return

    isis_nodes = [n for n in g_l3 if n['phy'].get('igp') == "isis"]
    g_isis.add_nodes_from(isis_nodes)
    g_isis.add_edges_from(g_l3.edges(), warn=False)
    ank_utils.copy_int_attr_from(g_l3, g_isis, "multipoint")

    ank_utils.copy_node_attr_from(
        g_in, g_isis, "custom_config_isis", dst_attr="custom_config")

    g_isis.remove_edges_from(
        [link for link in g_isis.edges() if link.src.get('asn') != link.dst.get('asn')])

    build_network_entity_title(anm)

    for node in g_isis.routers():
        node.set('process_id', node.get('asn'))

    for link in g_isis.edges():
        link.set('metric', 1)  # default

    for edge in g_isis.edges():
        for interface in edge.interfaces():
            interface.set('metric', edge.get('metric'))
            interface.set('multipoint', edge.get('multipoint'))
