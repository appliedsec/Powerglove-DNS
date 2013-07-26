from test import PowergloveTestCase
from powerglove_dns import main
from powerglove_dns.powerglove import PowergloveError
from powerglove_dns.model import Record

# this is either unittest2 or built-in unittest if >= py 2.7
from test import unittest


class PowergloveDNSCommandLineTestCase(PowergloveTestCase):

    def run_with_args(self, args):
        self.log.debug('about to run with: %r', args)
        return main(args, logger=self.log, session=self.Session)



    def test_sanity(self):
        """test the manually inserted items are indeed in the database"""

        self.assertRecordExists(type='A',
                                name=self.pdns.records.testing_a_132.name)
        self.assertRecordExists(type='A',
                                name=self.pdns.records.testing_a_133.name)
        self.assertRecordExists(type='PTR',
                                name=self.pdns.records.testing_ptr_132.name)
        self.assertRecordExists(type='PTR',
                                name=self.pdns.records.testing_ptr_133.name)
        self.assertRecordExists(type='A',
                                name=self.pdns.records.stable_a_134.name)
        self.assertRecordExists(type='A',
                                name=self.pdns.records.stable_a_135.name)
        self.assertRecordExists(type='PTR',
                                name=self.pdns.records.stable_ptr_134.name)
        self.assertRecordExists(type='PTR',
                                name=self.pdns.records.stable_ptr_135.name)

    def test_manual_command_line(self):
        """
        tests that the command line arguments can be manually called
        """

        with self.assertRaises(SystemExit):
            self.run_with_args(['-h'])

    def test_remove_cname_record(self):
        """
        tests that we're unable to remove a CNAME record
        """

        self.assertRecordExists(type='CNAME',
                                name=self.pdns.records.cname_record.name)
        self.run_with_args(['--remove', self.pdns.records.cname_record.name])

        self.assertRecordDoesNotExist(type='CNAME',
                                      name=self.pdns.records.cname_record.name)

    def test_unable_to_remove_record_with_cname(self):
        """
        tests that we're unable to remove an A records that has a cname
        associated with it
        """

        with self.assertRaises(PowergloveError):
            self.run_with_args(['--remove',
                                self.pdns.records.record_with_cname.name])
    def test_deleting_records_also_delete_text_records(self):
        """
        tests that deleting an A record with associated TXT record also deletes
        the TXT record
        """

        self.run_with_args(['--remove',
                            self.pdns.records.record_with_txt.name])
        self.assertRecordDoesNotExist(type='A',
                                  name=self.pdns.records.record_with_txt.name)
        self.assertRecordDoesNotExist(type='TXT',
                                  name=self.pdns.records.record_with_txt.name)
        self.assertRecordDoesNotExist(type='TXT',
                                      name=self.pdns.records.txt_record.name)
        self.assertRecordDoesNotExist(type='PTR',
                              content=self.pdns.records.record_with_txt.name)


    def test_remove_existing_hostname(self):
        """
        tests that removing a pre-existing host name is successful, and that no
        other records were touched
        """

        self.run_with_args(['--remove', self.pdns.records.stable_a_134.name])

        self.assertRecordExists(type='A',
                                name=self.pdns.records.testing_a_132.name)
        self.assertRecordExists(type='A',
                                name=self.pdns.records.testing_a_133.name)
        self.assertRecordExists(type='PTR',
                                name=self.pdns.records.testing_ptr_132.name)
        self.assertRecordExists(type='PTR',
                                name=self.pdns.records.testing_ptr_133.name)
        self.assertRecordDoesNotExist(type='A',
                                      name=self.pdns.records.stable_a_134.name)
        self.assertRecordExists(type='A',
                                name=self.pdns.records.stable_a_135.name)
        self.assertRecordDoesNotExist(type='PTR',
                                  name=self.pdns.records.stable_ptr_134.name)
        self.assertRecordExists(type='PTR',
                                name=self.pdns.records.stable_ptr_135.name)

    def test_adding_with_explicit_range(self):

        manual_ip = '192.168.135.101'
        next_ip = '192.168.135.102'
        self.add_and_test_new_hostname(['must_be_%s.stable.tld' % manual_ip,
                                        manual_ip, manual_ip],
                                       ip=manual_ip)
        self.add_and_test_new_hostname(['as_a_result_must_be_%s.stable.tld' % next_ip,
                                        manual_ip, next_ip], ip=next_ip)
        self.add_and_test_new_hostname(['whatever_basically.stable.tld',
                                        '192.168.132.1',
                                        '192.168.133.255'])
        self.add_and_test_new_hostname(['ip_already_reserved',
                                        manual_ip,
                                        next_ip],
                                       invalid=True)
        # it's supposed to lower higher, not higher, lower
        self.add_and_test_new_hostname(['invalid_explicit.test.tld', '192.168.132.150', '192.168.132.5'],
                                       invalid=True)


        with  self.assertRaises(AssertionError):
            self.add_and_test_new_hostname(['mismatched_ip.stable.tld',
                                            '192.168.135.62',
                                            '192.168.135.62'],
                                           ip='192.168.135.63')

    def test_add_and_deletes_with_explicit_range(self):

        manual_ip = '192.168.135.101'
        next_ip = '192.168.135.102'
        name = self.add_and_test_new_hostname(['must_be_%s.stable.tld' % manual_ip, manual_ip, manual_ip],
                                              ip=manual_ip, delete=True)
        self.assertRecordDoesNotExist(type='A', name=name)
        self.assertRecordDoesNotExist(type='PTR', content=name)
        name = self.add_and_test_new_hostname(['due_to_delete_is_still_%s.stable.tld' % manual_ip, manual_ip, next_ip],
                                              ip=manual_ip)
        self.assertRecordExists(type='A', name=name)
        self.assertRecordExists(type='PTR', content=name)

    def test_avoiding_invalid_addresses(self):

        self.add_and_test_new_hostname(['must_not_be_0_255_or_duplicate.test.tld', '192.168.132.255', '192.168.133.2'],
                                       invalid=True)
        self.add_and_test_new_hostname(['found_valid_address.test.tld', '192.168.132.255', '192.168.133.3'],
                                       ip='192.168.133.3')

    def test_duplicate_hostname(self):

        self.add_and_test_new_hostname(['brand_new_name.test.tld', '192.168.132.150', '192.168.132.151'])
        self.add_and_test_new_hostname(['brand_new_name.test.tld', '192.168.132.155', '192.168.132.156'], invalid=True)

    @unittest.expectedFailure
    def test_catching_ranges_outside_what_a_particular_domain_spans(self):

        # stable only is a 192.168.134/24 domain
        self.add_and_test_new_hostname(['in_the_range_of_testing.stable.tld', '192.168.132-133.*'], invalid=True)
        self.add_and_test_new_hostname(['outside_the_range.stable.tld', '192.168.132/22'], invalid=True)
        self.add_and_test_new_hostname(['outside_the_range.stable.tld', '192.168.132-135.*'], invalid=True)
        self.add_and_test_new_hostname(['bridges_the_domain.stable.tld', '192.168.133-134.*'], invalid=True)

    @unittest.expectedFailure
    def test_catching_ranges_outside_what_is_pdns(self):
        # this is WAAAAAAAAY too big
        self.add_and_test_new_hostname(['invalid_CIDR.test.tld', '192.168/2'], invalid=True)
        self.add_and_test_new_hostname(['invalid_IPGlob.test.tld', '192.168.*.*'], invalid=True)

    def test_adding_with_CIDR(self):

        self.add_and_test_new_hostname(['32_bit_mask.stable.tld', '192.168.135.100/32'])
        self.add_and_test_new_hostname(['23_bit_maskstable.tld', '192.168.132/23'])
        self.add_and_test_new_hostname(['23_bit_mask_same_domains.table.tld', '192.168.133/23'])

    def test_adding_with_IPGlob(self):

        self.add_and_test_new_hostname(['32_bit_mask.stable.tld', '192.168.135.100-101'])
        self.add_and_test_new_hostname(['23_bit_mask.stable.tld', '192.168.132-133.*'])

    def test_adding_with_explicit_ip(self):

        self.add_and_test_new_hostname(['hundred.stable.tld', '192.168.135.100'])
        self.add_and_test_new_hostname(['hundredone.stable.tld', '192.168.135.101'])
        self.add_and_test_new_hostname(['hundredone-dup.stable.tld', '192.168.135.101'], invalid=True)


    def test_creating_cname_for_existing_a_record(self):

        existing_fqdn = self.pdns.records.testing_a_132.name
        alias_fqdn = 'created_cname.test.tld'
        self.assertRecordExists(type='A', name=existing_fqdn)
        self.run_with_args(['--cname', alias_fqdn, existing_fqdn])
        self.assertRecordExists(type='CNAME',
                                name=alias_fqdn,
                                content=existing_fqdn)

    def test_for_presence_of_fqdn(self):
        """
        Tests that there is a simple command line argument for testing if a fully-qualified domain name is present in
        the A records
        """

        self.assertTrue(self.run_with_args(['--is_present',
                                        self.pdns.records.testing_a_132.name]))

        self.assertFalse(self.run_with_args(['--is_present',
                                             'nonexistant.fqdn']))

    def test_creation_of_text_record(self):
        """
        Tests that providing text record contents leads to the creation of an associated text record
        """
        text_record = 'test.thing.what'

        self.add_and_test_new_hostname(['record_with_associated_text.test.tld', '192.168.132.233',
                                        '--text', text_record])
        self.assertRecordExists(type='TXT', name='record_with_associated_text.test.tld',
                                content=text_record)


    def add_and_test_new_hostname(self, args, ip=None, invalid=False, delete=False, assertion=PowergloveError):
        """
        helper function for adding a new hostname using a variety of methods to specify ranges
        @arg hostname: the hostname of the machine to be added
        @arg args: the argument to be parsed and passed to the main function
        @arg ip: if specified, test that the resulting ip is equal to this value
        @raise RuntimeError: if there was an issue adding the hostname
        @raise AssertionError: if an assertion is failed
        """
        args = ['--add'] + args
        if invalid:
            with self.assertRaises(assertion):
                self.run_with_args(args)
        else:
            added_hostname, added_ip_address = self.run_with_args(args)
            a_record = self.getOneRecord(type='A', name=added_hostname)
            self.assertRecordExists(type='A', name=added_hostname)
            if ip is not None:
                self.assertRecordExists(type='PTR', content=added_hostname)
                self.assertEqual(ip, a_record.content)
            if delete:
                self.run_with_args(['--remove', added_hostname])
                self.assertRecordDoesNotExist(type='A', name=added_hostname)

            return added_hostname


    def test_unable_to_handle_no_range_or_domain(self):
        with self.assertRaises(PowergloveError) as cm:
            self.run_with_args(['--add', 'fall.down'])
        self.assertEqual(cm.exception.output, "unable to handle implicit mapping without a range or domain")
