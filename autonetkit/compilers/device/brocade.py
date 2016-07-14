#!/usr/bin/python
# -*- coding: utf-8 -*-
from collections import defaultdict

import autonetkit.log as log
import netaddr
from autonetkit.ank import sn_preflen_to_network
from autonetkit.compiler import sort_sessions
from autonetkit.compilers.device.router_base import RouterCompiler
from autonetkit.nidb import ConfigStanza


class BrocadeBaseCompiler(RouterCompiler):

    """Base IOS compiler"""

    lo_interface_prefix = 'Loopback'
    lo_interface = '%s%s' % (lo_interface_prefix, 0)

    def ibgp_session_data(self, session, ip_version):
        """Wraps RouterCompiler ibgp_session_data
        adds vpnv4 = True if ip_version == 4 and session is in g_ibgp_vpn_v4"""

        data = super(BrocadeBaseCompiler, self).ibgp_session_data(session,
                                                              ip_version)
        if ip_version == 4:
            g_ibgp_vpn_v4 = self.anm['ibgp_vpn_v4']
            if g_ibgp_vpn_v4.has_edge(session):
                data['use_vpnv4'] = True
        return data

    def compile(self, node):
        self.vrf_igp_interfaces(node)
        phy_node = self.anm['phy'].node(node)

        node.use_fdp = phy_node.use_fdp

        if node in self.anm['snmp']:
            node.add_stanza("snmp")

        if node in self.anm['mct']:
            node.add_stanza("mct")

        if node in self.anm['radius']:
            node.add_stanza("radius")

        if node in self.anm['ntp']:
            node.add_stanza("ntp")

        if node in self.anm['lag']:
            node.add_stanza("lag")

        if node in self.anm['ospf']:
            node.add_stanza("ospf")
            node.ospf.use_ipv4 = phy_node.use_ipv4
            node.ospf.use_ipv6 = phy_node.use_ipv6

        if node in self.anm['eigrp']:
            node.add_stanza("eigrp")
            node.eigrp.use_ipv4 = phy_node.use_ipv4
            node.eigrp.use_ipv6 = phy_node.use_ipv6

        if node in self.anm['isis']:
            node.add_stanza("isis")
            node.isis.use_ipv4 = phy_node.use_ipv4
            node.isis.use_ipv6 = phy_node.use_ipv6

        if node in self.anm['rip']:
            node.add_stanza("rip")
            node.rip.use_ipv4 = phy_node.use_ipv4
            node.rip.use_ipv6 = phy_node.use_ipv6

        super(BrocadeBaseCompiler, self).compile(node)
        if node in self.anm['isis']:
            self.isis(node)

        node.label = self.anm['phy'].node(node).label
        self.vrf(node)

    def interfaces(self, node):
        phy_loopback_zero = self.anm['phy'
                                     ].interface(node.loopback_zero)
        if node.ip.use_ipv4:
            ipv4_loopback_subnet = netaddr.IPNetwork('0.0.0.0/32')
            ipv4_loopback_zero = phy_loopback_zero['ipv4']
            ipv4_address = ipv4_loopback_zero.ip_address
            node.loopback_zero.use_ipv4 = True
            node.loopback_zero.ipv4_address = ipv4_address
            node.loopback_zero.ipv4_subnet = ipv4_loopback_subnet
            node.loopback_zero.ipv4_cidr = \
                sn_preflen_to_network(ipv4_address,
                                      ipv4_loopback_subnet.prefixlen)

        if node.ip.use_ipv6:
            # TODO: clean this up so can set on router_base: call cidr not
            # address and update templates
            node.loopback_zero.use_ipv6 = True
            ipv6_loopback_zero = phy_loopback_zero['ipv6']
            node.loopback_zero.ipv6_address = \
                sn_preflen_to_network(ipv6_loopback_zero.ip_address,
                                      128)

        super(BrocadeBaseCompiler, self).interfaces(node)

        for interface in node.physical_interfaces():
            interface.use_fdp = node.use_fdp  # use node value

        for interface in node.interfaces:
            interface.sub_ints = []  # temporary until full subinterfaces

    def mpls_oam(self, node):
        g_mpls_oam = self.anm['mpls_oam']
        node.add_stanza("mpls")
        node.mpls.oam = False

        if node not in g_mpls_oam:
            return   # no mpls oam configured

        # Node is present in mpls OAM
        node.mpls.oam = True

    def mpls_te(self, node):
        g_mpls_te = self.anm['mpls_te']

        if node not in g_mpls_te:
            return   # no mpls te configured

        node.mpls_te = True

        if node.isis:
            node.isis.ipv4_mpls_te = True
            node.isis.mpls_te_router_id = self.lo_interface

        if node.ospf:
            node.ospf.ipv4_mpls_te = True
            node.ospf.mpls_te_router_id = self.lo_interface

    def nailed_up_routes(self, node):
        log.debug('Configuring nailed up routes')
        phy_node = self.anm['phy'].node(node)

        if node.is_ebgp_v4 and node.ip.use_ipv4:
            infra_blocks = self.anm['ipv4'].data['infra_blocks'
                                                 ].get(phy_node.asn) or []
            for infra_route in infra_blocks:
                stanza = ConfigStanza(
                    prefix=str(infra_route.network),
                    netmask=str(infra_route.netmask),
                    nexthop="Null0",
                    metric=254,
                )
                node.ipv4_static_routes.append(stanza)

        if node.is_ebgp_v6 and node.ip.use_ipv6:
            infra_blocks = self.anm['ipv6'].data['infra_blocks'
                                                 ].get(phy_node.asn) or []
            # TODO: setup schema with defaults
            for infra_route in infra_blocks:
                stanza = ConfigStanza(
                    prefix=str(infra_route),
                    nexthop="Null0",
                    metric=254,
                )
                node.ipv6_static_routes.append(stanza)

    def bgp(self, node):
        node.add_stanza("bgp")
        node.bgp.lo_interface = self.lo_interface
        super(BrocadeBaseCompiler, self).bgp(node)
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

        node.bgp.ipv4_advertise_subnets = []
        node.bgp.ipv6_advertise_subnets = []

        # Advertise loopbacks into BGP

        if node.ip.use_ipv4:
            node.bgp.ipv4_advertise_subnets = \
                [node.loopback_zero.ipv4_cidr]
        if node.ip.use_ipv6:
            node.bgp.ipv6_advertise_subnets = \
                [node.loopback_zero.ipv6_address]

        # Advertise infrastructure into eBGP

        if node.ip.use_ipv4 and node.is_ebgp_v4:
            infra_blocks = self.anm['ipv4'].data['infra_blocks'
                                                 ].get(asn) or []
            for infra_route in infra_blocks:
                node.bgp.ipv4_advertise_subnets.append(infra_route)

        if node.ip.use_ipv6 and node.is_ebgp_v6:
            infra_blocks = self.anm['ipv6'].data['infra_blocks'
                                                 ].get(asn) or []
            for infra_route in infra_blocks:
                node.bgp.ipv6_advertise_subnets.append(infra_route)

        self.nailed_up_routes(node)

        # vrf
        # TODO: this should be inside vrf section?

        node.bgp.vrfs = []

        vrf_node = self.anm['vrf'].node(node)
        if vrf_node and vrf_node.vrf_role is 'PE':

            # iBGP sessions for this VRF

            vrf_ibgp_neighbors = defaultdict(list)

            g_ibgp_v4 = self.anm['ibgp_v4']
            for session in sort_sessions(g_ibgp_v4.edges(vrf_node)):
                if session.exclude and session.vrf:
                    data = self.ibgp_session_data(session, ip_version=4)
                    stanza = ConfigStanza(data)
                    vrf_ibgp_neighbors[session.vrf].append(stanza)

            g_ibgp_v6 = self.anm['ibgp_v6']
            for session in sort_sessions(g_ibgp_v6.edges(vrf_node)):
                if session.exclude and session.vrf:
                    data = self.ibgp_session_data(session, ip_version=6)
                    stanza = ConfigStanza(data)
                    vrf_ibgp_neighbors[session.vrf].append(stanza)

            # eBGP sessions for this VRF

            vrf_ebgp_neighbors = defaultdict(list)

            for session in sort_sessions(g_ebgp_v4.edges(vrf_node)):
                if session.exclude and session.vrf:
                    data = self.ebgp_session_data(session, ip_version=4)
                    stanza = ConfigStanza(data)
                    vrf_ebgp_neighbors[session.vrf].append(stanza)

            for session in sort_sessions(g_ebgp_v6.edges(vrf_node)):
                if session.exclude and session.vrf:
                    data = self.ebgp_session_data(session, ip_version=6)
                    stanza = ConfigStanza(data)
                    vrf_ebgp_neighbors[session.vrf].append(stanza)

            for vrf in vrf_node.node_vrf_names:
                rd_index = vrf_node.rd_indices[vrf]
                rd = '%s:%s' % (node.asn, rd_index)
                stanza = ConfigStanza(
                    vrf=vrf,
                    rd=rd,
                    use_ipv4=node.ip.use_ipv4,
                    use_ipv6=node.ip.use_ipv6,
                    vrf_ebgp_neighbors=vrf_ebgp_neighbors[vrf],
                    vrf_ibgp_neighbors=vrf_ibgp_neighbors[vrf],
                )
                node.bgp.vrfs.append(stanza)

        # Retain route_target if in ibgp_vpn_v4 and RR or HRR (set in design)

        vpnv4_node = self.anm['ibgp_vpn_v4'].node(node)
        if vpnv4_node:
            retain = False
            if vpnv4_node.retain_route_target:
                retain = True
            node.bgp.vpnv4 = ConfigStanza(retain_route_target=retain)

    def vrf_igp_interfaces(self, node):

        # marks physical interfaces to exclude from IGP

        vrf_node = self.anm['vrf'].node(node)
        if vrf_node and vrf_node.vrf_role is 'PE':
            for interface in node.physical_interfaces():
                vrf_int = self.anm['vrf'].interface(interface)
                if vrf_int.vrf_name:
                    interface.exclude_igp = True

    def vrf(self, node):
        g_vrf = self.anm['vrf']
        vrf_node = self.anm['vrf'].node(node)
        node.add_stanza("vrf")
        node.add_stanza("mpls")
        node.vrf.vrfs = []
        if vrf_node and vrf_node.vrf_role is 'PE':

            # TODO: check if mpls ldp already set elsewhere

            for vrf in vrf_node.node_vrf_names:
                route_target = g_vrf.data.route_targets[node.asn][vrf]
                rd_index = vrf_node.rd_indices[vrf]
                rd = '%s:%s' % (node.asn, rd_index)

                stanza = ConfigStanza(
                    vrf=vrf, rd=rd, route_target=route_target)
                node.vrf.vrfs.append(stanza)

            for interface in node.interfaces:
                vrf_int = self.anm['vrf'].interface(interface)
                if vrf_int.vrf_name:
                    # mark interface as being part of vrf
                    interface.vrf = vrf_int.vrf_name
                    if interface.physical:
                        interface.description += ' vrf %s' \
                            % vrf_int.vrf_name

        if vrf_node and vrf_node.vrf_role in ('P', 'PE'):

            # Add PE -> P, PE -> PE interfaces to MPLS LDP

            node.mpls.ldp_interfaces = []
            for interface in node.physical_interfaces():
                mpls_ldp_int = self.anm['mpls_ldp'].interface(interface)
                if mpls_ldp_int.is_bound:
                    node.mpls.ldp_interfaces.append(interface.id)
                    interface.use_mpls = True

        if vrf_node and vrf_node.vrf_role is 'P':
            node.mpls.ldp_interfaces = []
            for interface in node.physical_interfaces():
                node.mpls.ldp_interfaces.append(interface.id)

        vrf_node = self.anm['vrf'].node(node)

        node.vrf.use_ipv4 = node.ip.use_ipv4
        node.vrf.use_ipv6 = node.ip.use_ipv6
        node.vrf.vrfs = sorted(node.vrf.vrfs, key=lambda x: x.vrf)

        if self.anm.has_overlay('mpls_ldp') and node \
                in self.anm['mpls_ldp']:
            node.mpls.enabled = True
            node.mpls.router_id = node.loopback_zero.id

    def rip(self, node):
    #Inheriting from base compiler. Adding in interface stanza.
        super(BrocadeBaseCompiler, self).rip(node)
        for interface in node.physical_interfaces():
            phy_int = self.anm['phy'].interface(interface)

            rip_int = phy_int['rip']
            if rip_int and rip_int.is_bound:
                if interface.exclude_igp:
                    continue

                interface.rip = {
                    'cost': rip_int.cost,
                    'area': rip_int.area,
                    'process_id': node.rip.process_id,
                    'use_ipv4': node.ip.use_ipv4,
                    'use_ipv6': node.ip.use_ipv6,
                }

    def ospf(self, node):
        super(BrocadeBaseCompiler, self).ospf(node)
        for interface in node.physical_interfaces():
            phy_int = self.anm['phy'].interface(interface)

            ospf_int = phy_int['ospf']
            if ospf_int and ospf_int.is_bound:
                if interface.exclude_igp:
                    continue  # don't configure IGP for this interface

                # TODO: use ConfigStanza here
                interface.ospf = {
                    'cost': ospf_int.cost,
                    'area': ospf_int.area,
                    'process_id': node.ospf.process_id,
                    'use_ipv4': node.ip.use_ipv4,
                    'use_ipv6': node.ip.use_ipv6,
                    'multipoint': ospf_int.multipoint,
                }

                # TODO: add wrapper for this

    def eigrp(self, node):
        super(BrocadeBaseCompiler, self).eigrp(node)
        for interface in node.physical_interfaces():
            phy_int = self.anm['phy'].interface(interface)

            eigrp_int = phy_int['eigrp']
            if eigrp_int and eigrp_int.is_bound:
                if interface.exclude_igp:
                    continue  # don't configure IGP for this interface

                interface.eigrp = {
                    'metric': eigrp_int.metric,
                    'area': eigrp_int.area,
                    'name': node.eigrp.name,
                    'use_ipv4': node.ip.use_ipv4,
                    'use_ipv6': node.ip.use_ipv6,
                    'multipoint': eigrp_int.multipoint,
                }

                # TODO: add wrapper for this

    def isis(self, node):
        super(BrocadeBaseCompiler, self).isis(node)
        for interface in node.physical_interfaces():
            isis_int = self.anm['isis'].interface(interface)
            edges = isis_int.edges()
            if not isis_int.is_bound:
                # Could occur for VRFs
                log.debug("No ISIS connections for interface %s" % interface)
                continue

            # TODO: change this to be is_bound and is_multipoint
            if isis_int.multipoint:
                log.warning('Extended NI config support not valid for multipoint ISIS connections on %s'
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
            dst_type = dst['phy'].device_subtype
            '''
            Hardcoding for now. Need to check for brocade device
            '''
            interface.isis.hello_padding_disable = True
            interface.isis.mtu = 1430

            interface.isis_mtu = interface.isis.mtu
            interface.hello_padding_disable = \
                interface.isis.hello_padding_disable



class BrocadeNICompiler(BrocadeBaseCompiler):

    def compile(self, node):
        super(BrocadeNICompiler, self).compile(node)
        self.mpls_te(node)
        self.mpls_oam(node)

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

        if node.supported_features.mpls_oam is False:
            node.log.warning("Feature MPLS OAM is not supported for %s the on %s platform" % (
                node.device_subtype, node.platform))

    def vrf(self, node):
        g_vrf = self.anm['vrf']
        if node not in g_vrf:
            return   # no mpls oam configured
        if node.supported_features.vrf is False:
            node.log.warning("Feature VRF is not supported for %s on the %s platform" % (
                node.device_subtype, node.platform))

    def interfaces(self, node):

        # need to aggregate areas

        super(BrocadeNICompiler, self).interfaces(node)

    def rip(self, node):
        super(BrocadeNICompiler, self).rip(node)
        loopback_zero = node.loopback_zero
        loopback_zero.rip = {'use_ipv4': node.ip.use_ipv4,
                            'process_id': node.rip.process_id}


    def ospf(self, node):
        super(BrocadeNICompiler, self).ospf(node)
        loopback_zero = node.loopback_zero
        g_ospf = self.anm['ospf']
        ospf_node = g_ospf.node(node)
        loopback_zero.ospf = {
            'cost': ospf_node.cost,
            'area': ospf_node.area,
            'process_id': node.ospf.process_id,
            'use_ipv4': node.ip.use_ipv4,
            'use_ipv6': node.ip.use_ipv6,
        }

        # TODO: add wrapper for this

    def eigrp(self, node):

        # TODO: do we want to specify the name or hard-code (as currently)?

        super(BrocadeNICompiler, self).eigrp(node)
        loopback_zero = node.loopback_zero
        loopback_zero.eigrp = {'use_ipv4': node.ip.use_ipv4,
                               'use_ipv6': node.ip.use_ipv6}


