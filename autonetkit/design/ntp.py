import autonetkit.ank as ank_utils
import autonetkit.log as log
from autonetkit.ank_utils import call_log

def default_ntp_cfg(node):
    node.ntp = {}
    node.ntp['servers'] = []
    server = {}
    server['key'] = "@#$%%^&*"
    server['ip'] = "192.168.101.12"
    node.ntp['servers'].append(server)

def build_ntp(anm):
    g_in = anm['input']


    ntp_nodes =[]
    for node in g_in:
        #This is based on the assumption that we will put a dictionary named 'config'
        #in node which will containg config for all protocols.
        if node.config is not None and node.config['ntp'] is not None:
            node.ntp = {}
            ntp_config = node.config['ntp']

            if 'servers' in ntp_config:
                node.ntp['servers'] = []
                for server in ntp_config['servers']:
                    server = dict(server)
                    node.ntp['servers'].append(server)

        else:
            #do default config for POC
            default_ntp_cfg(node)

        ntp_nodes.append(node)

    g_ntp = anm.add_overlay("ntp")
    g_ntp.add_nodes_from(ntp_nodes, retain=['ntp'])
