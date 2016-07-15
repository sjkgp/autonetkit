"""Compiler for Brocade"""
import os
import autonetkit
import autonetkit.config
import autonetkit.log as log
import autonetkit.plugins.naming as naming
from autonetkit.compilers.platform.platform_base import PlatformCompiler
import string
import itertools
import netaddr
from autonetkit.ank_utils import alphabetical_sort as alpha_sort
from autonetkit.compilers.device.brocade import BrocadeNICompiler
from autonetkit.nidb import ConfigStanza
from autonetkit.render2 import NodeRender, PlatformRender
from datetime import datetime


class BrocadeCompiler(PlatformCompiler):

    """Brocade Platform Compiler"""
    @staticmethod
    def numeric_to_interface_label_ni(x):
        """Starts at GigabitEthernet0/1 """
        x = x + 1
        return "Ethernet0/%s" % x

    @staticmethod
    def numeric_to_interface_label_linux(x):
        return "eth%s" % x

    @staticmethod
    def loopback_interface_ids():
        for x in itertools.count(100):  # start at 100 for secondary
            prefix = BrocadeNICompiler.lo_interface_prefix
            yield "%s%s" % (prefix, x)

    @staticmethod
    def interface_ids_ni():
        # TODO: make this skip if in list of allocated ie [interface.name for
        # interface in node]
        for x in itertools.count(0):
            yield "GigabitEthernet0/%s" % x

    @staticmethod
    def numeric_interface_ids():
        """#TODO: later skip interfaces already taken"""
        for x in itertools.count(0):
            yield x

    def compile(self):
        self.copy_across_ip_addresses()
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S_%f")
        dst_folder = os.path.join("rendered", self.host, timestamp, "brocade")

        log.info("Compiling Brocade for %s" % self.host)

        g_phy = self.anm['phy']
        mgmt_addr_block = netaddr.IPNetwork("192.168.0.0/24").iter_hosts()
        mgmt_addr_mask = (netaddr.IPNetwork("192.168.0.0/24")).netmask

# TODO: this should be all l3 devices not just routers
        for phy_node in g_phy.l3devices(host=self.host, syntax='brcd_ni'):
            loopback_ids = self.loopback_interface_ids()
            dm_node = self.nidb.node(phy_node)
            dm_node.add_stanza("render")

            #adding management interface by default
            dm_node.add_stanza('mgmt')
            dm_node.mgmt.ip = mgmt_addr_block.next()
            dm_node.mgmt.mask = mgmt_addr_mask

            #enabling telnet by default
            dm_node.add_stanza('telnet')
            dm_node.telnet = True
            for interface in dm_node.loopback_interfaces():
                if interface != dm_node.loopback_zero:
                    interface.id = loopback_ids.next()

            # Note this could take external data
            numeric_int_ids = self.numeric_interface_ids()
            g_in_node = self.anm['input'].node(phy_node)
            for interface in DmNode.physical_interfaces():
                phy_numeric_id = phy_node.interface(interface).numeric_id
                if phy_numeric_id is None:
                    # TODO: remove numeric ID code
                    interface.numeric_id = numeric_int_ids.next()
                else:
                    interface.numeric_id = int(phy_numeric_id)

                phy_specified_id = phy_node.interface(interface).specified_id
                if phy_specified_id is not None:
                    interface.id = phy_specified_id
                g_in_interface = g_in_node._ports[interface.interface_id]
                if 'is_member_lag' in g_in_interface:
                    interface.is_member_lag = True
                if 'is_primary_port' in g_in_interface:
                    interface.is_primary_port = True

        ni_compiler = BrocadeNICompiler(self.nidb, self.anm)
        for phy_node in g_phy.routers(host=self.host, syntax='brcd_ni'):
            dm_node = self.nidb.node(phy_node)
            dm_node.add_stanza("render")
            dm_node.render.template = os.path.join("templates", "brcd_ni.mako")
            dm_node.render.dst_folder = dst_folder
            dm_node.render.dst_file = "%s.conf" % naming.network_hostname(
                    phy_node)

            # Assign interfaces
            int_ids = self.interface_ids_ni()
            numeric_to_interface_label = self.numeric_to_interface_label_ni
            for interface in dm_node.physical_interfaces():
                if not interface.id:
                    interface.id = numeric_to_interface_label(
                        interface.numeric_id)

            dm_node.supported_features = ConfigStanza(
                mpls_te=False, mpls_oam=False, vrf=False)

            ni_compiler.compile(dm_node)
            # TODO: make this work other way around
