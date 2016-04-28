import unittest
from cStringIO import StringIO
import sys
import ast
import autonetkit
from autonetkit.nidb import DmInterface


# redirect output if needed as suggested in
# http://stackoverflow.com/a/16571630/1629773
class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        sys.stdout = self._stdout


class TestDmNode(unittest.TestCase):
    def setUp(self):
        self.anm_house = autonetkit.topos.house()
        self.anm_mixed = autonetkit.topos.mixed()
        self.anm_multi = autonetkit.topos.multi_edge()

    def test_repr(self):
        nidb = autonetkit.DeviceModel(self.anm_house)
        r1 = nidb.node('r1')
        self.assertAlmostEqual(repr(r1), 'r1')

    def test_hash(self):
        nidb = autonetkit.DeviceModel(self.anm_house)
        r1 = nidb.node('r1')
        self.assertEqual(hash(r1), 14592087666131685)

    def test_eq(self):
        nidb = autonetkit.DeviceModel(self.anm_house)
        r1 = nidb.node('r1')
        rb = nidb.node('rb')
        self.assertIsNone(rb)
        rb = nidb.node('r1')
        self.assertEqual(r1, rb)

    def test_interface(self):
        nidb = autonetkit.DeviceModel(self.anm_house)
        r1 = nidb.node('r1')
        interface = r1.interface(1)
        self.assertIsInstance(interface, DmInterface)
        self.assertEqual(str(interface), 'r1.r1 to r2')

    def test_ports(self):
        nidb = autonetkit.DeviceModel(self.anm_house)
        r1 = nidb.node("r1")
        expected_result = {0: {'category': 'loopback', 'description': None},
                           1: {'category': 'physical', 'description': 'r1 to r2'},
                           2: {'category': 'physical', 'description': 'r1 to r3'}}
        self.assertDictEqual(expected_result, r1._ports)

    def test_next_int_id(self):
        nidb = autonetkit.DeviceModel(self.anm_house)
        r1 = nidb.node('r1')
        self.assertEqual(r1._next_int_id, 3)

    def test_add_interface(self):
        nidb = autonetkit.DeviceModel(self.anm_house)
        r1 = nidb.node('r1')
        interface = r1.add_interface()
        self.assertEqual(str(interface), 'r1.3')

    def test_interface_ids(self):
        nidb = autonetkit.DeviceModel(self.anm_house)
        r1 = nidb.node('r1')
        self.assertListEqual(r1._interface_ids, [0, 1, 2])
        r2 = nidb.node('r2')
        self.assertEqual(r2._interface_ids, [0, 1, 2, 3])

    def test_interfaces(self):
        nidb = autonetkit.DeviceModel(self.anm_house)
        r1 = nidb.node("r1")
        result = [str(i) for i in r1.interfaces]
        expected_result = ['r1.0', 'r1.r1 to r2', 'r1.r1 to r3']
        self.assertListEqual(expected_result, result)

    def test_physical_interfaces(self):
        nidb = autonetkit.DeviceModel(self.anm_house)
        r1 = nidb.node("r1")
        result = [str(i) for i in r1.physical_interfaces()]
        expected_result = ['r1.r1 to r2', 'r1.r1 to r3']
        self.assertListEqual(expected_result, result)

    def test_loopback_interfaces(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        r1 = nidb.node("r1")
        result = [str(i) for i in r1.loopback_interfaces()]
        self.assertListEqual(result, ['r1.0'])

    def test_loopback_zero(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        r1 = nidb.node("r1")
        self.assertEqual(str(r1.loopback_zero), 'r1.0')

    def test_raw_interfaces(self):
        nidb = autonetkit.DeviceModel(self.anm_house)
        r1 = nidb.node("r1")
        expected_result = {0: {'category': 'loopback', 'description': None},
                           1: {'category': 'physical', 'description': 'r1 to r2'},
                           2: {'category': 'physical', 'description': 'r1 to r3'}}
        self.assertDictEqual(r1.raw_interfaces, expected_result)

    def test_degree(self):
        nidb = autonetkit.DeviceModel(self.anm_house)
        r1 = nidb.node("r1")
        self.assertEqual(r1.degree(), 2)

    def test_neighbors(self):
        nidb = autonetkit.DeviceModel(self.anm_house)
        r1 = nidb.node("r1")
        r2 = nidb.node("r2")
        r3 = nidb.node("r3")
        self.assertListEqual(r1.neighbors(), [r2, r3])

    def test_lt(self):
        nidb = autonetkit.DeviceModel(self.anm_house)
        r1 = nidb.node("r1")
        r2 = nidb.node("r2")
        self.assertLess(r1,r2)

    def test_node_data(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        r1 = nidb.node("r1")
        expected_result = {'Network': None,
                           '_ports': {0: {'category': 'loopback', 'description': None},
                                                       1: {'category': 'physical', 'description': 'r1 to sw1'},
                                                       2: {'category': 'physical', 'description': 'r1 to r2'},
                                                       3: {'category': 'physical', 'description': 'r1 to r3'}},
                           'update': None,
                           'syntax': None,
                           'host': None,
                           'device_type': 'router',
                           'graphics': {'y': 300, 'x': 500,
                                        'device_type': 'router',
                                        'device_subtype': None},
                           'asn': 1,
                           'device_subtype': None,
                           'label': 'r1',
                           'platform': None}
        self.assertDictEqual(expected_result, r1._node_data)

    def test_dump(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        r1 = nidb.node("r1")
        expected_result = {'Network': None,
                           '_ports': {0: {'category': 'loopback', 'description': None},
                                      1: {'category': 'physical', 'description': 'r1 to sw1'},
                                      2: {'category': 'physical', 'description': 'r1 to r2'},
                                      3: {'category': 'physical', 'description': 'r1 to r3'}},
                           'asn': 1,
                           'device_subtype': None,
                           'device_type': 'router',
                           'graphics': {'device_subtype': None,
                                        'device_type': 'router',
                                        'x': 500,
                                        'y': 300},
                           'host': None,
                           'label': 'r1',
                           'platform': None,
                           'syntax': None,
                           'update': None}
        # capture output of dump function
        with Capturing() as output:
            r1.dump()
        # build from lines dict instance
        # reference: http://stackoverflow.com/a/988251/1629773
        result = ast.literal_eval(''.join(output))
        self.assertDictEqual(expected_result, result)



    def test_nonzero(self):
        nidb = autonetkit.DeviceModel(self.anm_house)
        r1 = nidb.node('r1')
        self.assertTrue(r1)

    def test_is_router(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        r1 = nidb.node('r1')
        self.assertTrue(r1.is_router())
        s1 = nidb.node("s1")
        self.assertFalse(s1.is_router())
        sw1 = nidb.node("sw1")
        self.assertFalse(sw1.is_router())

    def test_is_device_type(self):
        nidb = autonetkit.DeviceModel(self.anm_house)
        r1 = nidb.node('r1')
        self.assertTrue(r1.is_device_type('router'))
        self.assertFalse(r1.is_device_type('switch'))

    def test_is_switch(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        s1 = nidb.node("sw1")
        self.assertTrue(s1.is_switch())

    def test_is_server(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        r1 = nidb.node("r1")
        self.assertFalse(r1.is_server())

    def test_is_firewall(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        r1 = nidb.node("r1")
        self.assertFalse(r1.is_firewall())

    def test_is_l3device(self):
        nidb = autonetkit.DeviceModel(self.anm_mixed)
        r1 = nidb.node("r1")
        self.assertTrue(r1.is_l3device())

    def test_id(self):
        nidb = autonetkit.DeviceModel(self.anm_house)
        r1 = nidb.node("r1")
        self.assertEqual(r1.id, 'r1')

    def test_label(self):
        nidb = autonetkit.DeviceModel(self.anm_house)
        r1 = nidb.node("r1")
        self.assertEqual(r1.label, 'r1')

    def test_iter(self):
        nidb = autonetkit.DeviceModel(self.anm_house)
        r1 = nidb.node("r1")
        result = list(r1)
        expected_result = ['Network', '_ports', 'update',
                           'syntax', 'host', 'device_type',
                           'graphics', 'asn', 'device_subtype',
                           'label', 'platform']
        self.assertListEqual(expected_result, result)


if __name__ == '__main__':
    unittest.main()
