#!/usr/bin/python
# -*- coding: utf-8 -*-

import itertools
from collections import namedtuple
import autonetkit

import autonetkit.log as log
import networkx as nx
from ank_utils import unwrap_graph, unwrap_nodes
from autonetkit.anm import NmEdge, NmNode

# helper namedtuples - until have a more complete schema (such as from Yang)
static_route_v4 = namedtuple("static_route_v4",
                             ["prefix", "netmask", "nexthop", "metric"])

static_route_v6 = namedtuple("static_route_v6",
                             ["prefix", "nexthop", "metric"])


# TODO: add ability to specify labels to unwrap too

# TODO: split into a utils module


def sn_preflen_to_network(address, prefixlen):
    """Workaround for creating an IPNetwork from an address and a prefixlen.
    TODO: check if this is part of netaddr module
    """

    import netaddr
    return netaddr.IPNetwork('%s/%s' % (address, prefixlen))


def fqdn(node):
    """
    Returns in label.asn format of a node.
    """
    return '%s.%s' % (node.label, node.get('asn'))


def name_folder_safe(foldername):
    """Returning foldername if it's safe. If illegal character exists,
       replace the illegal character with a underscore.
    """
    for illegal_char in [' ', '/', '_', ',', '.', '&amp;', '-', '(', ')', ]:
        foldername = foldername.replace(illegal_char, '_')

    # Don't want double _

    while '__' in foldername:
        foldername = foldername.replace('__', '_')
    return foldername


def set_node_default(nm_graph, nbunch=None, **kwargs):
    """
    Sets all nodes in nbunch to value if key not already set
    This will not apply to future nodes that are added.
    """

    # work with the underlying NetworkX graph for efficiency
    graph = unwrap_graph(nm_graph)
    if nbunch is None:
        nbunch = graph.nodes()
    else:
        nbunch = unwrap_nodes(nbunch)
    for node in nbunch:
        for (key, val) in kwargs.items():
            if key not in graph.node[node]:
                graph.node[node][key] = val


# TODO: also add ability to copy multiple attributes

# TODO: rename to copy_node_attr_from


def copy_attr_from(overlay_src, overlay_dst, src_attr, dst_attr=None,
                   nbunch=None, type=None, default=None):
    """ Copies attribute from specific values that user sets from the source
        to the destination. Also can specify the remote attribute or default value.
    """

    if not dst_attr:
        dst_attr = src_attr

    graph_src = unwrap_graph(overlay_src)
    graph_dst = unwrap_graph(overlay_dst)
    if not nbunch:
        nbunch = graph_src.nodes()

    for node in nbunch:
        try:
            val = graph_src.node[node].get(src_attr, default)
        except KeyError:

            # TODO: check if because node doesn't exist in dest, or because
            # attribute doesn't exist in graph_src

            log.debug('Unable to copy node attribute %s for %s in %s',
                      src_attr, node, overlay_src)
        else:

            # TODO: use a dtype to take an int, float, etc

            if type is float:
                val = float(val)
            elif type is int:
                val = int(val)

            if node in graph_dst:
                graph_dst.node[node][dst_attr] = val


def copy_int_attr_from(overlay_src, overlay_dst, src_attr, dst_attr=None,
                       nbunch=None, type=None, default=None):
    """
    Copies interger attributes from the source to destination.
    Supported types are float and int.
    """

    # note; uses high-level API for practicality over raw speed

    if not dst_attr:
        dst_attr = src_attr

    if nbunch:
        nbunch = [overlay_src.node(n) for n in nbunch]
    else:
        nbunch = overlay_src.nodes()

    for node in nbunch:
        for src_int in node:
            val = src_int.get(src_attr)
            if val is None:
                val = default

            if type is float:
                val = float(val)
            elif type is int:
                val = int(val)

            if node not in overlay_dst:
                continue

            dst_int = overlay_dst.interface(src_int)
            if dst_int is not None:
                dst_int.set(dst_attr, val)


def copy_edge_attr_from(overlay_src, overlay_dst, src_attr,
                        dst_attr=None, type=None, default=None):
    # note this won't work if merge/aggregate edges
    """
    Main purpose is to copy edge attributes from source to the destination.
    Gets the edge attribute
    """
    if not dst_attr:
        dst_attr = src_attr

    for edge in overlay_src.edges():
        try:
            val = edge.get(src_attr)
            if val is None:
                val = default
        except KeyError:

            # TODO: check if because edge doesn't exist in dest, or because
            # attribute doesn't exist in graph_src

            log.debug('Unable to copy edge attribute %s for (%s, %s) in %s',
                      src_attr, edge.src, edge.dst, overlay_src)

        else:

            # TODO: use a dtype to take an int, float, etc

            if type is float:
                val = float(val)
            elif type is int:
                val = int(val)

            try:
                overlay_dst.edge(edge).set(dst_attr, val)
            except AttributeError:
                # fail to debug - as attribute may not have been set
                log.debug('Unable to set edge attribute on %s in %s',
                          edge, overlay_dst)


def wrap_edges(nm_graph, edges):
    """ wraps edge ids into the edge overlay.
    """

    # TODO: make support multigraphs

    edges = list(edges)
    if not any(len(e) for e in edges):
        return []  # each edge tuple is empty

    try:

        # strip out data from (src, dst, data) tuple

        edges = [(s, t) for (s, t, _) in edges]
    except ValueError:
        pass  # already of form (src, dst)

    return list(NmEdge(nm_graph._anm, nm_graph._overlay_id, src, dst)
                for (src, dst) in edges)


def wrap_nodes(nm_graph, nodes):
    """ Wraps node id into the node overlay.
     """

    return [NmNode(nm_graph._anm, nm_graph._overlay_id, node)
            for node in nodes]


def in_edges(nm_graph, nodes=None):
    """
    Returns incoming edges NetworkModel edge objects.
    """

    graph = unwrap_graph(nm_graph)
    edges = graph.in_edges(nodes)
    return wrap_edges(nm_graph, edges)


def split(nm_graph, edges, retain=None, id_prepend=''):
    """
    Splits edges in two, retaining any attributes specified.
    """

    added_nodes = []

    for edge in edges:
        src_node = edge.src
        dst_node = edge.dst
        src_int = edge.src_int
        dst_int = edge.dst_int

        # form name
        if nm_graph.is_directed():
            new_id = '%s%s_%s' % (id_prepend, src_node, dst_node)
        else:

            # undirected, make id deterministic across ank runs

            # use sorted for consistency
            (node_a, node_b) = sorted([src_node, dst_node])
            new_id = '%s%s_%s' % (id_prepend, node_a, node_b)

        if nm_graph.is_multigraph():
            new_id = new_id + '_%s' % edge.ekey

        split_node = nm_graph.add_node(new_id)
        added_nodes.append(split_node)
        split_ifaceA = split_node.add_interface()
        split_ifaceB = split_node.add_interface()

        nm_graph.add_edge(src_int, split_ifaceA)
        nm_graph.add_edge(dst_int, split_ifaceB)
        nm_graph.remove_edge(edge)

    return added_nodes

def explode_nodes(nm_graph, nodes, retain=None):
    """Explodes all nodes in nodes.
    TODO: Add support for digraph - check if nm_graph.is_directed()
    """
    if retain is None:
        retain = []

    log.debug('Exploding nodes')
    try:
        retain.lower()
        retain = [retain]  # was a string, put into list
    except AttributeError:
        pass  # already a list

    total_added_edges = []  # keep track to return

    if nodes in nm_graph:
        nodes = [nodes]  # place into list for iteration

    for node in nodes:

        edges = node.edges()
        edge_pairs = [(e1, e2) for e1 in edges for e2 in edges if e1
                      != e2]
        added_pairs = set()
        for edge_pair in edge_pairs:
            (src_edge, dst_edge) = sorted(edge_pair)
            if (src_edge, dst_edge) in added_pairs:
                continue  # already added this link pair in other direction
            else:
                added_pairs.add((src_edge, dst_edge))

            src = src_edge.dst  # src is the exploded node
            dst = dst_edge.dst  # src is the exploded node

            if src == dst:
                continue  # don't add self-loop

            data = dict((key, src_edge._data.get(key)) for key in
                        retain)
            node_to_dst_data = dict((key, dst_edge._data.get(key))
                                    for key in retain)
            data.update(node_to_dst_data)

            data['_ports'] = {}
            try:
                src_int_id = src_edge.raw_interfaces[src.node_id]
            except KeyError:
                pass  # not set
            else:
                data['_ports'][src.node_id] = src_int_id

            try:
                dst_int_id = dst_edge.raw_interfaces[dst.node_id]
            except KeyError:
                pass  # not set
            else:
                data['_ports'][dst.node_id] = dst_int_id

            new_edge = (src.node_id, dst.node_id, data)

            # TODO: use add_edge

            nm_graph.add_edges_from([new_edge])
            total_added_edges.append(new_edge)

        nm_graph.remove_node(node)
    return wrap_edges(nm_graph, total_added_edges)


def label(nm_graph, nodes):
    """
    Returns the label for each node in list format after looking up for each node.
    """
    return list(nm_graph._anm.node_label(node) for node in nodes)


def connected_subgraphs(nm_graph, nodes=None):
    """
    Returns the connected subgraphs in list. If edges are removed from connected graph,
    subgraph would output subgraphs with reflected changes.
    """
    if nodes is None:
        nodes = nm_graph.nodes()
    else:
        nodes = list(unwrap_nodes(nodes))
    graph = unwrap_graph(nm_graph)
    subgraph = graph.subgraph(nodes)
    if not len(subgraph.edges()):
        # print "Nothing to aggregate for %s: no edges in subgraph"

        pass
    if graph.is_directed():
        component_nodes_list = \
            nx.strongly_connected_components(subgraph)
    else:
        component_nodes_list = nx.connected_components(subgraph)

    wrapped = []
    for component in component_nodes_list:
        wrapped.append(list(wrap_nodes(nm_graph, component)))

    return wrapped


def aggregate_nodes(nm_graph, nodes):
    """Used to aggregate nodes in the nm_graph. Returns values with
    total amount of edges that are added.
    """

    #TODO: remove subgraph step into separate function

    nodes = list(unwrap_nodes(nodes))
    graph = unwrap_graph(nm_graph)
    subgraph = graph.subgraph(nodes)
    if not len(subgraph.edges()):
        # print "Nothing to aggregate for %s: no edges in subgraph"

        pass
    total_added_edges = []
    if graph.is_directed():
        component_nodes_list = \
            nx.strongly_connected_components(subgraph)
    else:
        component_nodes_list = nx.connected_components(subgraph)
    for component_nodes in component_nodes_list:
        if len(component_nodes) > 1:
            component_nodes = [nm_graph.node(n)
                               for n in component_nodes]

            # TODO: could choose most connected, or most central?
            # TODO: refactor so use nodes_to_remove

            nodes_to_remove = list(component_nodes)
            base = nodes_to_remove.pop()  # choose a base device to retain
            log.debug('Retaining %s, removing %s', base,
                      nodes_to_remove)

            external_interfaces = []
            for node in nodes_to_remove:
                external_interfaces += [e.dst_int for e in node.edges()
                if e.dst not in component_nodes]
                # all edges out of component

            log.debug('External interfaces %s', external_interfaces)
            edges_to_add = []
            for dst_int in external_interfaces:
                split_ifaceA = base.add_interface()
                new_edge = nm_graph.add_edge(split_ifaceA, dst_int)
                total_added_edges.append(new_edge)

            nm_graph.remove_nodes_from(nodes_to_remove)

    # return wrap_edges(nm_graph, total_added_edges)
    return total_added_edges


def most_frequent(iterable):
    """Returns most frequent item in iterable. If value error occurs,
    it will return that it's unable to calculate most frequent value.
    """

    # from http://stackoverflow.com/q/1518522

    gby = itertools.groupby
    try:
        return max(gby(sorted(iterable)), key=lambda (x, v):
        (len(list(v)), -iterable.index(x)))[0]
    except ValueError, error:
        log.warning('Unable to calculate most_frequent, %s', error)
        return None


def neigh_most_frequent(nm_graph, node, attribute,
                        attribute_graph=None, allow_none=False):
    """Used to explicitly force most frequent values of attribute in sorted format.
    """

    # TODO: rename to median?

    graph = unwrap_graph(nm_graph)
    if attribute_graph:
        attribute_graph = unwrap_graph(attribute_graph)
    else:
        attribute_graph = graph  # use input graph
    node = unwrap_nodes(node)
    values = [attribute_graph.node[n].get(attribute) for n in
              graph.neighbors(node)]
    values = sorted(values)
    if not allow_none:
        values = [v for v in values if v is not None]

    if len(values):
        return most_frequent(values)


def neigh_average(nm_graph, node, attribute, attribute_graph=None):
    """
    averages out attribute from neighbors in specified nm_graph
    attribute_graph is the graph to read the attribute from
    if property is numeric, then return mean
    else return most frequently occuring value
    """

    graph = unwrap_graph(nm_graph)
    if attribute_graph:
        attribute_graph = unwrap_graph(attribute_graph)
    else:
        attribute_graph = graph  # use input graph
    node = unwrap_nodes(node)
    values = [attribute_graph.node[n].get(attribute) for n in
              graph.neighbors(node)]

    try:
        values = [float(val) for val in values]
        return sum(values) / len(values)
    except ValueError:
        return most_frequent(values)


def neigh_attr(nm_graph, node, attribute, attribute_graph=None):
    """
    For each node in valid nodes, return neighbor attribute
    from neighbors in specified nm_graph. attribute_graph is the graph to read the attribute from.
    """

    graph = unwrap_graph(nm_graph)
    node = unwrap_nodes(node)
    if attribute_graph:
        attribute_graph = unwrap_graph(attribute_graph)
    else:
        attribute_graph = graph  # use input graph

    # Only look at nodes which exist in attribute_graph

    neighs = (n for n in graph.neighbors(node))
    valid_nodes = (n for n in neighs if n in attribute_graph)
    return (attribute_graph.node[node].get(attribute) for node in
            valid_nodes)


def neigh_equal(nm_graph, node, attribute, attribute_graph=None):
    """Boolean, returns True if neighbors in nm_graph
    all have same attribute in attribute_graph. If not, returns False.
    """

    neigh_attrs = neigh_attr(nm_graph, node, attribute, attribute_graph)
    return len(set(neigh_attrs)) == 1


def unique_attr(nm_graph, attribute):
    """
    Returns a set which contains unique attribute in nm_graph. Goes
    through the nodes, and searches for the attribute that has been set.
    """
    graph = unwrap_graph(nm_graph)
    return set(graph.node[node].get(attribute) for node in graph)


def groupby(attribute, nodes):
    """Takes a group of nodes and returns a generator of (attribute, nodes)
     for each attribute value. A simple wrapped around itertools.groupby
     that creates a lambda for the attribute.
    """

    keyfunc = lambda x: x.get(attribute)
    nodes = sorted(nodes, key=keyfunc)
    return itertools.groupby(nodes, key=keyfunc)


def shortest_path(nm_graph, src, dst):
    """
    Returns the shortest path from the source to the destination.
    """
    # TODO: move to utils
    # TODO: use networkx boundary nodes directly: does the same thing

    graph = unwrap_graph(nm_graph)
    src_id = unwrap_nodes(src)
    dst_id = unwrap_nodes(dst)

    # TODO: check path works for muli-edge graphs too
    path = nx.shortest_path(graph, src_id, dst_id)

    return wrap_nodes(nm_graph, path)


def boundary_nodes(nm_graph, nodes):
    """ returns nodes at boundary of G based on
    edge_boundary from networkx.
    """

    # TODO: move to utils
    # TODO: use networkx boundary nodes directly: does the same thing

    graph = unwrap_graph(nm_graph)
    nodes = list(nodes)
    nbunch = list(unwrap_nodes(nodes))

    # find boundary

    b_edges = nx.edge_boundary(graph, nbunch)  # boundary edges
    internal_nodes = [s for (s, _) in b_edges]
    assert all(n in nbunch for n in internal_nodes)  # check internal

    return wrap_nodes(nm_graph, internal_nodes)


def shallow_copy_nx_graph(nx_graph):
    """Convenience wrapper for nx shallow copy"""
    directed = nx_graph.is_directed()
    multi = nx_graph.is_multigraph()

    if directed:
        if multi:
            return nx.MultiDiGraph(nx_graph)
        else:
            return nx.DiGraph(nx_graph)
    else:
        if multi:
            return nx.MultiGraph(nx_graph)
        else:
            return nx.Graph(nx_graph)
