import unittest
import autonetkit


class TestNmNode(unittest.TestCase):

    def setUp(self):
        self.anm_house = autonetkit.topos.house()
        self.anm_mixed = autonetkit.topos.mixed()
        self.anm_multi = autonetkit.topos.multi_edge()

    def test_hash(self):
        r1 = self.anm_house['phy'].node("r1")
        self.assertEqual(hash(r1), 14592087666131685)

    def test_nonzero(self):
        r1 = self.anm_house['phy'].node("r1")
        self.assertTrue(r1)
        r_test = self.anm_house['phy'].node("test")
        self.assertFalse(r_test)

    def test_iter(self):
        r1 = self.anm_house['phy'].node("r1")
        res = [str(i) for i in list(r1)]
        self.assertListEqual(res, ['eth0.r1', 'eth1.r1'])

    def test_len(self):
        r1 = self.anm_house['phy'].node("r1")
        self.assertEqual(len(r1), 2)
        r2 = self.anm_house['phy'].node("r2")
        self.assertEqual(len(r2), 3)

    def test_eq(self):
        r1 = self.anm_house['phy'].node("r1")
        rb = self.anm_house['phy'].node("r1")
        self.assertEqual(r1, rb)
        r2 = self.anm_house['phy'].node("r2")
        # assertNotEqual calls __ne__ of NmNode, therefore use assertEqual here
        self.assertFalse(r1 == r2)
        self.assertEqual(r1, "r1")
        self.assertFalse(r1 == "r2")

    def test_ne(self):
        r1 = self.anm_house['phy'].node("r1")
        r2 = self.anm_house['phy'].node("r2")
        self.assertNotEqual(r1, r2)

    def test_loopback_zero(self):
        r1 = self.anm_house['phy'].node("r1")
        lo_zero = r1.loopback_zero
        # TODO: what should we test?

    def test_physical_interfaces(self):
        r1 = self.anm_mixed['phy'].node("r1")
        result = [str(i) for i in r1.physical_interfaces()]
        expected_result = ['eth0.r1', 'eth1.r1', 'eth2.r1']
        self.assertListEqual(expected_result, result)
        #TODO: add test with args and kwargs too

    def test_is_multigraph(self):
        r1 = self.anm_mixed['phy'].node("r1")
        self.assertFalse(r1.is_multigraph())
        r1 = self.anm_multi['phy'].node("r1")
        self.assertTrue(r1.is_multigraph())

    def test_lt(self):
        r1 = self.anm_house['phy'].node("r1")
        r2 = self.anm_house['phy'].node("r2")
        self.assertLess(r1, r2)
        self.assertFalse(r2<r1)

    def test_next_int_id(self):
        r1 = self.anm_house['phy'].node("r1")
        self.assertEqual(r1._next_int_id(), 3)

    def test_add_interface(self):
        r1 = self.anm_house['phy'].node("r1")
        self.assertEqual(r1._add_interface(), 3)

    def test_interface(self):
        r1 = self.anm_mixed['phy'].node("r1")
        self.assertEqual(str(r1.interface("eth0")), 'eth0.r1')

    def test_interface_ids(self):
        r1 = self.anm_mixed['phy'].node("r1")
        expected_result = [0, 1, 2, 3]
        self.assertListEqual(r1._interface_ids(), expected_result)

    def test_ports(self):
        r1 = self.anm_mixed['phy'].node("r1")
        expected_result = {0: {'category': 'physical', 'description': None},
                           1: {'category': 'physical', 'description': 'r1 to sw1', 'id': 'eth0'},
                           2: {'category': 'physical', 'description': 'r1 to r2', 'id': 'eth1'},
                           3: {'category': 'physical', 'description': 'r1 to r3', 'id': 'eth2'}}
        self.assertDictEqual(expected_result, r1._ports)

    def test_is_router(self):
        r1 = self.anm_mixed['phy'].node("r1")
        self.assertTrue(r1.is_router())
        s1 = self.anm_mixed['phy'].node("s1")
        self.assertFalse(s1.is_router())
        sw1 = self.anm_mixed['phy'].node("sw1")
        self.assertFalse(sw1.is_router())

    def test_is_firewall(self):
        r1 = self.anm_mixed['phy'].node("r1")
        self.assertTrue(r1.is_router())
        s1 = self.anm_mixed['phy'].node("s1")
        self.assertFalse(s1.is_router())
        sw1 = self.anm_mixed['phy'].node("sw1")
        self.assertFalse(sw1.is_router())

    def test_is_switch(self):
        r1 = self.anm_mixed['phy'].node("r1")
        self.assertFalse(r1.is_switch())
        s1 = self.anm_mixed['phy'].node("s1")
        self.assertFalse(s1.is_switch())
        sw1 = self.anm_mixed['phy'].node("sw1")
        self.assertTrue(sw1.is_switch())

    def test_is_server(self):
        r1 = self.anm_mixed['phy'].node("r1")
        self.assertFalse(r1.is_server())
        s1 = self.anm_mixed['phy'].node("s1")
        self.assertTrue(s1.is_server())
        sw1 = self.anm_mixed['phy'].node("sw1")
        self.assertFalse(sw1.is_server())

    def test_is_l3device(self):
        r1 = self.anm_mixed['phy'].node("r1")
        self.assertTrue(r1.is_l3device())
        s1 = self.anm_mixed['phy'].node("s1")
        self.assertTrue(s1.is_l3device())
        sw1 = self.anm_mixed['phy'].node("sw1")
        self.assertFalse(sw1.is_l3device())

    def test_raw_interfaces(self):
        r1 = self.anm_house['phy'].node("r1")
        expected_result = {0: {'category': 'physical', 'description': None},
                           1: {'category': 'physical', 'description': 'r1 to r2', 'id': 'eth0'},
                           2: {'category': 'physical', 'description': 'r1 to r3', 'id': 'eth1'}}
        self.assertDictEqual(expected_result, r1.raw_interfaces)

    def test_asn(self):
        r1 = self.anm_house['phy'].node("r1")
        self.assertEqual(r1.asn,1)
        r5 = self.anm_house['phy'].node("r5")
        self.assertEqual(r5.asn, 2)

    def test_id(self):
        r1 = self.anm_house['phy'].node("r1")
        self.assertEqual(r1.id, 'r1')

    def test_degree(self):
        r1 = self.anm_house['phy'].node("r1")
        self.assertEqual(r1.degree(), 2)
        r2 = self.anm_house['phy'].node("r2")
        self.assertEqual(r2.degree(), 3)

    def test_neighbors(self):
        r1 = self.anm_house['phy'].node("r1")
        result = [str(n) for n in r1.neighbors()]
        expected_result = ['r2', 'r3']
        self.assertListEqual(expected_result, result)
        r2 = self.anm_house['phy'].node("r2")
        result = [str(n) for n in r2.neighbors()]
        expected_result = ['r4', 'r1', 'r3']
        self.assertListEqual(expected_result, result)
        result = [str(n) for n in r2.neighbors(asn=1)]
        expected_result = ['r1', 'r3']
        self.assertListEqual(expected_result, result)
        result = [str(n) for n in r2.neighbors(asn=2)]
        expected_result = ['r4']
        self.assertListEqual(expected_result, result)

    def test_neighbor_interfaces(self):
        r1 = self.anm_house['phy'].node("r1")
        result = [str(n) for n in r1.neighbor_interfaces()]
        expected_result = ['eth0.r2', 'eth0.r3']
        self.assertListEqual(expected_result, result)
        r2 = self.anm_house['phy'].node("r2")
        result = [str(n) for n in r2.neighbor_interfaces()]
        expected_result = ['eth0.r4', 'eth0.r1', 'eth1.r3']
        self.assertListEqual(expected_result, result)

    def test_label(self):
        r1 = self.anm_house['phy'].node("r1")
        self.assertEqual(r1.label, 'r1')

    def test_dump(self):
        r1 = self.anm_house['phy'].node("r1")
        expected_result = "{'device_type': 'router', 'y': 400, 'x': 350, 'asn': 1, 'label': 'r1'}"
        self.assertEqual(expected_result, r1.dump())

    def test_edges(self, *args, **kwargs):
        r1 = self.anm_house['phy'].node("r1")
        r2 = self.anm_house['phy'].node("r2")
        r3 = self.anm_house['phy'].node("r3")
        r4 = self.anm_house['phy'].node("r4")
        result = r1.edges()
        expected_result = [(r1, r2), (r1, r3)]
        self.assertListEqual(expected_result, result)
        result = r2.edges()
        expected_result = [(r2, r4), (r2, r1), (r2, r3)]
        self.assertListEqual(expected_result, result)

    def test_repr(self):
        r1 = self.anm_house['phy'].node("r1")
        self.assertEqual(r1.__repr__(), 'r1')

    def test_get(self):
        r1 = self.anm_house['phy'].node("r1")
        self.assertEqual(r1.get('asn'),1)
        self.assertIsNone(r1.get('nonexistent attr'))
        self.assertEqual(r1.get('device_type'), 'router')

    def test_set(self):
        r1 = self.anm_house['phy'].node("r1")
        color = 'red'
        r1.set('color', color)
        self.assertEqual(r1.get('color'), color)
        asn = 2
        r1.set('asn', asn)
        self.assertEqual(r1.get('asn'), asn)


#if __name__ == '__main__':
#    unittest.main()
