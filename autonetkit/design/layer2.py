import autonetkit.ank as ank_utils
import autonetkit.log as log


class Layer2Builder(object):
    def __init__(self, anm):
        self.anm = anm

    def build_layer2(self):
        self.build_layer2_base()
        self.build_vlans()
        self.build_layer2_conn()

        self.check_layer2()
        self.build_layer2_broadcast()

    def build_layer2_base(self):
        anm = self.anm
        g_l2 = anm.add_overlay('layer2')
        g_l1 = anm['layer1']

        g_l2.copy_nodes_from(g_l1)
        g_l2.copy_edges_from(g_l1.edges())
        # Don't aggregate managed switches
        for node in g_l2:
            if node['layer1'].get('collision_domain') == True:
                node.set('broadcast_domain', True)
                node.set('device_type', 'broadcast_domain')


    def build_layer2_conn(self):
        anm = self.anm
        g_l2 = anm['layer2']
        g_l2_conn = anm.add_overlay('layer2_conn')
        g_l2_conn.copy_nodes_from(g_l2)
        ank_utils.copy_node_attr_from(g_l2, g_l2_conn, "broadcast_domain")
        g_l2_conn.copy_edges_from(g_l2.edges())

        broadcast_domains = g_l2_conn.nodes(broadcast_domain=True)
        exploded_edges = ank_utils.explode_nodes(g_l2_conn, broadcast_domains)

        # explode each seperately?
        for edge in exploded_edges:
            edge.set('multipoint', True)
            edge.src_int.set('multipoint', True)
            edge.dst_int.set('multipoint', True)


    def check_layer2(self):
        """Sanity checks on topology"""
        anm = self.anm
        from collections import defaultdict
        g_l2 = anm['layer2']

        # check for igp and ebgp on same switch
        for switch in sorted(g_l2.switches()):
            neigh_asns = defaultdict(int)
            for neigh in switch.neighbors():
                if neigh.get('asn') is None:
                    continue  # don't add if not set
                neigh_asns[neigh.get('asn')] += 1

            # IGP if two or more neighbors share the same ASN
            is_igp = any(asns > 1 for asns in neigh_asns.values())
            # eBGP if more than one unique neigh ASN
            is_ebgp = len(neigh_asns.keys()) > 1
            if is_igp and is_ebgp:
                log.warning("Switch %s contains both IGP and eBGP neighbors",
                            switch)

        # check for multiple links from nodes to switch
        for switch in sorted(g_l2.switches()):
            for neighbor in sorted(switch.neighbors()):
                edges = g_l2.edges(switch, neighbor)
                if len(edges) > 1:
                    # more than one edge between the (src, dst) pair -> parallel
                    log.warning("There are multiple parallel edges (%s) between %s and device %s. "
                        "This may lead to unexpected protocol behavior.",
                                len(edges), switch, neighbor)


    def build_layer2_broadcast(self):
        anm = self.anm
        g_l2 = anm['layer2']
        g_phy = anm['phy']
        g_graphics = anm['graphics']
        g_l2_bc = anm.add_overlay('layer2_bc')
        g_l2_bc.copy_nodes_from(g_l2.l3devices())
        g_l2_bc.copy_nodes_from(g_l2.switches())
        g_l2_bc.copy_edges_from(g_l2.edges())

        # remove external connectors

        edges_to_split = [edge for edge in g_l2_bc.edges()
                          if edge.src.is_l3device() and edge.dst.is_l3device()]
        # TODO: debug the edges to split
        for edge in edges_to_split:
            edge.set('split', True)  # mark as split for use in building nidb

        split_created_nodes = list(ank_utils.split_edges(g_l2_bc, edges_to_split,
                                                   id_prepend='cd_'))

        # TODO: if parallel nodes, offset
        # TODO: remove graphics, assign directly
        if len(g_graphics):
            co_ords_overlay = g_graphics  # source from graphics overlay
        else:
            co_ords_overlay = g_phy  # source from phy overlay

        for node in split_created_nodes:
            node['graphics'].set('x', ank_utils.neigh_average(g_l2_bc, node, 'x',
                                                         co_ords_overlay) + 0.1)

            # temporary fix for gh-90

            node['graphics'].set('y', ank_utils.neigh_average(g_l2_bc, node, 'y',
                                                         co_ords_overlay) + 0.1)

            # temporary fix for gh-90

            asn = ank_utils.neigh_most_frequent(
                g_l2_bc, node, 'asn', g_phy)  # arbitrary choice
            node['graphics'].set('asn', asn)
            node.set('asn', asn)  # need to use asn in IP overlay for aggregating subnets

        # also allocate an ASN for virtual switches
        vswitches = [n for n in g_l2_bc.nodes()
                     if n['layer2'].get('device_type') == "switch"
                     and n['layer2'].get('device_subtype') == "virtual"]
        for node in vswitches:
            # TODO: refactor neigh_most_frequent to allow fallthrough attributes
            asns = [n['layer2'].get('asn') for n in node.neighbors()]
            asns = [x for x in asns if x is not None]
            asn = ank_utils.most_frequent(asns)
            node.set('asn', asn)  # need to use asn in IP overlay for aggregating subnets
            # also mark as broadcast domain

        from collections import defaultdict
        coincident_nodes = defaultdict(list)
        for node in split_created_nodes:
            coincident_nodes[(node['graphics'].get('x'), node['graphics'].get('y'))].append(node)

        coincident_nodes = {k: v for k, v in coincident_nodes.items()
                            if len(v) > 1}  # trim out single node co-ordinates
        import math
        for _, val in coincident_nodes.items():
            for index, item in enumerate(val):
                index += 1
                x_offset = 25 * math.floor(index / 2) * math.pow(-1, index)
                y_offset = -1 * 25 * math.floor(index / 2) * math.pow(-1, index)
                item['graphics'].set('x', item['graphics'].get('x') + x_offset)
                item['graphics'].set('y', item['graphics'].get('y') + y_offset)

        switch_nodes = g_l2_bc.switches()  # regenerate due to aggregated
        g_l2_bc.update(switch_nodes, broadcast_domain=True)

        # switches are part of collision domain
        g_l2_bc.update(split_created_nodes, broadcast_domain=True)

        # Assign collision domain to a host if all neighbours from same host

        for node in split_created_nodes:
            if ank_utils.neigh_equal(g_l2_bc, node, 'host', g_phy):
                node.set('host', ank_utils.neigh_attr(g_l2_bc, node, 'host',
                                                 g_phy).next())  # first attribute

        # set collision domain IPs
        # TODO; work out why this throws a json exception
        for node in g_l2_bc.nodes('broadcast_domain'):
            graphics_node = g_graphics.node(node)
            if node.is_switch():
                # TODO: check not virtual
                node['phy'].set('broadcast_domain', True)
            if not node.is_switch():
                # use node sorting, as accommodates for numeric/string names
                graphics_node.set('device_type', 'broadcast_domain')
                neighbors = sorted(neigh for neigh in node.neighbors())
                label = '_'.join(neigh.label for neigh in neighbors)
                cd_label = 'cd_%s' % label  # switches keep their names
                node.set('label', cd_label)
                graphics_node.set('label', cd_label)
                node.set('device_type', 'broadcast_domain')
                node.set('label', node.id)
                graphics_node.set('label', node.id)

        for node in vswitches:
            node.set('broadcast_domain', True)


    def set_default_vlans(self, default_vlan=2):
        anm = self.anm
        #TODO: read default vlan from global input config (eg from .virl)
        # TODO: rename to "mark_defaults_vlan" or similar
        # checks all links to managed switches have vlans
        g_vtp = anm['vtp']
        managed_switches = [n for n in g_vtp.switches()
                            if n.get('device_subtype') == "managed"]

        no_vlan_ints = []
        for switch in managed_switches:
            for interface in switch.interfaces():
                if len(interface.neighbors()) > 1:
                    log.warning("Interface %s is connected to multiple endpoints. Please check resulting configuration is as intended",interface)
            for edge in switch.edges():
                neigh_int = edge.dst_int
                local_int = edge.src_int

                # first look at local interfaces
                vlan = local_int['input'].get('vlan')
                neigh_vlan = neigh_int['input'].get('vlan')
                if vlan and neigh_vlan and vlan != neigh_vlan:
                    log.warning("VLAN mismatch: VLAN %s on %s does not match VLAN %s on remote interface %s. Using local VLAN %s", vlan, interface, neigh_vlan, neigh_int, vlan)
                if vlan is not None:
                    if vlan.isdigit():
                        # use directly for next stage
                        pass
                    elif vlan == "1-4095":
                        local_int.set('trunk', True)
                        continue
                    else:
                        # not integer, set as trunk
                        local_int.set('trunk', True)
                        local_int.set('allowed_vlans', vlan)
                        continue

                # TODO: store vlans on node to add to vlan a, b, c stanza

                #TODO: use the vlans on the node to then


                if neigh_int.node in managed_switches:
                    local_int.set('trunk', True)
                    continue

                if vlan is None:
                    # no locally specified VLAN, try from neighbor
                    if neigh_vlan is None:
                        vlan = default_vlan
                        no_vlan_ints.append(neigh_int)
                    else:
                        if neigh_vlan.isdigit():
                            # use directly for next stage
                            vlan = neigh_vlan
                        elif neigh_vlan == "1-4095":
                            local_int.set('trunk', True)
                            continue
                        else:
                            # not integer, set as trunk
                            local_int.set('trunk', True)
                            local_int.set('allowed_vlans', neigh_vlan)
                            continue

                try:
                    vlan = int(vlan)
                except TypeError:
                    log.warning("Non-integer vlan %s for %s. Using default %s",
                        vlan, neigh_int, default_vlan)
                    vlan = default_vlan

                neigh_int.set('vlan', vlan)
                local_int.set('vlan', vlan)

            for interface in switch:
                if interface.get('vlan') and interface.get('trunk'):
                    log.warning("Interface %s set to trunk and vlan", interface)

        # map to layer 2 interfaces
        if len(no_vlan_ints):
            log.info("Setting default VLAN %s to interfaces connected to a managed "
               "switch with no VLAN: %s", default_vlan, no_vlan_ints)

        # and map the vlans the node is in onto the node
        for switch in managed_switches:
            switch.set('vlans', [])
            for interface in switch:
                if interface.get('vlan'):
                    switch.get('vlans').append(interface.get('vlan'))

            switch.set('vlans', list(set(switch.get('vlans')))) # unique-ify


    def build_vlans(self):
        anm = self.anm
        import itertools
        from collections import defaultdict
        g_l2 = anm['layer2']
        g_l1_conn = anm['layer1_conn']

        g_vtp = anm.add_overlay('vtp')
        managed_switches = [n for n in g_l2.switches()
                            if n.get('device_subtype') == "managed"]

        g_vtp.copy_nodes_from(g_l1_conn)
        g_vtp.copy_edges_from(g_l1_conn.edges())

        # remove anything not a managed_switch or connected to a managed_switch
        keep = set()
        keep.update(managed_switches)
        for switch in managed_switches:
            keep.update(switch['vtp'].neighbors())

        remove = set(g_vtp) - keep
        g_vtp.remove_nodes_from(remove)

        edges_to_remove = [e for e in g_vtp.edges()
                           if not(e.src in managed_switches or e.dst in managed_switches)]
        g_vtp.remove_edges_from(edges_to_remove)

        self.set_default_vlans()

        # copy across vlans from input graph
        vswitch_id_counter = itertools.count(1)

        # TODO: aggregate managed switches

        bcs_to_trim = set()

        subs = ank_utils.connected_subgraphs(g_vtp, managed_switches)
        for sub_index, sub in enumerate(subs):
            # identify the VLANs on these switches

            vlans = defaultdict(list)
            sub_neigh_ints = set()
            for switch in sub:
                l2_switch = switch['layer2']
                bcs_to_trim.update(l2_switch.neighbors())
                neigh_ints = {iface for iface in switch.neighbor_interfaces()
                              if iface.node.is_l3device()
                              and iface.node not in sub}

                sub_neigh_ints.update(neigh_ints)

                for interface in switch:
                    interface.set('vlan_domain', sub_index)

            for interface in sub_neigh_ints:
                # store keyed by vlan id
                vlan = interface['vtp'].get('vlan')
                vlans[vlan].append(interface)
                interface['vtp'].set('vlan_domain', sub_index)

            log.debug("Vlans for sub %s are %s", sub, vlans)

            # and record on the node for creating the bridges
            for switch in sub:
                switch.set('domain_vlans', vlans.keys())

            # create a virtual switch for each
            # TODO: naming: if this is the only pair then name after these, else
            # use the switch names too
            vswitches = []  # store to connect trunks

            vswitch_tp_lookup = {}

            for vlan, interfaces in vlans.items():
                # create a virtual switch
                vswitch_id = "vswitch%s" % vswitch_id_counter.next()
                vswitch = g_l2.create_node(vswitch_id)
                vlan_tp = vswitch.add_interface(category="vlan_termination_point")
                vswitch_tp_lookup[vswitch] = vlan_tp
                # TODO: check of switch or just broadcast_domain for higher layer
                # purposes
                vswitch.set('device_type', 'switch')
                vswitch.set('device_subtype', "virtual")
                vswitches.append(vswitch)
                # TODO: layout based on midpoint of previous?
                # or if same number as real switches, use their co-ordinates?
                # and then check for coincident?
                vswitch.set('x', sum(
                    i.node['phy'].get('x') for i in interfaces) / len(interfaces) + 50)
                vswitch.set('y', sum(
                    i.node['phy'].get('y') for i in interfaces) / len(interfaces) + 50)
                vswitch.set('vlan', vlan)

                vswitch['layer2'].set('broadcast_domain', True)
                vswitch['layer2'].set('vlan', vlan)

                # and connect from vswitch to the interfaces
                edges_to_add = [(vlan_tp, iface) for iface in interfaces]
                g_l2.create_edges_from(edges_to_add)

            # remove the physical switches
            g_l2.remove_nodes_from(bcs_to_trim)
            g_l2.remove_nodes_from(sub)
            # TODO: also remove any broadcast domains no longer connected


            # Note: we don't store the interface names as ciuld clobber
            # eg came from two physical switches, each on gige0
            # if need, work backwards from the router iface and its connectivity

            # and add the trunks
            # TODO: these need annotations! ???
            # create trunks
            for sw1 in vswitches:
                for sw2 in vswitches:
                    if sw1 == sw2:
                        continue

                    edge = (vswitch_tp_lookup[sw1], vswitch_tp_lookup[sw2])
                    edges_to_add.append(edge)

            # TODO: ensure only once
            # TODO: filter so only one direction
            new_edges = g_vtp.create_edges_from(edges_to_add)
            for e in new_edges:
                e.set('trunk', True)

        for node in g_vtp:
            node.set('vlans_by_domain', defaultdict(list))
            for interface in node:
                domain = interface.get('vlan_domain')
                if interface.get('vlan') and interface.get('vlan') not in node.get('vlans_by_domain')[domain]:
                    node.get('vlans_by_domain')[domain].append(interface.get('vlan'))
