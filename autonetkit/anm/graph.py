import autonetkit.log as log
from autonetkit.ank_utils import unwrap_edges, unwrap_nodes, unwrap_edge
from autonetkit.anm.base import OverlayBase
from autonetkit.anm.edge import NmEdge
from autonetkit.anm.interface import NmPort
from autonetkit.anm.node import NmNode
import autonetkit


class NmGraph(OverlayBase):

    """API to interact with an overlay graph in ANM"""

    @property
    def anm(self):
        """Returns anm for this overlay"""
        return self._anm

    @property
    def _graph(self):
        """Access underlying graph for this NmNode"""

        return self._anm.overlay_nx_graphs[self._overlay_id]

    def _replace_graph(self, graph):
        """"""

        self._anm.overlay_nx_graphs[self._overlay_id] = graph

    # these work similar to their nx counterparts: just need to strip the
    # node_id

    def _record_overlay_dependencies(self, node):
        return
        # TODO: add this logic to anm so can call when instantiating overlays too
        # TODO: make this able to be disabled for performance
        g_deps = self.anm['_dependencies']
        if self._overlay_id not in g_deps:
            g_deps.create_node(self._overlay_id)
        overlay_id = node.overlay_id
        if overlay_id not in g_deps:
            g_deps.create_node(overlay_id)

        if g_deps.number_of_edges(self._overlay_id, overlay_id) == 0:
            edge = (overlay_id, self._overlay_id)
            g_deps.add_edges_from([edge])

    def create_nodes_from(self, nbunch, **kwargs):
        nbunch = [n for n in nbunch if n not in self._graph]

        for n in nbunch:
            self.create_node(n, **kwargs)

    def copy_nodes_from(self, nbunch, **kwargs):
        nbunch = [n for n in nbunch if n not in self._graph]

        for n in nbunch:
            self.copy_node(n, **kwargs)

    def _copy_interfaces(self, node):
        """Copies ports from one overlay to another"""

        if self._overlay_id == "phy":
            # note: this will auto copy data from input if present - by default
            # TODO: provide an option to add_nodes to skip this
            # or would it be better to just provide a function in ank_utils to
            # wipe interfaces in the rare case it's needed?
            input_graph = self._anm.overlay_nx_graphs['input']
            if node not in input_graph:
                log.debug("Not copying interfaces for %s: ",
                          "not in input graph %s" % node)
                self._graph.node[node]['_ports'] = {
                    0: {'description': 'loopback', 'category': 'loopback'}}
                return

            try:
                input_interfaces = input_graph.node[node]['_ports']
            except KeyError:
                # Node not in input
                # Just do base initialisation of loopback zero
                self._graph.node[node]['_ports'] = {
                    0: {'description': 'loopback', 'category': 'loopback'}}
            else:
                interface_data = {'description': None,
                                  'category': 'physical'}
                # need to do dict() to copy, otherwise all point to same memory
                # location -> clobber
                # TODO: update this to also get subinterfaces?
                # TODO: should description and category auto fall through?
                data = dict((key, dict(interface_data)) for key in
                            input_interfaces)
                ports = {}
                for key, vals in input_interfaces.items():
                    port_data = {}
                    ports[key] = dict(vals)

                # force 0 to be loopback
                # TODO: could warn if already set
                ports[0] = {
                    'description': 'loopback', 'category': 'loopback'}
                self._graph.node[node]['_ports'] = ports
            return

        if self._overlay_id == "graphics":
            # TODO: remove once graphics removed
            return

        phy_graph = self._anm.overlay_nx_graphs['phy']
        try:
            phy_interfaces = phy_graph.node[node]['_ports']
        except KeyError:
            # Node not in phy (eg broadcast domain)
            # Just do base initialisation of loopback zero
            self._graph.node[node]['_ports'] = {
                0: {'description': 'loopback', 'category': 'loopback'}}
        else:
            interface_data = {'description': None,
                              'category': 'physical'}
            # need to do dict() to copy, otherwise all point to same memory
            # location -> clobber
            # TODO: update this to also get subinterfaces?
            # TODO: should description and category auto fall through?
            data = dict((key, dict(interface_data)) for key in
                        phy_interfaces)
            self._graph.node[node]['_ports'] = data

    def create_node(self, node, **kwargs):
        return self._add_node(node, **kwargs)

    def copy_node(self, node, **kwargs):
        return self._add_node(node.node_id, **kwargs)

    def _add_node(self, node, **kwargs):
        # TODO: label workaround
        data = {'label': node}
        self._graph.add_nodes_from([(node, data)], **kwargs)
        self._copy_interfaces(node)
        return NmNode(self.anm, self._overlay_id, node)

    def allocate_input_interfaces(self):
        """allocates edges to interfaces"""
        # TODO: move this to ank utils? or extra step in the anm?
        if self._overlay_id != "input":
            log.debug("Tried to allocate interfaces to %s" % overlay_id)
            return

        if all(len(node['input'].raw_interfaces) > 0 for node in self) \
            and all(len(edge['input'].raw_interfaces) > 0 for edge in
                    self.edges()):
            log.debug("Input interfaces allocated")
            return  # interfaces allocated
        elif self.data.interfaces_allocated == True:
            # explicitly flagged as allocated
            return
        else:
            log.info('Automatically assigning input interfaces')

        # Initialise loopback zero on node
        for node in self:
            node.set('raw_interfaces', {0:
                                   {'description': 'loopback', 'category': 'loopback'}})

        ebunch = sorted(self.edges())
        for edge in ebunch:
            src = edge.src
            dst = edge.dst
            src_int_id = src._add_interface('%s to %s' % (src.label,
                                                          dst.label))
            dst_int_id = dst._add_interface('%s to %s' % (dst.label,
                                                          src.label))
            edge.raw_interfaces = {
                src.id: src_int_id,
                dst.id: dst_int_id}

    def number_of_edges(self, node_a, node_b):
        return self._graph.number_of_edges(node_a, node_b)

    def __delitem__(self, key):
        """Alias for remove_node. Allows
        del overlay[node]
        """
        # TODO: needs to support node types
        self.remove_node(key)

    def remove_nodes_from(self, nbunch):
        """Removes set of nodes from nbunch. Node in nbunch has to be
        instance of NmNode class.
        """
        for n in nbunch:
            self.remove_node(n)

    def remove_node(self, node):
        """Removes a NmNode instance from the overlay"""
        node_id = node.node_id
        if node_id in self:
            self._graph.remove_node(node_id)
        else:
            log.debug('Node %s not present in graph', node_id)

    def create_edge(self, src, dst, **kwargs):
        data = {'_ports': {}}
        src_id = src.node.node_id
        dst_id = dst.node.node_id
        ports = {}
        if src_id in self:
            ports[src_id] = src.interface_id
        if dst in self:
            ports[dst_id] = dst.interface_id
        data['_ports'] = ports
        data.update(**kwargs)

        return self._add_edge(src_id, dst_id, data=data)

    def copy_edge(self, edge, reverse=False, **kwargs):
        ekey = edge.ekey  # explictly set ekey
        src = edge.src.node_id
        dst = edge.dst.node_id

        ports = {k: v for k, v in edge.raw_interfaces.items()
                 if k in self._graph}  # only if exists in this overlay
        # TODO: debug log if skipping a binding?
        data = {'_ports': ports}
        data.update(**kwargs)
        if reverse:
            return self._add_edge(dst, src, data, ekey)
        return self._add_edge(src, dst, data, ekey)

    def _add_edge(self, src, dst, data, ekey=None):
        if not(src in self and dst in self):
            self.log.debug("Not adding edge %s/%s, src/dst not in overlay",
                           str(src), str(dst))
            return
        if self.is_multigraph() and ekey is None:
            # now have the keys mapping
            try:
                keys = self._graph.adj[src][dst].keys()
            except KeyError, e:
                keys = []
            ekey=len(keys)
            while ekey in keys:
                ekey+=1

        if self.is_multigraph():
            self._graph.add_edges_from([(src, dst, ekey, dict(data))])
            return NmEdge(self.anm, self._overlay_id, src, dst, ekey)

        self._graph.add_edges_from([(src, dst, dict(data))])
        return NmEdge(self.anm, self._overlay_id, src, dst)

    def remove_edge(self, edge):
        """Removes NmEdge instance from overlay"""
        nx_edge = unwrap_edge(edge)
        self._graph.remove_edge(*nx_edge)

    def remove_edges_from(self, ebunch):
        """Removes set of edges from ebunch"""
        for edge in ebunch:
            self.remove_edge(edge)

    def create_edges_from(self, ebunch, bidirectional=False, **kwargs):
        edges = []
        for in_edge in ebunch:
            new_edge = self.create_edge(in_edge[0], in_edge[1], **kwargs)
            if new_edge:
                edges.append(new_edge)
            if bidirectional:
                new_edge = self.create_edge(in_edge[1], in_edge[0], **kwargs)
                if new_edge:
                    edges.append(new_edge)
        return edges

    def copy_edges_from(self, ebunch, bidirectional=False, **kwargs):
        edges = []
        for in_edge in ebunch:
            new_edge = self.copy_edge(in_edge, **kwargs)
            if new_edge:
                edges.append(new_edge)
            if bidirectional:
                new_edge = self.copy_edge(in_edge, reverse=True, **kwargs)
                if new_edge:
                    edges.append(new_edge)
        return edges

    def update(self, nbunch=None, **kwargs):
        """Sets property defined in kwargs to all nodes in nbunch"""

        if nbunch is None:
            nbunch = self.nodes()

        if nbunch in self:
            nbunch = [nbunch]  # single node in the list for iteration

        # if the node is in the underlying networkx graph, then map to an
        # overlay node
        nbunch = [self.node(n) if n in self._graph else n for n in nbunch]
        for node in nbunch:
            for (key, value) in kwargs.items():
                node.set(key, value)

    def subgraph(self, nbunch, name=None):
        """"""

        nbunch = (n.node_id for n in nbunch)  # only store the id in overlay
        from autonetkit.anm.subgraph import OverlaySubgraph
        return OverlaySubgraph(self._anm, self._overlay_id,
                               self._graph.subgraph(nbunch), name)
