#!/usr/bin/python
# -*- coding: utf-8 -*-
import os

import autonetkit
import autonetkit.ank_json as ank_json
import autonetkit.config as config
import autonetkit.log as log
import autonetkit.render as render
import autonetkit.build_network as build_network
from autonetkit.nidb import DeviceModel


import cProfile

# from https://zapier.com/engineering/profiling-python-boss/


def do_cprofile(func):
    def profiled_func(*args, **kwargs):
        profile = cProfile.Profile()
        try:
            profile.enable()
            result = func(*args, **kwargs)
            profile.disable()
            return result
        finally:
            # profile.print_stats()
            profile.dump_stats("profile")
    return profiled_func


def file_monitor(filename):
    """Generator based function to check if a file has changed"""

    last_timestamp = os.stat(filename).st_mtime

    while True:
        timestamp = os.stat(filename).st_mtime
        if timestamp > last_timestamp:
            last_timestamp = timestamp
            yield True
        yield False


class NoneCompiler:
    def __init__(self, platform):
        self.platform = platform
    def compile(self):
        raise Exception('No compiler for platform "%s"' %
                        self.platform)


class Network(object):
    def __init__(self, graph_string, timestamp, **kwargs):
        self.graph_def = graph_string
        self.should_build = kwargs.get('build', True)
        self.should_visualise = kwargs.get('visualise', True)
        self.should_compile = kwargs.get('compile', True)
        self.should_validate = kwargs.get('validate', True)
        self.should_render = kwargs.get('render', True)
        self.should_monitor = kwargs.get('monitor', True)
        self.should_deploy = kwargs.get('deploy', True)
        self.should_measure = kwargs.get('measure', True)
        self.should_diff = kwargs.get('diff', True)
        self.should_archive = kwargs.get('archive', True)

    def load(self):
        self.graph = build_network.load(self.graph_def)

    def select_platform_compiler(self, host, platform, print_log=True):
        if platform == 'netkit':
            import autonetkit.compilers.platform.netkit as pl_netkit
            platform_compiler = pl_netkit.NetkitCompiler(self.nidb, self.anm,
                                                         host)
        elif platform == 'dynagen':
            import autonetkit.compilers.platform.dynagen as pl_dynagen
            platform_compiler = pl_dynagen.DynagenCompiler(self.nidb, self.anm,
                                                           host)
        elif platform == 'junosphere':
            import autonetkit.compilers.platform.junosphere as pl_junosphere
            platform_compiler = pl_junosphere.JunosphereCompiler(
                self.nidb, self.anm, host)
        else:
            platform_compiler = NoneCompiler(platform)
            if print_log:
                log.warning('Unknown platform "%s"' % platform)
        return platform_compiler

    #@do_cprofile
    def compile_network(self):
        # log.info("Creating base network model")
        self.nidb = create_nidb(self.anm)
        g_phy = self.anm['phy']
        # log.info("Compiling to targets")

        for target_data in config.settings['Compile Targets'].values():
            host, platform = target_data['host'], target_data['platform']
            platform_compiler = self.select_platform_compiler(host, platform)

            if any(g_phy.nodes(host=host, platform=platform)):
                # log.info('Compiling configurations for %s on %s'
                         # % (platform, host))
                platform_compiler.compile()  # only compile if hosts set
            else:
                log.debug('No devices set for %s on %s' % (platform, host))
        return self.nidb

    def configure(self):
        if self.should_build:
            self.load()
            # TODO: integrate the code to visualise on error (enable in config)
            self.anm = None
            try:
                self.anm = build_network.build(self.graph)
            except Exception, e:
                # Send the visualisation to help debugging
                try:
                    if self.should_visualise:
                        import autonetkit
                        autonetkit.update_vis(self.anm)
                except Exception, e:
                    # problem with vis -> could be coupled with original exception -
                    # raise original
                    log.warning("Unable to visualise: %s" % e)
                raise  # raise the original exception
            else:
                if self.should_visualise:
                    # log.info("Visualising network")
                    import autonetkit
                    autonetkit.update_vis(self.anm)

            if not compile:
                # autonetkit.update_vis(self.anm)
                pass

            if self.should_validate:
                import autonetkit.ank_validate
                try:
                    autonetkit.ank_validate.validate(self.anm)
                except Exception, e:
                    log.warning('Unable to validate topologies: %s' % e)
                    log.debug('Unable to validate topologies',
                              exc_info=True)

        if compile:
            if self.should_archive:
                self.anm.save()
            self.nidb = self.compile_network()
            autonetkit.update_vis(self.anm, self.nidb)

            #autonetkit.update_vis(self.anm, self.nidb)
            log.debug('Sent ANM to web server')
            if self.should_archive:
                self.nidb.save()

            # render.remove_dirs(["rendered"])

            if render:
                #import time
                #start = time.clock()
                autonetkit.render.render(self.nidb)
                # print time.clock() - start
                #import autonetkit.render2
                #start = time.clock()
                # autonetkit.render2.render(self.nidb)
                # print time.clock() - start

        if not (self.should_build or compile):

            # Load from last run

            import autonetkit.anm
            self.anm = autonetkit.anm.NetworkModel()
            self.anm.restore_latest()
            self.nidb = DeviceModel()
            self.nidb.restore_latest()
            #autonetkit.update_vis(self.anm, self.nidb)

        if self.should_diff:
            import autonetkit.diff
            nidb_diff = autonetkit.diff.nidb_diff()
            import json
            data = json.dumps(nidb_diff, cls=ank_json.AnkEncoder, indent=4)
            # log.info('Wrote diff to diff.json')

            # TODO: make file specified in config

            with open('diff.json', 'w') as fh:
                fh.write(data)

        if self.should_deploy:
            deploy_network(self.anm, self.nidb, self.graph_def)

        log.info('Configuration engine completed')  # TODO: finished what?


class GridNetwork(Network):
    def load(self):
        self.graph = build_network.grid_2d(self.graph_def)


def create_nidb(anm):

    # todo: refactor this now with the layer2/layer2_bc graphs - what does nidb need?
    # probably just layer2, and then allow compiled to access layer2_bc if
    # need (eg netkit?)

    nidb = DeviceModel(anm)


    return nidb


def deploy_network(anm, nidb, input_graph_string=None):

    # log.info('Deploying Network')

    deploy_hosts = config.settings['Deploy Hosts']
    for (hostname, host_data) in deploy_hosts.items():
        for (platform, platform_data) in host_data.items():
            if not any(nidb.nodes(host=hostname, platform=platform)):
                log.debug('No hosts for (host, platform) (%s, %s), skipping deployment'
                          % (hostname, platform))
                continue

            if not platform_data['deploy']:
                log.debug('Not deploying to %s on %s' % (platform,
                                                         hostname))
                continue

            config_path = os.path.join('rendered', hostname, platform)
            username = platform_data['username']
            key_file = platform_data['key_file']
            host = platform_data['host']

            if platform == 'netkit':
                import autonetkit.deploy.netkit as netkit_deploy
                tar_file = netkit_deploy.package(config_path, 'nklab')
                netkit_deploy.transfer(host, username, tar_file,
                                       tar_file, key_file)
                netkit_deploy.extract(
                    host,
                    username,
                    tar_file,
                    config_path,
                    timeout=60,
                    key_filename=key_file,
                    parallel_count=10,
                )
