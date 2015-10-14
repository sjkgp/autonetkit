class DeviceCompiler(object):

    def __init__(self, nidb, anm):
        """Base Router compiler"""
        self.nidb = nidb
        self.anm = anm

    def compile(self, node):
        node.do_render = True  # turn on rendering
        #TODO: refactor interfaces to go here - be careful - need to check against dependencies/ordering
        node.infrastructure_only = self.anm["phy"].data.infrastructure_only

    def interfaces(self, node):
        for interface in node.physical_interfaces():
            interface.physical = True
