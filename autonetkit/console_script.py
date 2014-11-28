"""Console script entry point for AutoNetkit"""

import os
import sys
import time
import traceback
from datetime import datetime

import autonetkit.config as config
import autonetkit.log as log
import autonetkit.workflow as workflow
import pkg_resources

try:
    ANK_VERSION = pkg_resources.get_distribution("autonetkit").version
except pkg_resources.DistributionNotFound:
    ANK_VERSION = "dev"

def parse_options(argument_string=None):
    """Parse user-provided options"""
    import argparse
    usage = "autonetkit -f input.graphml"
    version = "%(prog)s " + str(ANK_VERSION)
    parser = argparse.ArgumentParser(description=usage, version=version)

    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        '--file', '-f', default=None, help="Load topology from FILE")
    input_group.add_argument('--stdin', action="store_true", default=False,
                             help="Load topology from STDIN")

    parser.add_argument(
        '--monitor', '-m', action="store_true", default=False,
        help="Monitor input file for changes")
    parser.add_argument('--debug', action="store_true",
                        default=False, help="Debug mode")
    parser.add_argument('--quiet', action="store_true",
                        default=False, help="Quiet mode (only display warnings and errors)")
    parser.add_argument('--diff', action="store_true", default=False,
                        help="Diff DeviceModel")
    parser.add_argument('--no_vis', dest="visualise",
        action="store_false", default=True,
        help="Visualise output")
    parser.add_argument('--compile', action="store_true",
                        default=False, help="Compile")
    parser.add_argument(
        '--build', action="store_true", default=False, help="Build")
    parser.add_argument(
        '--render', action="store_true", default=False, help="Compile")
    parser.add_argument(
        '--validate', action="store_true", default=False, help="Validate")
    parser.add_argument('--deploy', action="store_true",
                        default=False, help="Deploy")
    parser.add_argument('--archive', action="store_true", default=False,
                        help="Archive ANM, DeviceModel, and IP allocations")
    parser.add_argument('--measure', action="store_true",
                        default=False, help="Measure")
    parser.add_argument(
        '--webserver', action="store_true", default=False, help="Webserver")
    parser.add_argument('--grid', type=int, help="Grid Size (n * n)")
    parser.add_argument(
        '--target', choices=['netkit'], default=None)
    parser.add_argument(
        '--vis_uuid', default=None, help="UUID for multi-user visualisation")
    if argument_string:
        arguments = parser.parse_args(argument_string.split())
    else:
        # from command line arguments
        arguments = parser.parse_args()

    return arguments


class Runner(object):
    def __init__(self, options):
        self.options = options
        self.settings = config.settings
        if options.vis_uuid:
            config.settings['Http Post']['uuid'] = options.vis_uuid

        self.print_version()

        if options.debug or self.settings['General']['debug']:
            # TODO: fix this
            import logging
            logger = logging.getLogger("ANK")
            logger.setLevel(logging.DEBUG)

        if options.quiet or self.settings['General']['quiet']:
            import logging
            logger = logging.getLogger("ANK")
            logger.setLevel(logging.WARNING)

        self.init_build_options()

        if options.webserver:
            log.info("Webserver not yet supported, please run as seperate module")

        self.load_input()

    def print_version(self):
        log.info("AutoNetkit %s" % ANK_VERSION)

    def init_build_options(self):
        self.build_options = {
            'compile': self.options.compile or self.settings['General']['compile'],
            'render': self.options.render or self.settings['General']['render'],
            'validate': self.options.validate or self.settings['General']['validate'],
            'build': self.options.build or self.settings['General']['build'],
            'deploy': self.options.deploy or self.settings['General']['deploy'],
            'measure': self.options.measure or self.settings['General']['measure'],
            'monitor': self.options.monitor or self.settings['General']['monitor'],
            'diff': self.options.diff or self.settings['General']['diff'],
            'archive': self.options.archive or self.settings['General']['archive'],
            # use and for visualise as no_vis negates
            'visualise': self.options.visualise and self.settings['General']['visualise'],
        }

    def load_input(self):
        if self.options.file:
            with open(self.options.file, "r") as fh:
                self.input_string = fh.read()
            self.timestamp = os.stat(self.options.file).st_mtime
        elif self.options.stdin:
            self.input_string = sys.stdin
            now = datetime.now()
            self.timestamp = now.strftime("%Y%m%d_%H%M%S_%f")
        elif self.options.grid:
            self.input_string = ""
            now = datetime.now()
            self.timestamp = now.strftime("%Y%m%d_%H%M%S_%f")
        else:
            log.info("No input file specified. Exiting")
            raise Exception('No input specified')

    def load_network(self):
        if self.input_string:
            self.network = workflow.Network(self.input_string, self.timestamp,
                                            **self.build_options)
        elif self.options.grid:
            self.network = workflow.GridNetwork(self.options.grid,
                                                self.timestamp,
                                                **self.build_options)

    def run(self):
        try:
            self.load_network()
            self.network.configure()
        except Exception as err:
            log.exception('Error generating network configurations: %s. More '
                      'information may be available in the debug log.' % err)
            log.debug('Error generating network configurations', exc_info=True)
            if self.settings['General']['stack_trace']:
                print traceback.print_exc()
            sys.exit('Unable to build configurations.')

        # TODO: work out why build_options is being clobbered for monitor mode
        self.build_options['monitor'] = self.options.monitor or self.settings['General'][
            'monitor']

        if self.build_options['monitor']:
            try:
                log.info("Monitoring for updates...")
                input_filemonitor = workflow.file_monitor(self.options.file)
                #build_filemonitor = file_monitor("autonetkit/build_network.py")
                while True:
                    time.sleep(1)
                    rebuild = False
                    if input_filemonitor.next():
                        rebuild = True

                    if rebuild:
                        try:
                            log.info("Input graph updated, recompiling network")
                            with open(options.file, "r") as fh:
                                input_string = fh.read()  # read updates
                            self.network = workflow.Network(
                                self.input_string, self.timestamp,
                                **self.build_options)
                            self.network.configure()
                            log.info("Monitoring for updates...")
                        except Exception, e:
                            log.warning("Unable to build network %s" % e)
                            traceback.print_exc()

            except KeyboardInterrupt:
                log.info("Exiting")


def main(options):
    runner = Runner(options)
    runner.run()

def console_entry():
    """If come from console entry point"""
    args = parse_options()
    main(args)

if __name__ == "__main__":
    try:
        args = parse_options()
        main(args)
    except KeyboardInterrupt:
        pass
