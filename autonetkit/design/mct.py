import autonetkit.ank as ank_utils
import autonetkit.log as log
import random
from autonetkit.ank_utils import call_log
from lag import configure_lag, default_lag_cfg, fill_lag_data

def fill_cluster_data(node1, node2):

    cluster_data_node1 = {}
    cluster_data_node1['id'] = random.randint(1, 65535)
    cluster_data_node1['name'] = node1.id + "_" + node2.id
    cluster_data_node1['session_vlan'] = random.randint(1, 4090)
    cluster_data_node1['member_vlan'] = random.randint(1, 4090)

    rbridge_id_node1 = random.randint(1, 35535)
    rbridge_id_node2 = random.randint(1, 35535)
    cluster_data_node1['rbridge_id'] = rbridge_id_node1
    cluster_data_node1['rbridge_id_peer'] = rbridge_id_node2
    cluster_data_node1['icl'] = node1.lag[0]['primary_port']
    cluster_data_node1['peer'] = []
    cluster_data_node1['peer'].append(node2)
    node1.mct.append(cluster_data_node1)

    cluster_data_node2 = {}
    cluster_data_node2['id'] = cluster_data_node1['id']
    cluster_data_node2['name'] = cluster_data_node1['name']
    cluster_data_node2['session_vlan'] = cluster_data_node1['session_vlan']
    cluster_data_node2['member_vlan'] = cluster_data_node1['member_vlan']
    cluster_data_node2['rbridge_id'] = rbridge_id_node2
    cluster_data_node2['rbridge_id_peer'] = rbridge_id_node1
    cluster_data_node2['icl'] = node2.lag[0]['primary_port']
    cluster_data_node2['peer'] = []
    cluster_data_node2['peer'].append(node1)
    node2.mct.append(cluster_data_node2)

def default_mct_cfg(anm):
    g_in = anm['input']

    mct_nodes = []
    list_nodes = []
    for node in g_in:
        list_nodes.append(node)

    for node in g_in:
        if node in list_nodes:
            neighbors = node.neighbors(asn=node.asn)
            for neighbor in neighbors:
                if neighbor in list_nodes:
                    if node.lag is None:
                        node.lag = []
                    if neighbor.lag is None:
                        neighbor.lag = []
                    #icl link
                    fill_lag_data(node, neighbor, lag_type="dynamic")
                    #cluster data
                    node.mct = []
                    neighbor.mct = []
                    fill_cluster_data(node, neighbor)
                    #client lag
                    fill_lag_data(node, None, lag_type="dynamic")
                    fill_lag_data(neighbor, None, lag_type="dynamic")
                    mct_nodes.append(node)
                    mct_nodes.append(neighbor)
                    list_nodes.remove(node)
                    list_nodes.remove(neighbor)
                    break

    return mct_nodes

def configure_mct(node):
    #This is based on the assumption that we will put a dictionary named 'config'
    #in node which will containg config for all protocols.
    if node.config is not None and node.config['mct'] is not None:
        mct_config = node.config['mct']
        node.mct = []
        for cluster_cfg in mct_config:
            cluster = {}
            if 'id' in cluster_cfg:
                cluster['id'] = cluster_cfg['id']

            if 'name' in cluster_cfg:
                cluster['name'] = cluster_cfg['name']

            if 'session_vlan' in cluster_cfg:
                cluster['session_vlan'] = cluster_cfg['session_vlan']

            if 'member_vlan' in cluster_cfg:
                cluster['member_vlan'] = cluster_cfg['member_vlan']

            if 'rbridge_id' in cluster_cfg:
                cluster['rbridge_id'] = cluster_cfg['rbridge_id']

            if 'rbridge_id_peer' in cluster_cfg:
                cluster['rbridge_id_peer'] = cluster_cfg['rbridge_id_peer']

            if 'icl' in cluster_cfg:
                cluster['icl'] = cluster_cfg['icl']

            node.mct.append(cluster)
        return node
    else:
        return None

def build_mct(anm):
    g_in = anm['input']

    mct_nodes =[]
    for node in g_in:
        temp_node = configure_mct(node)
        if temp_node is not None:
            mct_nodes.append(temp_node)

    #for POC add some mct config
    if not mct_nodes:
        mct_nodes = default_mct_cfg(anm)

    g_mct = anm.add_overlay("mct")
    g_mct.add_nodes_from(mct_nodes, retain=['mct'])
