import collections
import logging
from autonetkit.log import CustomAdapter
import autonetkit.log as log
import autonetkit


class DmInterface(object):

    def __init__(self, nidb, node_id, interface_id):
        object.__setattr__(self, 'nidb', nidb)
        object.__setattr__(self, 'node_id', node_id)
        object.__setattr__(self, 'interface_id', interface_id)
        #logger = logging.getLogger("ANK")
        #logstring = "Interface: %s" % str(self)
        #self.log = CustomAdapter(logger, {'item': logstring})
        logger = log
        object.__setattr__(self, 'log', logger)

    def __key(self):
        """Note: key doesn't include overlay_id to allow fast cross-layer comparisons"""

        # based on http://stackoverflow.com/q/2909106
        return (self.interface_id, self.node_id)

    def __hash__(self):
        """"Returns hash of a key

        >>> anm = autonetkit.topos.mixed()
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> test_node = nidb.node("r1")
        >>> eth0 = test_node.interface(1)
        >>> hash(eth0)
        2346446788448031185
        """
        return hash(self.__key())

    def __eq__(self, other):
        """Compare two __keys

        >>> anm = autonetkit.topos.mixed()
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> test_node = nidb.node("r1")
        >>> eth0 = test_node.interface(1)
        >>> eth0.__eq__(eth0)
        True

        """
        return self.__key() == other.__key()

    def __lt__(self, other):
        """Comparison method

        >>> anm = autonetkit.topos.house()
        >>> g_phy = anm['phy']
        >>> test_node = g_phy.node("r1")
        >>> eth0 = test_node.interface(1)
        >>> eth0.__lt__(eth0)
        False

        """

        # TODO: check how is comparing the node

        return (self.node, self.interface_id) < (other.node,
                                                 other.interface_id)

    @property
    def is_bound(self):
        """Returns if this interface is bound to an edge on this layer

        >>> anm = autonetkit.topos.mixed()
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> test_node = nidb.node("r1")
        >>> eth0 = test_node.interface(1)
        >>> loopback0 = test_node.interface(0)
        >>> eth0.is_bound
        True
        >>> loopback0.is_bound
        False

        """
        return len(self.edges()) > 0

    def __repr__(self):
        """Return string representation of an object in node, description format

        >>> anm = autonetkit.topos.mixed()
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> test_node = nidb.node("r1")
        >>> eth0 = test_node.interface(1)
        >>> repr(eth0)
        'r1.r1 to sw1'
        """

        description = self.description or self.interface_id
        return "%s.%s" % (self.node, description)

    def __nonzero__(self):
        """Allows for checking if node exists

        >>> anm = autonetkit.topos.mixed()
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> test_node = nidb.node("r1")
        >>> eth0 = test_node.interface(1)
        >>> loopback0 = test_node.interface(0)
        >>> eth1 = test_node.interface(2)
        >>> bool(eth1)
        True
        >>> bool(eth0)
        True
        >>> bool(loopback0)
        True

        """
        return len(self._port) > 0  # if interface data set

    def __str__(self):
        """Get string representation of an object

        >>> anm = autonetkit.topos.mixed()
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> test_node = nidb.node("r1")
        >>> eth0 = test_node.interface(1)
        >>> eth1 = test_node.interface(2)
        >>> str(eth0)
        'r1.r1 to sw1'
        >>> str(eth1)
        'r1.r1 to r2'
        """
        return self.__repr__()

    @property
    def _graph(self):
        """Return graph the node belongs to"""
        return self.nidb.raw_graph()

    @property
    def _node(self):
        """Return node the node belongs to

        >>> anm = autonetkit.topos.mixed()
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> test_node = nidb.node("r1")
        >>> loopback0 = test_node.interface(0)
        >>> loopback0._node
        {'Network': None, '_ports': {0: {'category': 'loopback', 'description': None}, 1: {'category': 'physical', 'description': 'r1 to sw1'}, 2: {'category': 'physical', 'description': 'r1 to r2'}, 3: {'category': 'physical', 'description': 'r1 to r3'}}, 'update': None, 'syntax': None, 'host': None, 'device_type': 'router', 'graphics': {'y': 300, 'x': 500, 'device_type': 'router', 'device_subtype': None}, 'asn': 1, 'device_subtype': None, 'label': 'r1', 'platform': None}
        """
        return self._graph.node[self.node_id]

    @property
    def _port(self):
        """Return graph the node belongs to

        >>> anm = autonetkit.topos.mixed()
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> test_node = nidb.node("r1")
        >>> loopback0 = test_node.interface(0)
        >>> loopback0._port
        {'category': 'loopback', 'description': None}
        """
        return self._node["_ports"][self.interface_id]

    @property
    def is_loopback(self):
        """

        >>> anm = autonetkit.topos.mixed()
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> test_node = nidb.node("r1")
        >>> loopback0 = test_node.interface(0)
        >>> loopback0.is_loopback
        True

        """
        return self.category == "loopback" or self.phy.category == "loopback"

    @property
    def is_physical(self):
        """
        >>> anm = autonetkit.topos.mixed()
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> test_node = nidb.node("r1")
        >>> eth0 = test_node.interface(1)
        >>> eth0.is_physical
        True
        """
        return self.category == "physical" or self.phy.category == "physical"

    @property
    def description(self):
        """
        >>> anm = autonetkit.topos.mixed()
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> test_node = nidb.node("r1")
        >>> eth0 = test_node.interface(1)
        >>> eth1 = test_node.interface(2)
        >>> eth0.description
        'r1 to sw1'
        >>> eth1.description
        'r1 to r2'

        """
        return self._port.get("description")

    @property
    def is_loopback_zero(self):
        """
        >>> anm = autonetkit.topos.mixed()
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> test_node = nidb.node("r1")
        >>> eth0 = test_node.interface(1)
        >>> loopback0 = test_node.interface(0)
        >>> loopback0.is_loopback_zero
        True
        >>> eth0.is_loopback_zero
        False
        """
        # by convention, loopback_zero is at id 0
        return self.interface_id == 0 and self.is_loopback

    @property
    def node(self):
        """Returns parent node of this interface

        >>> anm = autonetkit.topos.mixed()
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> test_node = nidb.node("r1")
        >>> eth0 = test_node.interface(1)
        >>> loopback0 = test_node.interface(0)
        >>> eth1 = test_node.interface(2)
        >>> eth0.node
        r1
        >>> eth1.node
        r1
        >>> loopback0.node
        r1

        """
        from autonetkit.nidb import DmNode
        return DmNode(self.nidb, self.node_id)

    def dump(self):
        """
        >>> anm = autonetkit.topos.mixed()
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> test_node = nidb.node("r1")
        >>> eth1 = test_node.interface(2)
        >>> eth1.dump()
        "[('category', 'physical'), ('description', 'r1 to r2')]"
        """
        return str(self._port.items())

    def dict(self):
        """Returns shallow copy of dictionary used.
        Note not a deep copy: modifying values may have impact

        >>> anm = autonetkit.topos.mixed()
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> test_node = nidb.node("r1")
        >>> eth0 = test_node.interface(1)
        >>> eth1 = test_node.interface(2)
        >>> eth1.dict()
        {'category': 'physical', 'description': 'r1 to r2'}
        >>> eth0.dict()
        {'category': 'physical', 'description': 'r1 to sw1'}
        """
        return dict(self._port.items())

    def __getattr__(self, key):
        """Returns interface property"""
        try:
            data = self._port.get(key)
        except KeyError:
            return

        if isinstance(data, dict):
            # TODO: use config stanza instead?
            return InterfaceDataDict(data)

        return data

    def get(self, key):
        """For consistency, node.get(key) is neater
        than getattr(interface, key)"""
        return getattr(self, key)

    def __setattr__(self, key, val):
        """Sets interface property"""
        try:
            self._port[key] = val
        except KeyError:
            self.set(key, val)

    def set(self, key, val):
        """For consistency, node.set(key, value) is neater
        than setattr(interface, key, value)"""
        return self.__setattr__(key, val)

    def edges(self):
        """Returns all edges from node that have this interface ID
        This is the convention for binding an edge to an interface

        >>> anm = autonetkit.topos.mixed()
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> test_node = nidb.node("r1")
        >>> eth0 = test_node.interface(1)
        >>> eth0.edges()
        [(r1, sw1, 0)]
        """
        # edges have raw_interfaces stored as a dict of {node_id: interface_id,
        # }
        valid_edges = [e for e in self.node.edges()
                       if self.node_id in e.raw_interfaces
                       and e.raw_interfaces[self.node_id] == self.interface_id]
        return valid_edges

    def neighbors(self):
        """Returns interfaces on nodes that are linked to this interface
        Can get nodes using [i.node for i in interface.neighbors()]

        >>> anm = autonetkit.topos.mixed()
        >>> nidb = autonetkit.DeviceModel(anm)
        >>> test_node = nidb.node("r1")
        >>> eth0 = test_node.interface(1)
        >>> eth0.neighbors()
        [sw1.sw1 to r1]
        """
        edges = self.edges()
        return [e.dst_int for e in edges]


class InterfaceDataDict(collections.MutableMapping):
    # TODO: replace with config stanza

    """A dictionary which allows access as dict.key as well as dict['key']
    Based on http://stackoverflow.com/questions/3387691
    only allows read only acess
    """

    def __repr__(self):
        return ", ".join(self.store.keys())

    def __init__(self, data):
        # Note this won't allow updates in place
        self.store = data
        #self.data = parent[index]
        # self.update(dict(*args, **kwargs)) # use the free update to set keys
# TODO: remove duplicate of self.store and parent

    def __getitem__(self, key):
        return self.store[self.__keytransform__(key)]

    def __setitem__(self, key, value):
        self.store[key] = value  # store locally

    def __delitem__(self, key):
        del self.store[self.__keytransform__(key)]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def __keytransform__(self, key):
        return key

    def __getattr__(self, key):
        return self.store.get(key)

    def __setattr__(self, key, value):
        if key == "store":
            object.__setattr__(self, 'store', value)
        else:
            self.store[key] = value  # store locally

    def dump(self):
        return self.store
