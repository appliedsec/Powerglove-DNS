from powerglove_dns.powerglove import PowergloveDns, PowergloveError

from test import PowergloveTestCase

class PowergloveUtilsTestCase(PowergloveTestCase):

    def setUp(self):

        super(PowergloveUtilsTestCase, self).setUp()
        self.powerglove = PowergloveDns(session=self.Session, logger=self.log)

    def test_get_domain(self):
        """
        test that the correct domain can be inferred from a fully-qualified domain name
        """

        self.assertIn('tld', self.powerglove.domains)
        self.assertIn('stable.tld', self.powerglove.domains)
        self.assertIn('super.stable.tld', self.powerglove.domains)

        self.assertEqual(self.powerglove.get_domain('host.tld').name, "tld")
        self.assertEqual(self.powerglove.get_domain('host.super.tld').name, "tld")
        self.assertEqual(self.powerglove.get_domain('host.super.great.tld').name, "tld")
        self.assertEqual(self.powerglove.get_domain('host.super.stable.great.tld').name, "tld")
        self.assertEqual(self.powerglove.get_domain('host.stable.tld').name, "stable.tld")
        self.assertEqual(self.powerglove.get_domain('host.very.stable.tld').name, "stable.tld")
        self.assertEqual(self.powerglove.get_domain('host.super.stable.tld').name, "super.stable.tld")
        self.assertEqual(self.powerglove.get_domain('host.very.super.stable.tld').name, "super.stable.tld")

        with self.assertRaises(PowergloveError):
            self.powerglove.get_domain('host.unknowntld')

    def test_get_domain(self):
        """
        test that the correct domain can be inferred from a fully-qualified domain name
        """

        self.assertIn('tld', self.powerglove.domains)
        self.assertIn('stable.tld', self.powerglove.domains)
        self.assertIn('super.stable.tld', self.powerglove.domains)

        self.assertEqual(self.powerglove.get_domain('host.tld').name, "tld")
        self.assertEqual(self.powerglove.get_domain('host.super.tld').name, "tld")
        self.assertEqual(self.powerglove.get_domain('host.super.great.tld').name, "tld")
        self.assertEqual(self.powerglove.get_domain('host.super.stable.great.tld').name, "tld")
        self.assertEqual(self.powerglove.get_domain('host.stable.tld').name, "stable.tld")
        self.assertEqual(self.powerglove.get_domain('host.very.stable.tld').name, "stable.tld")
        self.assertEqual(self.powerglove.get_domain('host.super.stable.tld').name, "super.stable.tld")
        self.assertEqual(self.powerglove.get_domain('host.very.super.stable.tld').name, "super.stable.tld")

        with self.assertRaises(PowergloveError):
            self.powerglove.get_domain('host.unknowntld')