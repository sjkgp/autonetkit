#!/usr/bin/python
# -*- coding: utf-8 -*-
from collections import defaultdict

import autonetkit.log as log
import netaddr
from autonetkit.ank import sn_preflen_to_network
from autonetkit.compiler import sort_sessions
from autonetkit.compilers.device.router_base import RouterCompiler


class IosBaseCompiler(RouterCompiler):

    """Base IOS compiler"""

    lo_interface_prefix = 'Loopback'
    lo_interface = '%s%s' % (lo_interface_prefix, 0)

    def ibgp_session_data(self, session, ip_version):
        """Wraps RouterCompiler ibgp_session_data
        adds vpnv4 = True if ip_version == 4 and session is in g_ibgp_vpn_v4"""

        data = super(IosBaseCompiler, self).ibgp_session_data(session,
                                                              ip_version)
        if ip_version == 4:
            g_ibgp_vpn_v4 = self.anm['ibgp_vpn_v4']
            if g_ibgp_vpn_v4.has_edge(session):
                data['use_vpnv4'] = True
        return data

    def compile(self, node):
        self.vrf_igp_interfaces(node)
        phy_node = self.anm['phy'].node(node)

        node.use_cdp = phy_node.get('use_cdp')

        if node in self.anm['ospf']:
            node.add_scope("ospf")
            node.ospf['use_ipv4'] = phy_node.get('use_ipv4')
            node.ospf['use_ipv6'] = phy_node.get('use_ipv6')

        if node in self.anm['eigrp']:
            node.add_scope("eigrp")
            node.eigrp['use_ipv4'] = phy_node.get('use_ipv4')
            node.eigrp['use_ipv6'] = phy_node.get('use_ipv6')

        if node in self.anm['isis']:
            node.add_scope("isis")
            node.isis['use_ipv4'] = phy_node.get('use_ipv4')
            node.isis['use_ipv6'] = phy_node.get('use_ipv6')

        if node in self.anm['rip']:
            node.add_scope("rip")
            node.rip['use_ipv4'] = phy_node.get('use_ipv4')
            node.rip['use_ipv6'] = phy_node.get('use_ipv6')

        super(IosBaseCompiler, self).compile(node)
        if node in self.anm['isis']:
            self.isis(node)

        node.label = self.anm['phy'].node(node).label
        self.vrf(node)
        self.mpls_ldp(node)

    def interfaces(self, node):
        phy_loopback_zero = self.anm['phy'
                                     ].interface(node.loopback_zero)
        if node.ip.get('use_ipv4'):
            ipv4_loopback_subnet = netaddr.IPNetwork('0.0.0.0/32')
            ipv4_loopback_zero = phy_loopback_zero['ipv4']
            ipv4_address = ipv4_loopback_zero.get('ip_address')
            node.loopback_zero.use_ipv4 = True
            node.loopback_zero.ipv4_address = ipv4_address
            node.loopback_zero.ipv4_subnet = ipv4_loopback_subnet
            node.loopback_zero.ipv4_cidr = \
                sn_preflen_to_network(ipv4_address,
                                      ipv4_loopback_subnet.prefixlen)

        if node.ip.get('use_ipv6'):
            # TODO: clean this up so can set on router_base: call cidr not
            # address and update templates
            node.loopback_zero.use_ipv6 = True
            ipv6_loopback_zero = phy_loopback_zero['ipv6']
            node.loopback_zero.ipv6_address = \
                sn_preflen_to_network(ipv6_loopback_zero.get('ip_address'),
                                      128)

        super(IosBaseCompiler, self).interfaces(node)

        for interface in node.physical_interfaces():
            interface.use_cdp = node.use_cdp  # use node value

        for interface in node.interfaces:
            interface.sub_ints = []  # temporary until full subinterfaces

        for interface in node.physical_interfaces():
            g_ext_conn = self.anm['ext_conn']
            if node not in g_ext_conn:
                continue

            node_ext_conn = g_ext_conn.node(node)
            ext_int = node_ext_conn.interface(interface)
            for sub_int in ext_int.get('sub_int') or []:
                stanza = {'id': sub_int['id'],
                          'ipv4_address': sub_int['ipv4_address'],
                          'ipv4_prefixlen': sub_int['ipv4_prefixlen'],
                          'ipv4_subnet': sub_int['ipv4_subnet'],
                          'dot1q': sub_int['dot1q']}
                interface.sub_ints.append(stanza)

    def mpls_oam(self, node):
        g_mpls_oam = self.anm['mpls_oam']
        node.add_scope("mpls")
        node.mpls['oam'] = False

        if node not in g_mpls_oam:
            return   # no mpls oam configured

        # Node is present in mpls OAM
        node.mpls['oam'] = True

    def mpls_te(self, node):
        g_mpls_te = self.anm['mpls_te']

        if node not in g_mpls_te:
            return   # no mpls te configured

        node.mpls_te = True

        if node.isis:
            node.isis['ipv4_mpls_te'] = True
            node.isis['mpls_te_router_id'] = self.lo_interface

        if node.ospf:
            node.ospf['ipv4_mpls_te'] = True
            node.ospf['mpls_te_router_id'] = self.lo_interface

    def nailed_up_routes(self, node):
        log.debug('Configuring nailed up routes')
        phy_node = self.anm['phy'].node(node)

        if node.is_ebgp_v4 and node.ip.get('use_ipv4'):
            infra_blocks = self.anm['ipv4'].data['infra_blocks'
                                                 ].get(phy_node.get('asn')) or []
            for infra_route in infra_blocks:
                stanza = {'prefix': str(infra_route.network),
                          'netmask': str(infra_route.netmask),
                          'nexthop': "Null0",
                          'metric': 254}
                node.ipv4_static_routes.append(stanza)

        if node.is_ebgp_v6 and node.ip.get('use_ipv6'):
            infra_blocks = self.anm['ipv6'].data['infra_blocks'
                                                 ].get(phy_node.get('asn')) or []
            # TODO: setup schema with defaults
            for infra_route in infra_blocks:
                stanza = {'prefix': str(infra_route),
                          'nexthop': "Null0",
                          'metric': 254}
                node.ipv6_static_routes.append(stanza)

    def bgp(self, node):
        node.add_scope("bgp")
        node.bgp['lo_interface'] = self.lo_interface
        super(IosBaseCompiler, self).bgp(node)
        phy_node = self.anm['phy'].node(node)
        asn = phy_node.asn
        g_ebgp_v4 = self.anm['ebgp_v4']
        g_ebgp_v6 = self.anm['ebgp_v6']

        if node in g_ebgp_v4 \
                and len(list(g_ebgp_v4.node(node).edges())) > 0:
            node.is_ebgp_v4 = True
        else:
            node.is_ebgp_v4 = False

        if node in g_ebgp_v6 \
                and len(list(g_ebgp_v6.node(node).edges())) > 0:
            node.is_ebgp_v6 = True
        else:
            node.is_ebgp_v6 = False

        node.bgp['ipv4_advertise_subnets'] = []
        node.bgp['ipv6_advertise_subnets'] = []

        # Advertise loopbacks into BGP

        if node.ip.get('use_ipv4'):
            node.bgp['ipv4_advertise_subnets'] = \
                [node.loopback_zero.ipv4_cidr]
        if node.ip.get('use_ipv6'):
            node.bgp['ipv6_advertise_subnets'] = \
                [node.loopback_zero.ipv6_address]

        # Advertise infrastructure into eBGP

        if node.ip.get('use_ipv4') and node.is_ebgp_v4:
            infra_blocks = self.anm['ipv4'].data['infra_blocks'
                                                 ].get(asn) or []
            for infra_route in infra_blocks:
                node.bgp['ipv4_advertise_subnets'].append(infra_route)

        if node.ip.get('use_ipv6') and node.is_ebgp_v6:
            infra_blocks = self.anm['ipv6'].data['infra_blocks'
                                                 ].get(asn) or []
            for infra_route in infra_blocks:
                node.bgp['ipv6_advertise_subnets'].append(infra_route)

        self.nailed_up_routes(node)

        # vrf
        # TODO: this should be inside vrf section?

        node.bgp['vrfs'] = []

        vrf_node = self.anm['vrf'].node(node)
        if vrf_node and vrf_node.get('vrf_role') is 'PE':

            # iBGP sessions for this VRF

            vrf_ibgp_neighbors = defaultdict(list)

            g_ibgp_v4 = self.anm['ibgp_v4']
            for session in sort_sessions(g_ibgp_v4.edges(vrf_node)):
                if session.get('exclude') and session.get('vrf'):
                    data = self.ibgp_session_data(session, ip_version=4)
                    vrf_ibgp_neighbors[session.get('vrf')].append(data)

            g_ibgp_v6 = self.anm['ibgp_v6']
            for session in sort_sessions(g_ibgp_v6.edges(vrf_node)):
                if session.get('exclude') and session.get('vrf'):
                    data = self.ibgp_session_data(session, ip_version=6)
                    vrf_ibgp_neighbors[session.get('vrf')].append(data)

            # eBGP sessions for this VRF

            vrf_ebgp_neighbors = defaultdict(list)

            for session in sort_sessions(g_ebgp_v4.edges(vrf_node)):
                if session.get('exclude') and session.get('vrf'):
                    data = self.ebgp_session_data(session, ip_version=4)
                    vrf_ebgp_neighbors[session.get('vrf')].append(data)

            for session in sort_sessions(g_ebgp_v6.edges(vrf_node)):
                if session.get('exclude') and session.vrf:
                    data = self.ebgp_session_data(session, ip_version=6)
                    vrf_ebgp_neighbors[session.get('vrf')].append(data)

            for vrf in vrf_node.get('node_vrf_names'):
                rd_index = vrf_node.get('rd_indices')[vrf]
                rd = '%s:%s' % (node.asn, rd_index)
                stanza = {'vrf': vrf,
                          'rd': rd,
                          'use_ipv4': node.ip.get('use_ipv4'),
                          'use_ipv6': node.ip.get('use_ipv6'),
                          'vrf_ebgp_neighbors': vrf_ebgp_neighbors[vrf],
                          'vrf_ibgp_neighbors': vrf_ibgp_neighbors[vrf]}
                node.bgp['vrfs'].append(stanza)

        # Retain route_target if in ibgp_vpn_v4 and RR or HRR (set in design)

        vpnv4_node = self.anm['ibgp_vpn_v4'].node(node)
        if vpnv4_node:
            retain = False
            if vpnv4_node.get('retain_route_target'):
                retain = True
            node.bgp['vpnv4'] = {'retain_route_target': retain}

    def vrf_igp_interfaces(self, node):

        # marks physical interfaces to exclude from IGP

        vrf_node = self.anm['vrf'].node(node)
        if vrf_node and vrf_node.get('vrf_role') is 'PE':
            for interface in node.physical_interfaces():
                vrf_int = self.anm['vrf'].interface(interface)
                if vrf_int.get('vrf_name'):
                    interface.exclude_igp = True

    def vrf(self, node):
        g_vrf = self.anm['vrf']
        vrf_node = self.anm['vrf'].node(node)
        node.add_scope("vrf")
        node.vrf['vrfs'] = []
        if vrf_node and vrf_node.get('vrf_role') is 'PE':

            # TODO: check if mpls ldp already set elsewhere

            for vrf in vrf_node.get('node_vrf_names'):
                route_target = g_vrf.data.route_targets[node.asn][vrf]
                rd_index = vrf_node.get('rd_indices')[vrf]
                rd = '%s:%s' % (node.asn, rd_index)

                stanza = {'vrf': vrf,
                          'rd': rd,
                          'route_target': route_target}
                node.vrf['vrfs'].append(stanza)

            for interface in node.interfaces:
                vrf_int = self.anm['vrf'].interface(interface)
                if vrf_int.get('vrf_name'):
                    # mark interface as being part of vrf
                    interface.vrf = vrf_int.get('vrf_name')
                    if interface.physical:
                        interface.description += ' vrf %s' \
                            % vrf_int.get('vrf_name')

        node.vrf['use_ipv4'] = node.ip.get('use_ipv4')
        node.vrf['use_ipv6'] = node.ip.get('use_ipv6')
        node.vrf['vrfs'] = sorted(node.vrf['vrfs'], key=lambda x: x['vrf'])

    def mpls_ldp(self, node):
        g_mpls_ldp = self.anm['mpls_ldp']
        mpls_ldp_node = g_mpls_ldp.node(node)
        ipv4_node = self.anm["ipv4"].node(node)
        node.add_scope("mpls")
        if mpls_ldp_node and mpls_ldp_node.get('role') in ('P', 'PE'):

            # Add PE -> P, PE -> PE interfaces to MPLS LDP

            node.mpls['ldp_interfaces'] = []
            for interface in node.physical_interfaces():
                mpls_ldp_int = mpls_ldp_node.interface(interface)
                if mpls_ldp_int.is_bound:
                    node.mpls['ldp_interfaces'].append(interface.id)
                    interface.use_mpls = True

        # TODO: check if this block is repeated (redundant) logic of above
        if mpls_ldp_node and mpls_ldp_node.get('role') is 'P':
            node.mpls['ldp_interfaces'] = []
            for interface in node.physical_interfaces():
                node.mpls['ldp_interfaces'].append(interface.id)

        # TODO: refactor this logic
        if mpls_ldp_node:
            # P, PE, CE
            node.mpls['enabled'] = True
            node.mpls['router_id'] = ipv4_node.loopback_zero[
                "ipv4"].get("ip_address")

    def rip(self, node):
        # Inheriting from base compiler. Adding in interface stanza.
        super(IosBaseCompiler, self).rip(node)
        for interface in node.physical_interfaces():
            phy_int = self.anm['phy'].interface(interface)

            rip_int = phy_int['rip']
            if rip_int and rip_int.is_bound:
                if interface.exclude_igp:
                    continue

                interface.rip = {
                    'cost': rip_int.get('cost'),
                    'area': rip_int.get('area'),
                    'process_id': node.rip.get('process_id'),
                    'use_ipv4': node.ip.get('use_ipv4'),
                    'use_ipv6': node.ip.get('use_ipv6'),
                }

    def ospf(self, node):
        super(IosBaseCompiler, self).ospf(node)
        for interface in node.physical_interfaces():
            phy_int = self.anm['phy'].interface(interface)

            ospf_int = phy_int['ospf']
            if ospf_int and ospf_int.is_bound:
                if interface.exclude_igp:
                    continue  # don't configure IGP for this interface

                interface.ospf = {
                    'cost': ospf_int.get('cost'),
                    'area': ospf_int.get('area'),
                    'process_id': node.ospf.get('process_id'),
                    'use_ipv4': node.ip.get('use_ipv4'),
                    'use_ipv6': node.ip.get('use_ipv6'),
                    'multipoint': ospf_int.get('multipoint'),
                }

                # TODO: add wrapper for this

    def eigrp(self, node):
        super(IosBaseCompiler, self).eigrp(node)
        for interface in node.physical_interfaces():
            phy_int = self.anm['phy'].interface(interface)

            eigrp_int = phy_int['eigrp']
            if eigrp_int and eigrp_int.is_bound:
                if interface.exclude_igp:
                    continue  # don't configure IGP for this interface

                interface.eigrp = {
                    'metric': eigrp_int.get('metric'),
                    'area': eigrp_int.get('area'),
                    'name': node.eigrp.get('name'),
                    'use_ipv4': node.ip.get('use_ipv4'),
                    'use_ipv6': node.ip.get('use_ipv6'),
                    'multipoint': eigrp_int.get('multipoint'),
                }

                # TODO: add wrapper for this

    def isis(self, node):
        super(IosBaseCompiler, self).isis(node)
        for interface in node.physical_interfaces():
            isis_int = self.anm['isis'].interface(interface)
            edges = isis_int.edges()
            if not isis_int.is_bound:
                # Could occur for VRFs
                log.debug("No ISIS connections for interface %s" % interface)
                continue

            # TODO: change this to be is_bound and is_multipoint
            if isis_int.get('multipoint'):
                log.warning('Extended IOS config support not valid for multipoint ISIS connections on %s'
                            % interface)
                continue

                # TODO multipoint handling?

            edge = edges[0]
            dst = edge.dst
            if not dst.is_router():
                log.debug('Connection to non-router host not added to IGP'
                          )
                continue

            src_type = node.device_subtype
            dst_type = dst['phy'].get('device_subtype')
            if src_type == 'IOS XRv':
                if dst_type == 'IOSv':
                    interface.isis.hello_padding_disable = True
                elif dst_type == 'IOL':
                    interface.isis.hello_padding_disable = True
                elif dst_type == 'CSR1000v':
                    interface.isis.hello_padding_disable = True
                elif dst_type == 'NX-OSv':
                    interface.isis.hello_padding_disable = True

            if src_type == 'IOSv':
                if dst_type == 'IOS XRv':
                    interface.isis.mtu = 1430

            if src_type == 'CSR1000v':
                if dst_type == 'IOS XRv':
                    interface.isis.mtu = 1430
                if dst_type == 'IOL':
                    interface.isis.mtu = 1430

            if src_type == 'NX-OSv':
                if dst_type == 'IOS XRv':
                    interface.mtu = 1430  # for all of interface
                    interface.isis.hello_padding_disable = True
                elif dst_type == 'IOSv':
                    interface.isis.hello_padding_disable = True
                elif dst_type == 'IOL':
                    interface.isis.hello_padding_disable = True
                elif dst_type == 'CSR1000v':
                    interface.isis.hello_padding_disable = True

            interface.isis_mtu = interface.isis.mtu
            interface.hello_padding_disable = \
                interface.isis.hello_padding_disable


class IosClassicCompiler(IosBaseCompiler):

    def compile(self, node):
        super(IosClassicCompiler, self).compile(node)

        self.mpls_te(node)
        self.mpls_oam(node)
        self.gre(node)
        self.l2tp_v3(node)

        phy_node = self.anm['phy'].node(node)
        if phy_node.get('device_subtype') == 'IOSv' or phy_node.get('device_subtype') == 'IOL':

            # only copy across for certain reference platforms

            node.use_onepk = phy_node.get('use_onepk')
            node.transport_input_ssh_telnet = True
            node.no_service_config = True
            node.ipv4_cef = True
            node.ipv6_cef = True

        if phy_node.get('device_subtype') == 'CSR1000v':

            # only copy across for certain reference platforms

            node.use_onepk = phy_node.get('use_onepk')
            node.transport_input_ssh_telnet = True
            node.include_csr = True

            # Set secret password to "cisco"

            node.enable_secret = \
                'tnhtc92DXBhelxjYk8LWJrPV36S2i4ntXrpb4RFmfqY'
            node.exclude_phy_int_auto_speed_duplex = True
            node.no_service_config = True

    def rip(self, node):
        super(IosClassicCompiler, self).rip(node)

    def ospf(self, node):
        super(IosClassicCompiler, self).ospf(node)
        loopback_zero = node.loopback_zero
        ospf_node = self.anm['ospf'].node(node)
        loopback_zero.ospf = {
            'cost': 1,
            'area': ospf_node.get('area'),
            'process_id': node.ospf.get('process_id'),
            'use_ipv4': False,
            'use_ipv6': node.ip.get('use_ipv6'),
            'multipoint': False,
        }

        # TODO: add wrapper for this
    def gre(self, node):
        node.gre_tunnels = []
        if not self.anm.has_overlay('gre_tunnel'):
            return

        g_gre_tunnel = self.anm['gre_tunnel']
        if node not in g_gre_tunnel:
            return   # no gre tunnel for node

        gre_node = g_gre_tunnel.node(node)
        neighbors = gre_node.neighbors()
        for index, neigh in enumerate(neighbors, start=1):
            stanza = {'id': index, 'endpoint': neigh}

            # TODO: try/except here
            # TODO: Explain logic here
            src_int = g_gre_tunnel.edge(node, neigh).src_int
            tunnel_source = node.interface(src_int).id
            stanza['source'] = tunnel_source
            # placeholder for user to replace
            stanza['destination'] = "0.0.0.0"

            if neigh.get('tunnel_enabled_ipv4'):
                ip_address = neigh.get('tunnel_ipv4_address')
                cidr = neigh.get('tunnel_ipv4_cidr')
                stanza['ipv4_address'] = ip_address
                stanza['ipv4_subnet'] = cidr
                stanza['use_ipv4'] = True

            if neigh.get('tunnel_enabled_ipv6'):
                cidr = neigh.get('tunnel_ipv6_cidr')
                stanza['ipv4_subnet'] = cidr
                stanza['use_ipv6'] = True

            node.gre_tunnels.append(stanza)

    def l2tp_v3(self, node):
        node.l2tp_classes = []
        node.pseudowire_classes = []
        if not self.anm.has_overlay('l2tp_v3'):
            return

        g_l2tp_v3 = self.anm['l2tp_v3']
        g_phy = self.anm['phy']
        if node not in g_l2tp_v3:
            return   # no l2tp_v3 for node

        l2tp_v3_node = g_l2tp_v3.node(node)
        if l2tp_v3_node.get('role') != "tunnel":
            return  # nothing to configure

        node.l2tp_classes = list(l2tp_v3_node.get('l2tp_classes'))

        node.pseudowire_classes = []
        for pwc in l2tp_v3_node.get('pseudowire_classes'):
            stanza = {'name': pwc['name'],
                      'encapsulation': pwc['encapsulation'],
                      'protocol': pwc['protocol'],
                      'l2tp_class_name': pwc['l2tp_class_name']}
            local_interface = pwc['local_interface']

            # Lookup the interface ID allocated for this loopback by compiler
            local_interface_id = node.interface(local_interface).id
            stanza['local_interface'] = local_interface_id

            node.pseudowire_classes.append(stanza)

        for interface in node.physical_interfaces():
            phy_int = g_phy.interface(interface)
            if phy_int.get('xconnect_encapsulation') != "l2tpv3":
                continue  # no l2tpv3 encap, no need to do anything

            tunnel_int = l2tp_v3_node.interface(interface)
            stanza = {'remote_ip': tunnel_int.get('xconnect_remote_ip'),
                      'vc_id': tunnel_int.get('xconnect_vc_id'),
                      'encapsulation': "l2tpv3",
                      'pw_class': tunnel_int.get('xconnect_pw_class')}
            # TODO: need to be conscious of support for other xconnect types
            # in templates since pw_class may not apply if not l2tpv3, et

            interface.xconnect = stanza

    def eigrp(self, node):
        super(IosClassicCompiler, self).eigrp(node)
        # Numeric process IDs use "old-style" non-ipv6 EIGRP stanzas
        process_id = node.eigrp.get('process_id')
        if str(process_id).isdigit():
            process_id = "as%s" % process_id
        node.eigrp['process_id'] = process_id

    def mpls_te(self, node):
        super(IosClassicCompiler, self).mpls_te(node)

        g_mpls_te = self.anm['mpls_te']
        if node not in g_mpls_te:
            return   # no mpls te configured

        mpls_te_node = g_mpls_te.node(node)

        for interface in mpls_te_node.physical_interfaces():
            nidb_interface = self.nidb.interface(interface)
            if not interface.is_bound:
                log.debug('Not enable MPLS and RSVP for interface %s on %s '
                          % (nidb_interface.id, node))
                continue
            nidb_interface.te_tunnels = True
            nidb_interface.rsvp_bandwidth_percent = 100

    def bgp(self, node):
        super(IosClassicCompiler, self).bgp(node)

        node.bgp['use_ipv4'] = node.ip.get('use_ipv4')
        node.bgp['use_ipv6'] = node.ip.get('use_ipv6')

        # Seperate by address family

        ipv4_peers = []
        ipv6_peers = []

        # Note cast to dict - #TODO revisit this requirement
        # TODO: revisit and tidy up the logic here: split iBGP and eBGP
        # TODO: sort the peer list by peer IP

        for peer in node.bgp['ibgp_neighbors']:
            peer['remote_ip'] = peer['loopback']
            if peer['use_ipv4']:
                if node.is_ebgp_v4:
                    peer['next_hop_self'] = True
                ipv4_peers.append(peer)
            if peer['use_ipv6']:
                if node.is_ebgp_v6:
                    peer['next_hop_self'] = True
                ipv6_peers.append(peer)

        for peer in node.bgp['ibgp_rr_parents']:
            peer['remote_ip'] = peer['loopback']
            if peer['use_ipv4']:
                if node.is_ebgp_v4:
                    peer['next_hop_self'] = True
                ipv4_peers.append(peer)
            if peer['use_ipv6']:
                if node.is_ebgp_v6:
                    peer['next_hop_self'] = True
                ipv6_peers.append(peer)

        for peer in node.bgp['ibgp_rr_clients']:
            peer['rr_client'] = True
            peer['remote_ip'] = peer['loopback']
            if peer['use_ipv4']:
                if node.is_ebgp_v4:
                    peer['next_hop_self'] = True
                ipv4_peers.append(peer)
            if peer['use_ipv6']:
                if node.is_ebgp_v6:
                    peer['next_hop_self'] = True
                ipv6_peers.append(peer)

        for peer in node.bgp['ebgp_neighbors']:
            peer['is_ebgp'] = True
            peer['remote_ip'] = peer['dst_int_ip']
            if peer['use_ipv4']:
                peer['next_hop_self'] = True
                ipv4_peers.append(peer)
            if peer['use_ipv6']:
                peer['next_hop_self'] = True
                ipv6_peers.append(peer)

        node.bgp['ipv4_peers'] = ipv4_peers
        node.bgp['ipv6_peers'] = ipv6_peers

        vpnv4_neighbors = []
        if node.bgp.get('vpnv4'):
            for neigh in node.bgp['ibgp_neighbors']:
                if not neigh['use_ipv4']:
                    continue
                vpnv4_neighbors.append(neigh)

            for neigh in node.bgp['ibgp_rr_clients']:
                if not neigh['use_ipv4']:
                    continue
                neigh['rr_client'] = True
                vpnv4_neighbors.append(neigh)

            for neigh in node.bgp['ibgp_rr_parents']:
                if not neigh['use_ipv4']:
                    continue
                vpnv4_neighbors.append(neigh)

        vpnv4_neighbors = sorted(vpnv4_neighbors, key=lambda x:
                                 x['loopback'])
        node.bgp['vpnv4_neighbors'] = vpnv4_neighbors


class IosXrCompiler(IosBaseCompiler):

    def compile(self, node):
        super(IosXrCompiler, self).compile(node)
        self.mpls_te(node)
        self.mpls_oam(node)

    def mpls_te(self, node):
        super(IosXrCompiler, self).mpls_te(node)

        g_mpls_te = self.anm['mpls_te']
        if node not in g_mpls_te:
            return   # no mpls te configured

        rsvp_interfaces = []
        mpls_te_interfaces = []
        mpls_te_node = g_mpls_te.node(node)

        for interface in mpls_te_node.physical_interfaces():
            nidb_interface = self.nidb.interface(interface)
            stanza = {'id': nidb_interface.id,
                      'bandwidth_percent': 100}
            rsvp_interfaces.append(stanza)

            mpls_te_interfaces.append(nidb_interface.id)

        node.add_scope("rsvp")
        node.rsvp['interfaces'] = rsvp_interfaces
        node.mpls['te_interfaces'] = mpls_te_interfaces

    def rip(self, node):
        super(IosXrCompiler, self).rip(node)

        g_rip = self.anm['rip']
        ipv4_interfaces = []

        for interface in node.physical_interfaces():
            if interface.exclude_igp:
                continue  # discontinue configuring IGP for this interface

            rip_int = g_rip.interface(interface)
            if rip_int and rip_int.is_bound:
                data = {'id': interface.id, 'passive': False}
                if node.rip.get('use_ipv4'):
                    ipv4_interfaces.append(data)

        data = {'id': node.loopback_zero.id, 'passive': True}
        if node.rip.get('use_ipv4'):
            ipv4_interfaces.append(data)

        node.rip['ipv4_interfaces'] = ipv4_interfaces

    def ospf(self, node):
        super(IosXrCompiler, self).ospf(node)

    def eigrp(self, node):
        super(IosXrCompiler, self).eigrp(node)

        g_eigrp = self.anm['eigrp']
        ipv4_interfaces = []
        ipv6_interfaces = []

        for interface in node.physical_interfaces():
            if interface.exclude_igp:
                continue  # don't configure IGP for this interface

            eigrp_int = g_eigrp.interface(interface)
            if eigrp_int and eigrp_int.is_bound:
                # TODO: for here and below use stanza directly
                data = {'id': interface.id, 'passive': False}
                if node.eigrp.get('use_ipv4'):
                    ipv4_interfaces.append(data)
                if node.eigrp.get('use_ipv6'):
                    ipv6_interfaces.append(data)

        data = {'id': node.loopback_zero.id, 'passive': True}
        if node.eigrp.get('use_ipv4'):
            ipv4_interfaces.append(data)
        if node.eigrp.get('use_ipv6'):
            ipv6_interfaces.append(data)

        node.eigrp['ipv4_interfaces'] = ipv4_interfaces
        node.eigrp['ipv6_interfaces'] = ipv6_interfaces

    def isis(self, node):
        super(IosXrCompiler, self).isis(node)
        node.isis['isis_links'] = []

        for interface in node.physical_interfaces():
            if interface.exclude_igp:
                continue  # don't configure IGP for this interface

            # print interface.isis.dump()
            # copy across attributes from the IosBaseCompiler setting step

            isis_int = self.anm['isis'].interface(interface)
            if isis_int and isis_int.is_bound:
                data = {'id': interface.id, 'metric': isis_int.get('metric'),
                        'multipoint': isis_int.get('multipoint')}
                if interface.isis.hello_padding_disable is not None:
                    data['hello_padding_disable'] = \
                        interface.isis.hello_padding_disable
                if interface.isis.mtu is not None:
                    data['mtu'] = interface.isis.hello_padding_disable

                node.isis['isis_links'].append(data)


class NxOsCompiler(IosBaseCompiler):

    def compile(self, node):
        super(NxOsCompiler, self).compile(node)
        self.mpls_te(node)
        self.mpls_oam(node)
        self.mpls_ldp(node)

        node.allocate_interfaces = ["Ethernet2/1-48", "Ethernet3/1-48"]

    def mpls_te(self, node):
        g_mpls_te = self.anm['mpls_te']
        if node not in g_mpls_te:
            return   # no mpls te configured

        if node.supported_features.mpls_te is False:
            node.log.warning("Feature MPLS TE is not supported for %s on the %s platform" % (
                node.device_subtype, node.platform))

    def mpls_oam(self, node):
        g_mpls_oam = self.anm['mpls_oam']
        if node not in g_mpls_oam:
            return   # no mpls oam configured

        if node.supported_features.get('mpls_oam') is False:
            node.log.warning("Feature MPLS OAM is not supported for %s the on %s platform" % (
                node.device_subtype, node.platform))

    def mpls_ldp(self, node):
        g_mpls_ldp = self.anm['mpls_ldp']
        mpls_ldp_node = g_mpls_ldp.node(node)
        node.add_scope("mpls")
        if mpls_ldp_node and mpls_ldp_node.get('role') in ('P', 'PE'):

            # Add PE -> P, PE -> PE interfaces to MPLS LDP

            node.mpls['ldp_interfaces'] = []
            for interface in node.physical_interfaces():
                mpls_ldp_int = mpls_ldp_node.interface(interface)
                if mpls_ldp_int.is_bound:
                    node.mpls['ldp_interfaces'].append(interface.id)
                    interface.use_mpls = True

        # TODO: check if this block is repeated (redundant) logic of above
        if mpls_ldp_node and mpls_ldp_node.get('role') is 'P':
            node.mpls['ldp_interfaces'] = []
            for interface in node.physical_interfaces():
                node.mpls['ldp_interfaces'].append(interface.id)

        # TODO: refactor this logic
        if mpls_ldp_node:
            # P, PE, CE
            node.mpls['enabled'] = True
            node.mpls['router_id'] = node.loopback_zero.id

    def vrf(self, node):
        g_vrf = self.anm['vrf']
        if node not in g_vrf:
            return   # no mpls oam configured
        if node.supported_features.vrf is False:
            node.log.warning("Feature VRF is not supported for %s on the %s platform" % (
                node.device_subtype, node.platform))

    def interfaces(self, node):

        # need to aggregate areas

        super(NxOsCompiler, self).interfaces(node)
        for interface in node.physical_interfaces():
            interface.full_duplex = True

    def rip(self, node):
        super(NxOsCompiler, self).rip(node)
        loopback_zero = node.loopback_zero
        loopback_zero.rip = {'use_ipv4': node.ip.get('use_ipv4'),
                             'process_id': node.rip.get('process_id')}

    def ospf(self, node):
        super(NxOsCompiler, self).ospf(node)
        loopback_zero = node.loopback_zero
        g_ospf = self.anm['ospf']
        ospf_node = g_ospf.node(node)
        loopback_zero.ospf = {
            'cost': ospf_node.get('cost'),
            'area': ospf_node.get('area'),
            'process_id': node.ospf.get('process_id'),
            'use_ipv4': node.ip.get('use_ipv4'),
            'use_ipv6': node.ip.get('use_ipv6'),
        }

        # TODO: add wrapper for this

    def eigrp(self, node):

        # TODO: do we want to specify the name or hard-code (as currently)?

        super(NxOsCompiler, self).eigrp(node)
        loopback_zero = node.loopback_zero
        loopback_zero.eigrp = {'use_ipv4': node.ip.get('use_ipv4'),
                               'use_ipv6': node.ip.get('use_ipv6')}
