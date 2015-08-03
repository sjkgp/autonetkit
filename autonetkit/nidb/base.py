import autonetkit.log as log
import autonetkit

from autonetkit.nidb.interface import DmInterface
from autonetkit.nidb.edge import DmEdge
from autonetkit.nidb.node import DmNode
from autonetkit import ank_json

# TODO: add to doc we don't llow bidirectional nidb


class DmBase(object):
    # TODO: inherit common methods from same base as overlay

    def __init__(self):
        # TODO: make optional for restore serialized file on init
        self._graph = None
        pass

    def __getstate__(self):
        return self._graph

    def __setstate__(self, state):
        self._graph = state

    def __repr__(self):
        """Return nidb
        >>> anm = autonetkit.topos.mixed()
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> nidb
        nidb
        """
        return "nidb"

    def is_multigraph(self):
        """Returns graph that is multigraph

        >>> anm = autonetkit.topos.house()
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> nidb.is_multigraph()
        True
        >>> anm = autonetkit.topos.multi_edge()
        >>> nidb.is_multigraph()
        True
        """
        return self._graph.is_multigraph()

    # Model-level functions

    def save(self, timestamp=True, use_gzip=True):
        """ Used to save

        >>> anm = autonetkit.topos.house()
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> nidb.save()
        """
        import os
        import gzip
        archive_dir = os.path.join("versions", "nidb")
        if not os.path.isdir(archive_dir):
            os.makedirs(archive_dir)

        data = ank_json.ank_json_dumps(self._graph)
        if timestamp:
            json_file = "nidb_%s.json.gz" % self.timestamp
        else:
            json_file = "nidb.json"
        json_path = os.path.join(archive_dir, json_file)
        log.debug("Saving to %s" % json_path)
        if use_gzip:
            with gzip.open(json_path, "wb") as json_fh:
                json_fh.write(data)
        else:
            with open(json_path, "wb") as json_fh:
                json_fh.write(data)

    def interface(self, interface):
        """
        >>> anm = autonetkit.topos.house()
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> test_node = nidb.node("r1")
        >>> eth0 = test_node.interface(1)
        >>> nidb.interface(eth0)
        r1.r1 to r2
        """
        return DmInterface(self,
                           interface.node_id, interface.interface_id)

    def restore_latest(self, directory=None):
        """Restore latest saved DeviceModel

        # >>> anm = autonetkit.topos.mixed()
        # >>> nidb = autonetkit.DeviceModel(anm)
        # >>> nidb.restore_latest()
        # WARNING No previous DeviceModel saved. Please compile new DeviceModel
        """
        import os
        import glob
        if not directory:
            # TODO: make directory loaded from config
            directory = os.path.join("versions", "nidb")

        glob_dir = os.path.join(directory, "*.json.gz")
        pickle_files = glob.glob(glob_dir)
        pickle_files = sorted(pickle_files)
        try:
            latest_file = pickle_files[-1]
        except IndexError:
            # No files loaded
            log.warning(
                "No previous DeviceModel saved. Please compile new DeviceModel")
            return
        self.restore(latest_file)
        ank_json.rebind_nidb_interfaces(self)

    def restore(self, pickle_file):
        """Used to restore specific file by setting the file"""
        import gzip
        log.debug("Restoring %s" % pickle_file)
        with gzip.open(pickle_file, "r") as fh:
            #data = json.load(fh)
            data = fh.read()
            self._graph = ank_json.ank_json_loads(data)

        ank_json.rebind_nidb_interfaces(self)

    @property
    def name(self):
        """ Return name

        >>> anm = autonetkit.topos.mixed()
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> nidb.name
        'nidb'
        """
        return self.__repr__()

    def raw_graph(self):
        """Returns the underlying NetworkX graph

        >>> anm = autonetkit.topos.mixed()
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> nidb.__setstate__('r1')
        >>> nidb.raw_graph()
        'r1'
        """
        return self._graph

    def copy_graphics(self, network_model):
        """Transfers graphics data from anm to nidb"""
        for node in self:
            node.add_stanza("graphics")
            #TODO: deprecate g_graphics overlay, store on phy
            if (network_model.has_overlay("graphics")
                and node in network_model['graphics']):
                source_node = network_model['graphics'].node(node)
            else:
                source_node = network_model['phy'].node(node)
            node.graphics.x = source_node.x
            node.graphics.y = source_node.y
            node.graphics.device_type = source_node.device_type
            node.graphics.device_subtype = source_node.device_subtype
            node.device_type = source_node.device_type
            node.device_subtype = source_node.device_subtype

    def __len__(self):
        """Returns length of the graph

        >>> anm = autonetkit.topos.mixed()
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> nidb.__len__()
        5
        """
        return len(self._graph)

    @property
    def data(self):
        """Returns data stored on the graph

        # >>> anm = autonetkit.topos.mixed()
        # >>> nidb = autonetkit.DeviceModel(anm)
        # >>> nidb.data
        # DeviceModel data: {'topologies': defaultdict(<type 'dict'>, {}), 'timestamp': '20150421_143139'}
        """
        from autonetkit.nidb.device_model import DmGraphData
        return DmGraphData(self)

    # Nodes

    def __iter__(self):
        return iter(DmNode(self, node)
                    for node in self._graph)

    def node(self, key):
        """Returns node based on name
        This is currently O(N). Could use a lookup table

        >>> anm = autonetkit.topos.mixed()
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> test_node = nidb.node("r1")
        >>> eth0 = test_node.interface(1)
        >>> nidb.node(eth0)
        r1
        """
        try:
            if key.node_id in self._graph:
                return DmNode(self, key.node_id)
        except AttributeError:
            # doesn't have node_id, likely a label string, search on label
            for node in self:
                if str(node) == key:
                    return node
                elif node.id == key:
                    return node
            print "Unable to find node", key, "in", self
            return None

    def update(self, nbunch, **kwargs):
        for node in nbunch:
            for (_, key), value in kwargs.items():
                node.category.set(key, value)

    def nodes(self, *args, **kwargs):
        result = self.__iter__()
        if len(args) or len(kwargs):
            result = self.filter(result, *args, **kwargs)
        return result

    def routers(self, *args, **kwargs):
        """Shortcut for nodes(), sets device_type to be router

        >>> anm = autonetkit.topos.mixed()
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> nidb.routers()
        [r1, r2, r3]


        """

        result = self.nodes(*args, **kwargs)
        return [r for r in result if r.is_router()]

    def switches(self, *args, **kwargs):
        """Shortcut for nodes(), sets device_type to be switch

        >>> anm = autonetkit.topos.mixed()
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> nidb.switches()
        [sw1]
        """
        result = self.nodes(*args, **kwargs)
        return [r for r in result if r.is_switch()]

    def servers(self, *args, **kwargs):
        """Shortcut for nodes(), sets device_type to be server

        >>> anm = autonetkit.topos.mixed()
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> nidb.servers()
        [s1]
        """
        result = self.nodes(*args, **kwargs)
        return [r for r in result if r.is_server()]

    def l3devices(self, *args, **kwargs):
        """Shortcut for nodes(), sets device_type to be server

        >>> anm = autonetkit.topos.mixed()
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> nidb.l3devices()
        [s1, r1, r2, r3]
        """

        result = self.nodes(*args, **kwargs)
        return [r for r in result if r.is_l3device()]

    def filter(self, nbunch=None, *args, **kwargs):
        # TODO: also allow nbunch to be passed in to subfilter on...?
        """TODO: expand this to allow args also, ie to test if value evaluates to True"""
        # need to allow filter_func to access these args
        if not nbunch:
            nbunch = self.nodes()

        def filter_func(node):
            return (
                all(getattr(node, key) for key in args) and
                all(getattr(node, key) == val for key, val in kwargs.items())
            )

        return (n for n in nbunch if filter_func(n))

    def add_nodes_from(self, nbunch, retain=None, **kwargs):
        """Add nodes from by importing from different overlay"""
        if retain is None:
            retain = []
        try:
            retain.lower()
            retain = [retain]  # was a string, put into list
        except AttributeError:
            pass  # already a list

        nbunch = list(nbunch)
        nodes_to_add = nbunch  # retain for interface copying

        if len(retain):
            add_nodes = []
            for n in nbunch:
                data = dict((key, n.get(key)) for key in retain)
                add_nodes.append((n.node_id, data))
            nbunch = add_nodes
        else:
            log.warning(
                "Cannot add node ids directly to DeviceModel: must add overlay nodes")
        self._graph.add_nodes_from(nbunch, **kwargs)

        for node in nodes_to_add:
            # TODO: add an interface_retain for attributes also
            int_dict = {i.interface_id: {'category': i.category,
                                         'description': i.description,
                                         'layer': i.overlay_id} for i in node.interfaces()}
            int_dict = {i.interface_id: {'category': i.category,
                                         'description': i.description,
                                         } for i in node.interfaces()}
            self._graph.node[node.node_id]["_ports"] = int_dict

    # Edges

    def edges(self, nbunch=None, *args, **kwargs):
        """returns edges in the graph

        >>> import autonetkit
        >>> anm = autonetkit.NetworkModel()
        >>> g_phy = anm['phy']
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> input_edges = [("r1", "r2"), ("r2", "r4"), ("r3", "r4"), ("r3", "r5"), ("r1", "r3")]
        >>> nodes = ['r1', 'r2', 'r3', 'r4', 'r5']
        >>> g_in = anm.add_overlay("input")
        >>> g_in.add_nodes_from(nodes)
        >>> g_in.add_edges_from(input_edges)
        [(r1, r2), (r2, r4), (r3, r4), (r3, r5), (r1, r3)]
        >>> g_phy.add_nodes_from(g_in)
        >>> g_phy.add_edges_from(g_in.edges())
        [(r4, r2), (r4, r3), (r5, r3), (r1, r2), (r1, r3)]
        >>> retain = ['label', 'host', 'platform', 'x', 'y', 'asn', 'device_type']
        >>> nidb.add_nodes_from(g_phy, retain=retain)
        >>> nidb.add_edges_from(g_phy.edges())
        >>> list(nidb.edges())
        [(r4, r2, 0), (r4, r3, 0), (r5, r3, 0), (r1, r2, 0), (r1, r3, 0)]

        """
        # nbunch may be single node
        # TODO: Apply edge filters
        if nbunch:
            try:
                nbunch = nbunch.node_id
            except AttributeError:
                # only store the id in overlay
                nbunch = (n.node_id for n in nbunch)

        def filter_func(edge):
            """Filter based on args and kwargs"""
            return (
                all(getattr(edge, key) for key in args) and
                all(getattr(edge, key) == val for key, val in kwargs.items())
            )

        # TODO: See if more efficient way to access underlying data structure
        # rather than create overlay to throw away
        if self.is_multigraph():
            valid_edges = list((src, dst, key) for (src, dst, key) in
                               self._graph.edges(nbunch, keys=True))
        else:
            default_key = 0
            valid_edges = list((src, dst, default_key) for (src, dst) in
                               self._graph.edges(nbunch))

        all_edges = [DmEdge(self, src, dst, key)
                     for src, dst, key in valid_edges]
        return (edge for edge in all_edges if filter_func(edge))

    def edge(self, edge_to_find, key=0):
        """returns edge in this graph with same src and dst"""
        # TODO: check if this even needed - will be if searching nidb specifically
        # but that's so rare (that's a design stage if anywhere)
        src_id = edge_to_find.src
        dst_id = edge_to_find.dst
        search_key = key

        if self.is_multigraph():
            for (src, dst, rkey) in self._graph.edges(src_id, keys=True):
                if dst == dst_id and rkey == search_key:
                    return DmEdge(self, src, dst, search_key)

        for (src, dst) in self._graph.edges(src_id):
            if dst == dst_id:
                return DmEdge(self, src, dst)

    def add_edge(self, src, dst, retain=None, **kwargs):
        """Add edge with the set source and the destination"""
        # TODO: support multigraph
        if retain is None:
            retain = []
        self.add_edges_from([(src, dst)], retain, **kwargs)

    def add_edges_from(self, ebunch, retain=None, **kwargs):
        """Used to copy edges from ANM -> NIDB
        Note: won't support (yet) copying from one NIDB to another
        #TODO: allow copying from one NIDB to another
        (check for DmNode as well as NmNode)

        To keep congruency, only allow copying edges from ANM
        can't add NIDB edges directly (node, node) or (port, port)
        workflow: if need this, create a new overlay and copy from there

        >>> import autonetkit
        >>> anm = autonetkit.NetworkModel()
        >>> g_phy = anm['phy']
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> input_edges = [("r1", "r2"), ("r2", "r4"), ("r3", "r4"), ("r3", "r5"), ("r1", "r3")]
        >>> nodes = ['r1', 'r2', 'r3', 'r4', 'r5']
        >>> g_in = anm.add_overlay("input")
        >>> g_in.add_nodes_from(nodes)
        >>> g_in.add_edges_from(input_edges)
        [(r1, r2), (r2, r4), (r3, r4), (r3, r5), (r1, r3)]
        >>> g_phy.add_nodes_from(g_in)
        >>> g_phy.add_edges_from(g_in.edges())
        [(r4, r2), (r4, r3), (r5, r3), (r1, r2), (r1, r3)]
        >>> retain = ['label', 'host', 'platform', 'x', 'y', 'asn', 'device_type']
        >>> nidb.add_nodes_from(g_phy, retain=retain)
        >>> nidb.add_edges_from(g_phy.edges())
        >>> list(nidb.edges())
        [(r4, r2, 0), (r4, r3, 0), (r5, r3, 0), (r1, r2, 0), (r1, r3, 0)]

        >>> list(nidb.edges())
        [(r4, r2, 0), (r4, r3, 0), (r5, r3, 0), (r1, r2, 0), (r1, r3, 0)]
        """
        from autonetkit.anm import NmEdge
        if not retain:
            retain = []
        try:
            retain.lower()
            retain = [retain]  # was a string, put into list
        except AttributeError:
            pass  # already a list

        # TODO: this needs to support parallel links
        for in_edge in ebunch:
            """Edge could be one of:
            - NmEdge - copied into be returned as a DmEdge
            """
            # This is less efficient than nx add_edges_from, but cleaner logic
            # TODO: could put the interface data into retain?
            data = {'_ports': {}}  # to retain
            ekey = 0

            # convert input to a NmEdge
            if isinstance(in_edge, NmEdge):
                edge = in_edge  # simple case
                ekey = edge.ekey
                src = edge.src.node_id
                dst = edge.dst.node_id

                # and copy retain data
                retain.append('_ports')
                # TODO: explicity copy ports as raw_interfaces?
                data = dict((key, edge.get(key)) for key in retain)

                # this is the only case where copy across data
                # but want to copy attributes for all cases

            # TODO: add check that edge.src and edge.dst exist
            if not(src in self and dst in self):
                log.warning("Not adding edge, %s to %s, "
                            "src and/or dst not in overlay %s" % (src, dst, self))
                continue

            # TODO: warn if not multigraph and edge already exists - don't
            # add/clobber
            data.update(**kwargs)

            if self.is_multigraph():
                self._graph.add_edge(src, dst, key=ekey,
                                     attr_dict=dict(data))
            else:
                self._graph.add_edge(src, dst, attr_dict=dict(data))
