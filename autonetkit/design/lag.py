import autonetkit.ank as ank_utils
import autonetkit.log as log
import random
from autonetkit.ank_utils import call_log

def fill_single_node_lag_data(node,lag_id = None, lag_name = None, lag_type = None, lag_max_num_port = None):

    lag = {}

    if lag_id is None:
        lag_id = random.randint(0, 500)

    if lag_name is None:
        lag_name = node.id + "_" + str(lag_id)

    if lag_type is None:
        lag_type = "static"
    if lag_max_num_port is None:
        lag_max_num_port = 2

    lag['name'] = lag_name
    lag['id'] = lag_id
    lag['type'] = lag_type

    port = None
    port_count = 0
    lag['ports'] = []
    for interface in node.physical_interfaces():
        if not interface.is_member_lag:
            port = str(interface.id)
            lag['ports'].append(port)
            interface.is_member_lag = True
            port_count = port_count + 1
            if port_count >=lag_max_num_port:
                break
    if port is not None:
        interface.is_primary_port = True
    lag['primary_port'] = port
    node.lag.append(lag)
    lag_dict = []
    lag_dict.append(lag)
    return lag

def fill_lag_data(node1, node2, lag_id = None, lag_name = None, lag_type = None, lag_max_num_port = None):

    if node2 is None:
        lag_dict = fill_single_node_lag_data(node1, lag_id = None, lag_name = None, lag_type = None, lag_max_num_port = None)
        return lag_dict

    lag1 = {}
    lag2 = {}

    if lag_id is None:
        lag_id = random.randint(0, 500)

    if lag_name is None:
        lag_name = node1.id + "_" + node2.id + "_" + str(lag_id)

    if lag_type is None:
        lag_type = "static"
    if lag_max_num_port is None:
        lag_max_num_port = 2

    lag1['name'] = lag2['name'] = lag_name
    lag1['id'] = lag2['id'] = lag_id
    lag1['type'] = lag2['type'] = lag_type

    port = None
    port_count = 0
    lag1['ports'] = []
    neighbor_interfaces = node2.neighbor_interfaces()
    for interface in neighbor_interfaces:
        if not interface.is_member_lag:
            if interface.node_id == node1.id:
                port = str(interface.id)
                lag1['ports'].append(port)
                interface.is_member_lag = True
                port_count = port_count + 1
                if port_count >=lag_max_num_port:
                    break
    if port is not None:
        interface.is_primary_port = True
    lag1['primary_port'] = port
    node1.lag.append(lag1)

    port = None
    lag2['ports'] = []
    port_count = 0
    neighbor_interfaces = node1.neighbor_interfaces()
    for interface in neighbor_interfaces:
        if not interface.is_member_lag:
            if interface.node_id == node2.id:
                port = str(interface.id)
                lag2['ports'].append(port)
                interface.is_member_lag = True
                port_count = port_count + 1
                if port_count >=lag_max_num_port:
                    break
    if port is not None:
        interface.is_primary_port = True
    lag2['primary_port'] = port

    node2.lag.append(lag2)
    lag_dict = []
    lag_dict.append(lag1)
    lag_dict.append(lag2)
    return lag_dict

def default_lag_cfg(anm):
    g_in = anm['input']

    lag_nodes = []
    list_nodes = []
    for node in g_in:
        list_nodes.append(node)

    for node in g_in:
        if node in list_nodes:
            neighbors = node.neighbors(asn=node.asn)
            print neighbors
            for neighbor in neighbors:
                if neighbor in list_nodes:
                    node.lag = []
                    neighbor.lag = []
                    fill_lag_data(node, neighbor)
                    #fill_lag_data(node, neighbor)
                    lag_nodes.append(node)
                    lag_nodes.append(neighbor)
                    list_nodes.remove(node)
                    list_nodes.remove(neighbor)
                    break

    return lag_nodes

def configure_lag(node):
    #This is based on the assumption that we will put a dictionary named 'config'
    #in node which will containg config for all protocols.
    if node.config is not None and node.config['lag'] is not None:
        lag_list = node.config['lag']
        node.lag = []
        for lag_config in lag_list:
            lag = {}
            if 'name' in lag_config:
                lag['name'] = lag_config['name']

            if 'type' in lag_config:
                lag['type'] = lag_config['type']

            if 'id' in lag_config:
                lag['id'] = lag_config['id']

            if 'ports' in lag_config:
                lag['ports'] = []
                for port in lag_config['ports']:
                    lag['ports'].append(port)

            if 'primary_port' in lag_config:
                lag['primary_port'] = lag_config['primary_port']

            node.lag.append(lag)
        return node
    else:
        return None

def build_lag(anm):
    g_in = anm['input']

    lag_nodes =[]
    for node in g_in:
        temp_node = configure_lag(node)
        if temp_node is not None:
            lag_nodes.append(temp_node)

    #for POC add some lag config
    if not lag_nodes:
        lag_nodes = default_lag_cfg(anm)

    g_lag = anm.add_overlay("lag")
    g_lag.add_nodes_from(lag_nodes, retain=['lag'])