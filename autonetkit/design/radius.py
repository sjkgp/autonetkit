import autonetkit.ank as ank_utils
import autonetkit.log as log
from autonetkit.ank_utils import call_log

def default_radius_cfg(node):
    node.radius ={}
    node.radius['servers'] = []
    server ={}
    server['auth_port'] = 1812
    server['acct_port'] = 1813
    server['key'] = "!$%^&*"
    server['ip'] = "192.168.101.11"
    node.radius['servers'].append(server)

def build_radius(anm):
    g_in = anm['input']

    radius_nodes =[]
    for node in g_in:
        #This is based on the assumption that we will put a dictionary named 'config'
        #in node which will containg config for all protocols.
        if node.config is not None and node.config['radius'] is not None:
            node.radius = {}
            radius_config = node.config['radius']

            if 'servers' in radius_config:
                node.radius['servers'] = []
                for server in radius_config['servers']:
                    server = dict(server)
                    node.radius['servers'].append(server)

        else:
            #do default config for POC
            default_radius_cfg(node)

        radius_nodes.append(node)

    g_radius = anm.add_overlay("radius")
    g_radius.add_nodes_from(radius_nodes, retain=['radius'])
