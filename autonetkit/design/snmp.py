import autonetkit.ank as ank_utils
import autonetkit.log as log
from autonetkit.ank_utils import call_log

def default_snmp_cfg(node):

    node.snmp = {}
    node.snmp['enabled'] = True

    node.snmp['traps'] = []
    trap = {}
    trap['id'] = "link-down"
    trap['enabled'] = True
    node.snmp['traps'].append(trap)

    node.snmp['users'] = []
    user = {}
    user['user'] = "rag"
    user['grp'] = "admin"
    node.snmp['users'].append(user)

    node.snmp['communities'] = []
    community = {}
    community['name'] = "public"
    community['permission'] = "rw"
    node.snmp['communities'].append(community)

    node.snmp['servers'] = []
    server = {}
    server["ip"] = "172.168.22.112"
    server["version"] = 2
    server["udp_port"] = 162
    server["community"] = "public"
    node.snmp['servers'].append(server)


def build_snmp(anm):
    g_in = anm['input']

    snmp_nodes =[]
    for node in g_in:
        #This is based on the assumption that we will put a dictionary named 'config'
        #in node which will containg config for all protocols.
        if node.config is not None and node.config['snmp'] is not None:
            node.snmp = {}
            snmp_config = node.config['snmp']
            if 'enabled' in snmp_config:
                node.snmp['enabled'] = snmp_config['enabled']

            if 'traps' in snmp_config:
                node.snmp['traps'] = []
                for trap in snmp_config['traps']:
                    trap = dict(trap)
                    node.snmp['traps'].append(trap)

            if 'users' in snmp_config:
                node.snmp['users'] = []
                for user in snmp_config['users']:
                    user = dict(user)
                    node.snmp['users'].append(user)

            if 'communities' in snmp_config:
                node.snmp['communities'] = []
                for community in snmp_config['communities']:
                    community = dict(community)
                    node.snmp['communities'].append(community)

            if 'servers' in snmp_config:
                node.snmp['servers'] = []
                for server in snmp_config['servers']:
                    server = dict(server)
                    node.snmp['servers'].append(server)

        else:
            #do default config for POC
            default_snmp_cfg(node)

        snmp_nodes.append(node)

    g_snmp = anm.add_overlay("snmp")
    g_snmp.add_nodes_from(snmp_nodes, retain=['snmp'])