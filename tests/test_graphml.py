import os
import logging
import pkg_resources

import autonetkit.console_script as console_script
import autonetkit.log as log
import autonetkit
import autonetkit.load.graphml as graphml

# stdio redirect from stackoverflow.com/q/2654834

#TODO: add feature that reports if only IP addresses have changed: match the diff to an IP regex


def resource_path(relative):
    return pkg_resources.resource_filename(__name__, relative)


def compare_output_expected(topology_name):
    import difflib

    message = ''

    log.info("Testing %s" % topology_name)
    input_filename = "%s.graphml" % topology_name

    dirname, filename = os.path.split(os.path.abspath(__file__))
    input_file = os.path.join(dirname, input_filename)

    arg_string = "-f %s --quiet --render" % input_file
    args = console_script.parse_options(arg_string)
    console_script.main(args)

    #: set log level back to INFO because --quit it turns down to WARNING
    log.ank_logger.setLevel(logging.INFO)

    #: load expected structure
    topology_expected_dir_name = topology_name + '_output'
    topology_expected_dir = resource_path(topology_expected_dir_name)
    topology_output_dir = os.path.join(os.path.dirname(os.path.dirname(autonetkit.__file__)), 'rendered')

    differences_found = False

    #: compare each file from expected dir to file in output directory
    for root, dirs, files in os.walk(topology_expected_dir):
        for file in files:
            exp_file_path = os.path.join(root, file)
            exp_file_relpath = os.path.relpath(exp_file_path, topology_expected_dir)
            output_file_path  = os.path.join(topology_output_dir, exp_file_relpath)
            with open(exp_file_path, "r") as fh:
                expected_result = fh.read()
            with open(output_file_path, "r") as fh:
                output_result = fh.read()
            expected_lines = expected_result.splitlines()
            output_lines = output_result.splitlines()

            #remove line with version and time stamp
            if file == 'motd.txt':
                expected_lines = expected_lines[2:]
                output_lines = output_lines[2:]

            diff = difflib.context_diff(expected_lines, output_lines, n=0)
            diff = "\n".join(diff)
            if len(diff) > 0:
                differences_found = True
                # print diff
                diff_with_context = difflib.context_diff(
                        expected_lines, output_lines, n=3)
                diff_with_context = "\n".join(diff_with_context)
                message += " Change in config %s: %s" % (
                    exp_file_relpath, diff_with_context)
                log.warning(message)
            else:
                log.info("Verified: %s", exp_file_relpath)

    if differences_found:
        raise AssertionError("Failed: %s" % topology_name)

    log.info("Verified topology %s" % topology_name)


topologies = [
    "small_internet",
    "Aarnet",
    "multigraph",
]


# special case testing
def build_anm(topology_name):
    print "Building anm for %s" % topology_name
    dirname, filename = os.path.split(os.path.abspath(__file__))
    input_filename = os.path.join(dirname, "%s.graphml" % topology_name)

    anm =  autonetkit.NetworkModel()
    input_graph = graphml.load_graphml(input_filename)

    import autonetkit.build_network as build_network
    anm = build_network.initialise(input_graph)
    applicator = build_network.DesignRulesApplicator(anm)
    anm = applicator.design()
    return anm


def test():
    anm = build_anm("blank_labels")
    actual_labels = sorted(anm['phy'].nodes())
    expected_labels = ["none___0", "none___1", "none___2"]
    assert(actual_labels == expected_labels)

    anm = build_anm("duplicate_labels")
    actual_labels = sorted(anm['phy'].nodes())
    expected_labels = ["none___0", "none___1", "none___2"]
    #TODO: need to log this as a bug
    #assert(actual_labels == expected_labels)

    anm = build_anm("asn_zero")
    actual_asns = [n.asn for n in anm['phy']]
    expected_asns = [1, 1, 1]
    assert(actual_asns == expected_asns)


def test_topologies():
    for topology in topologies:
        yield compare_output_expected, topology


automated = True # whether to open ksdiff, log to file... currently not used
if __name__ == "__main__":
    automated = False
    for topology in topologies:
        print "Testing topology", topology
        compare_output_expected(topology)
