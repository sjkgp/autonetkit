#!/usr/bin/python
# -*- coding: utf-8 -*-

import itertools
import logging

import autonetkit
import autonetkit.log as log
from autonetkit.anm.edge import NmEdge
from autonetkit.anm.graph_data import NmGraphData
from autonetkit.anm.interface import NmPort
from autonetkit.anm.node import NmNode
from autonetkit.exception import OverlayNotFound
# TODO: check if this is still a performance hit
from autonetkit.log import CustomAdapter

from autonetkit.anm.ank_element import AnkElement

class OverlayBase(AnkElement):

    '''Base class for overlays - overlay graphs, subgraphs, projections, etc'''

    def __init__(self, anm, overlay_id):
        """"""

        if overlay_id not in anm.overlay_nx_graphs:
            raise OverlayNotFound(overlay_id)

            # TODO: return False instead?

        self._overlay_id = overlay_id
        self._anm = anm
        #logger = logging.getLogger('ANK')
        #logstring = 'Overlay: %s' % str(overlay_id)
        #logger = CustomAdapter(logger, {'item': logstring})
        #object.__setattr__(self, 'log', logger)
        #self.init_logging("graph")
        logger = log
        object.__setattr__(self, 'log', logger)
        self.init_logging("graph")

    def __repr__(self):
        return self._overlay_id

    def is_multigraph(self):
        """Checks if the graph is multigraph"""
        return self._graph.is_multigraph()

    def is_directed(self):
        return self._graph.is_directed()

    @property
    def data(self):
        """Returns data stored on this overlay graph"""

        return NmGraphData(self._anm, self._overlay_id)

    def __contains__(self, n):
        """Checks if item is contained"""

        try:
            return n.node_id in self._graph
        except AttributeError:

            # try with node_id as a string

            return n in self._graph

    def interface(self, interface):
        """Returns in interface.nodeid format"""

        return NmPort(self._anm, self._overlay_id, interface.node_id,
                      interface.interface_id)

    def edge(self, edge_to_find, dst_to_find=None, key=0):
        '''returns edge in this graph with same src and dst
        and key for parallel edges (default is to return first edge)
        #TODO: explain parameter overloading: strings, edges, nodes...
        '''

        # TODO: handle multigraphs
        from autonetkit.nidb.node import DmNode
        if isinstance(edge_to_find, NmEdge):
            # TODO: tidy this logic
            edge = edge_to_find  # alias for neater code
            if (edge.is_multigraph() and self.is_multigraph()
                and self._graph.has_edge(edge.src,
                                         edge.dst, key=edge.ekey)):
                return NmEdge(self._anm, self._overlay_id,
                              edge.src, edge.dst, edge.ekey)
            elif (self._graph.has_edge(edge.src, edge.dst)):
                return NmEdge(self._anm, self._overlay_id,
                              edge.src, edge.dst)

        if isinstance(edge_to_find, NmEdge):
            src_id = edge_to_find.src
            dst_id = edge_to_find.dst
            search_key = key

            if self.is_multigraph():
                for (src, dst, rkey) in self._graph.edges(src_id,
                                                          keys=True):
                    if dst == dst_id and rkey == search_key:
                        return NmEdge(self._anm, self._overlay_id, src,
                                      dst, search_key)

            for (src, dst) in self._graph.edges(src_id):
                if dst == dst_id:
                    return NmEdge(self._anm, self._overlay_id, src, dst)

        # from here on look for (src, dst) pairs
        src = edge_to_find
        dst = dst_to_find

        if (isinstance(src, basestring) and isinstance(dst, basestring)):
            src = src.lower()
            dst = dst.lower()
            if self.is_multigraph():
                if self._graph.has_edge(src, dst, key=key):
                    return NmEdge(self._anm, self._overlay_id, src,
                                  dst, key)
            elif self._graph.has_edge(src, dst):
                return NmEdge(self._anm, self._overlay_id, src, dst)

        # TODO: refactor to pick up a BaseNode class that both NmNode, DmNode inherit from
        if isinstance(src, (NmNode, DmNode)) and isinstance(dst, (NmNode, DmNode)):
            src_id = src.node_id
            dst_id = dst.node_id

            if self.is_multigraph():
                if self._graph.has_edge(src_id, dst_id, key):
                    return NmEdge(self._anm, self._overlay_id, src, dst, key)

            else:
                if self._graph.has_edge(src_id, dst_id):
                    return NmEdge(self._anm, self._overlay_id, src, dst)


        if isinstance(src, NmPort) and isinstance(dst, NmPort):
            # further filter result by ports
            src_id = src.node_id
            dst_id = dst.node_id
            src_int = src.interface_id
            dst_int = dst.interface_id


            # TODO: combine duplicated logic from above
            #TODO: test with directed graph

            if self.is_multigraph():
                # search edges from src to dst
                for src, iter_dst, iter_key in self._graph.edges(src_id, keys=True):
                    if iter_dst != dst_id:
                        continue # to a different node

                    ports = self._graph[src][iter_dst][iter_key]["_ports"]
                    if ports[src_id] == src_int and ports[dst_id] == dst_int:
                        return NmEdge(self._anm, self._overlay_id, src_id, dst_id, iter_key)

            else:
                #TODO: add test case for here
                for src, iter_dst in self._graph.edges(src_id):
                    if iter_dst != dst_id:
                        continue # to a different node

                    ports = self._graph[src][iter_dst]["_ports"]
                    if ports[src_id] == src_int and ports[dst_id] == dst_int:
                        return NmEdge(self._anm, self._overlay_id, src_id, dst_id)






    def __getitem__(self, key):
        """Gets and returns the node with the corresponding key"""
        return self.node(key)

    def node(self, key):
        """Returns node based on name
        This is currently O(N). Could use a lookup table
        """

        # TODO: refactor

        try:
            if key.node_id in self._graph:
                return NmNode(self._anm, self._overlay_id, key.node_id)
        except AttributeError:

             # try as string id

            if key in self._graph:
                return NmNode(self._anm, self._overlay_id, key)

            # doesn't have node_id, likely a label string, search based on this
            # label

            for node in self:
                if str(node) == key:
                    return node
            # TODO: change warning to an exception
            log.warning('Unable to find node %s in %s ' % (key, self))
            return None

    def overlay(self, key):
        """Get to other overlay graphs in functions"""

        # TODO: refactor: shouldn't be returning concrete instantiation from
        # abstract parent!

        from autonetkit.anm.graph import NmGraph
        return NmGraph(self._anm, key)

    @property
    def name(self):
        """Return the name"""

        return self.__repr__()

    def __nonzero__(self):
        """Checks if the value is nonzero"""

        return self.anm.has_overlay(self._overlay_id)

    def node_label(self, node):
        """Return node label"""

        return repr(NmNode(self._anm, self._overlay_id, node))

    def has_edge(self, edge_to_find, dst_to_find=None,):
        """Tests if edge in graph"""

        if dst_to_find is None:
            if self.is_multigraph():
                return self._graph.has_edge(edge_to_find.src,
                    edge_to_find.dst, edge_to_find.ekey)

            return self._graph.has_edge(edge_to_find.src, edge_to_find.dst)

        else:
            return bool(self.edge(edge_to_find, dst_to_find))

    def __iter__(self):
        return iter(self.nodes())

    def __len__(self):
        """Returns length of the graph"""

        return len(self._graph)

    def nodes(self, *args, **kwargs):
        result = list(NmNode(self._anm, self._overlay_id, node)
                      for node in self._graph)

        if len(args) or len(kwargs):
            result = self.filter(result, *args, **kwargs)
        return result

    def routers(self, *args, **kwargs):
        """Shortcut for nodes(), sets device_type to be router"""

        result = self.nodes(*args, **kwargs)
        return [r for r in result if r.is_router()]

    def switches(self, *args, **kwargs):
        """Shortcut for nodes(), sets device_type to be switch"""

        result = self.nodes(*args, **kwargs)
        return [r for r in result if r.is_switch()]

    def servers(self, *args, **kwargs):
        """Shortcut for nodes(), sets device_type to be server"""

        result = self.nodes(*args, **kwargs)
        return [r for r in result if r.is_server()]

    def l3devices(self, *args, **kwargs):
        """Shortcut for nodes(), tests if device is_l3device"""

        result = self.nodes(*args, **kwargs)
        return [r for r in result if r.is_l3device()]

    def device(self, key):
        """To access programatically"""

        return NmNode(self._anm, self._overlay_id, key)

    def groupby(self, attribute, nodes=None):
        """Returns a dictionary sorted by attribute"""

        result = {}

        if not nodes:
            data = self.nodes()
        else:
            data = nodes
        data = sorted(data, key=lambda x: x.get(attribute))
        for (key, grouping) in itertools.groupby(data, key=lambda x:
                                                 x.get(attribute)):
            result[key] = list(grouping)

        return result

    def filter(self, nbunch=None, *args, **kwargs):
        """Filter the nodes"""

        if nbunch is None:
            nbunch = self.nodes()

        def filter_func(node):
            """Filter based on args and kwargs"""

            return all(node.get(key) for key in args) \
                and all(node.get(key) == val for (key, val) in
                        kwargs.items())

        return [n for n in nbunch if filter_func(n)]

    def edges(self, src_nbunch=None, dst_nbunch=None, *args,
              **kwargs):
        """Returns edges. Can also return edges by setting filter."""

# src_nbunch or dst_nbunch may be single node
# TODO: refactor this

        if src_nbunch:
            nbunch_out = []
            try:
                src_nbunch = src_nbunch.node_id
            except AttributeError:
                src_nbunch = (n.node_id for n in src_nbunch)

                # only store the id in overlay

        def filter_func(edge):
            """Filter based on args and kwargs"""

            return all(edge.get(key) for key in args) \
                and all(edge.get(key) == val for (key, val) in
                        kwargs.items())

        if self.is_multigraph():
            valid_edges = list((src, dst, key) for (src, dst, key) in
                               self._graph.edges(src_nbunch, keys=True))
        else:
            default_key = 0
            valid_edges = list((src, dst, default_key)
                               for (src, dst) in self._graph.edges(src_nbunch))

        if dst_nbunch:
            try:
                dst_nbunch = dst_nbunch.node_id
                dst_nbunch = set([dst_nbunch])
            except AttributeError:
                dst_nbunch = (n.node_id for n in dst_nbunch)
                dst_nbunch = set(dst_nbunch)

            valid_edges = list((src, dst, key) for (src, dst, key) in
                               valid_edges if dst in dst_nbunch)

        if len(args) or len(kwargs):
            all_edges = [NmEdge(self._anm, self._overlay_id, src, dst,
                                key) for (src, dst, key) in valid_edges]
            result = list(edge for edge in all_edges
                          if filter_func(edge))
        else:
            result = list(NmEdge(self._anm, self._overlay_id, src, dst,
                                 key) for (src, dst, key) in valid_edges)

        return list(result)

