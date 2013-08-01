from powerglove_dns.powerglove import PowergloveDns, PowergloveError

from test import PowergloveTestCase

class PowergloveUtilsTestCase(PowergloveTestCase):

    def setUp(self):

        super(PowergloveUtilsTestCase, self).setUp()
        self.powerglove = PowergloveDns(logger=self.log)

    def test_get_a_domain(self):
        """
        test that the correct domain can be inferred from a fully-qualified domain name
        """

        self.assertIn('tld', self.powerglove.domains)
        self.assertIn('stable.tld', self.powerglove.domains)
        self.assertIn('super.stable.tld', self.powerglove.domains)

        self.assertEqual(self.powerglove.get_a_domain_from_fqdn('host.tld').name, "tld")
        self.assertEqual(self.powerglove.get_a_domain_from_fqdn('host.super.tld').name, "tld")
        self.assertEqual(self.powerglove.get_a_domain_from_fqdn('host.super.great.tld').name, "tld")
        self.assertEqual(self.powerglove.get_a_domain_from_fqdn('host.super.stable.great.tld').name, "tld")
        self.assertEqual(self.powerglove.get_a_domain_from_fqdn('host.stable.tld').name, "stable.tld")
        self.assertEqual(self.powerglove.get_a_domain_from_fqdn('host.very.stable.tld').name, "stable.tld")
        self.assertEqual(self.powerglove.get_a_domain_from_fqdn('host.super.stable.tld').name, "super.stable.tld")
        self.assertEqual(self.powerglove.get_a_domain_from_fqdn('host.very.super.stable.tld').name, "super.stable.tld")

        with self.assertRaises(PowergloveError):
            self.powerglove.get_a_domain_from_fqdn('host.unknowntld')

    def test_get_ptr_domain(self):
        """
        test that we can infer the appriate PTR domain (if it even exists)
        """

        self.assertIn('10.10.in-addr.arpa', self.powerglove.domains)
        self.assertIn('10.in-addr.arpa', self.powerglove.domains)
        self.assertIn('132.168.192.in-addr.arpa', self.powerglove.domains)

        self.assertEqual(self.powerglove.get_ptr_domain_from_ptr_record_name('10.10.10.10.in-addr.arpa').name,
                         "10.10.in-addr.arpa")
        self.assertEqual(self.powerglove.get_ptr_domain_from_ptr_record_name('10.10.20.10.in-addr.arpa').name,
                         "10.in-addr.arpa")
        self.assertEqual(self.powerglove.get_ptr_domain_from_ptr_record_name('15.132.168.192.in-addr.arpa').name,
                         "132.168.192.in-addr.arpa")

        with self.assertRaises(PowergloveError):
            self.powerglove.get_ptr_domain_from_ptr_record_name('1.1.168.192.in-addr.arpa')
        with self.assertRaises(PowergloveError):
            self.powerglove.get_ptr_domain_from_ptr_record_name('1.0.0.127.in-addr.arpa')