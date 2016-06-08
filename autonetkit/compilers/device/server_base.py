#!/usr/bin/python
# -*- coding: utf-8 -*-
from autonetkit.compilers.device.device_base import DeviceCompiler


class ServerCompiler(DeviceCompiler):
    def compile(self, node):
        # TODO: call this from parent
        node.do_render = True  # turn on rendering
        super(ServerCompiler, self).compile(node)
