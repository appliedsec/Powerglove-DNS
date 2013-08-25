from test import PowergloveTestCase
from powerglove_dns import main
from powerglove_dns.powerglove import PowergloveError
from powerglove_dns.model import Record

# this is either unittest2 or built-in unittest if >= py 2.7
from test import unittest, setup_mock_pdns


class PowergloveDNSCommandLineTestCase(PowergloveTestCase):

    def run_with_args(self, args):
        self.log.debug('about to run with: %r', args)
        return main(args, logger=self.log)

    def test_passing_sqla_url_on_the_command_line_overrides_config_file(self):
        """
        if a user passing an sqla connection string on the command,
        it should be preferentially used over a config file
        """
        # using the normal, mocked configuration file
        self.assertTrue(self.run_with_args(['--is_present', self.pdns.records.testing_a_133.name]))
        self.add_and_test_new_hostname(['sanity_check.tld', '10.10.*.*'])
        self.assertTrue(self.run_with_args(['--is_present', 'sanity_check.tld']))
        # we can also use the exact same connect string as what is in the config file
        self.assertTrue(self.run_with_args(['--pdns_connect_string', self.original_sqla_connect_string,
                                            '--is_present', self.pdns.records.testing_a_133.name]))
        self.assertTrue(self.run_with_args(['--pdns_connect_string', self.original_sqla_connect_string,
                                            '--is_present', self.pdns.records.testing_a_133.name]))

        new_connect_string = 'sqlite:///%s' % self.get_temporary_file().name
        self.log.debug('setting up a new PDNS test location at %s', new_connect_string)
        # we've now setup this new, other PDNS installation to a new place
        setup_mock_pdns(self.get_session_from_connect_string(new_connect_string)())
        self.assertTrue(self.run_with_args(['--pdns_connect_string', new_connect_string,
                                            '--is_present', self.pdns.records.testing_a_133.name]))
        # this is still using the original SQLite database, so it works
        self.assertTrue(self.run_with_args(['--is_present', 'sanity_check.tld']))
        # this is using the overridden value, so it doesn't
        self.assertFalse(self.run_with_args(['--pdns_connect_string', new_connect_string,
                                             '--is_present', 'sanity_check.tld']))

    def test_that_setting_an_unallowed_key_errors(self):
        """
        arbitrary key-value pairs shouldn't be saved to the config files
        """
        with self.assertRaises(PowergloveError):
            self.run_with_args(['--set', 'some_key', 'some_value'])

    def test_that_the_command_line_can_save_a_new_pdns_connection_string(self):
        """
        if a user passing an sqla connection string on the command,
        it should be preferentially used over a config file
        """
        # using the normal, mocked configuration file
        self.assertTrue(self.run_with_args(['--is_present', self.pdns.records.testing_a_133.name]))
        self.add_and_test_new_hostname(['sanity_check.tld', '10.10.*.*'])
        self.assertTrue(self.run_with_args(['--is_present', 'sanity_check.tld']))

        new_connect_string = 'sqlite:///%s' % self.get_temporary_file().name
        self.log.debug('setting up a new PDNS test location at %s', new_connect_string)
        # we've now setup this new, other PDNS installation to a new place, and saved it to the config file
        setup_mock_pdns(self.get_session_from_connect_string(new_connect_string)())
        # we've set the configuration file to now use this new PDNS file
        self.run_with_args(['--set', 'pdns_connect_string', new_connect_string])
        # this is NOT the original SQLite database, so it does not work
        self.assertFalse(self.run_with_args(['--is_present', 'sanity_check.tld']))
        # this is using the overridden value, so it doesn't
        self.assertTrue(self.run_with_args(['--pdns_connect_string', self.original_sqla_connect_string,
                                             '--is_present', 'sanity_check.tld']))

    def test_sanity(self):
        """
        test some manually inserted items are indeed in the database
        """

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

        self.assertRecordExists(type='A', name=self.pdns.records.testing_a_132.name)
        self.assertIsNone(self.getOneDomain(id=self.pdns.records.testing_a_132.domain_id).notified_serial)
        self.assertRecordExists(type='A', name=self.pdns.records.testing_a_133.name)
        self.assertRecordExists(type='PTR', name=self.pdns.records.testing_ptr_132.name)
        self.assertRecordExists(type='PTR', name=self.pdns.records.testing_ptr_133.name)
        self.assertRecordDoesNotExist(type='A', name=self.pdns.records.stable_a_134.name)
        self.assertIsNotNone(self.getOneDomain(id=self.pdns.records.stable_a_134.domain_id).notified_serial)
        self.assertRecordExists(type='A', name=self.pdns.records.stable_a_135.name)
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

        self.add_and_test_new_hostname(['invalid_too_many.test.tld', '192.168.132.50', '192.168.132.55', '192.168.132.60'],
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

    def test_catching_ranges_outside_what_a_particular_domain_spans(self):

        # in the event that stable is, by convention, a 192.168.134/24 domain, we're not enforcing that
        self.add_and_test_new_hostname(['in_the_range_of_testing.stable.tld', '192.168.132-133.*'])
        self.add_and_test_new_hostname(['outside_the_range_cidr.stable.tld', '192.168.132/22'])
        self.add_and_test_new_hostname(['outside_the_range_glob.stable.tld', '192.168.132-135.*'])
        self.add_and_test_new_hostname(['bridges_the_domain.stable.tld', '192.168.133-134.*'])

    def test_tying_PTR_records_to_the_correct_PTR_domain_in_case_of_multiple_options(self):
        self.add_and_test_new_hostname(['sanity_check.tld', '10.10.*.*'])
        self.add_and_test_new_hostname(['sanity_check2.tld', '10.20.*.*'])
        sanity_check_10_10 = self.getOneRecord(content='sanity_check.tld', type='PTR')
        self.assertEqual(sanity_check_10_10.domain_id, self.pdns.domains.wide_domain_ptr_10_10.id)
        sanity_check_10_20 = self.getOneRecord(content='sanity_check2.tld', type='PTR')
        self.assertEqual(sanity_check_10_20.domain_id, self.pdns.domains.wide_domain_ptr_10.id)


    def test_catching_ranges_outside_what_is_pdns(self):
        # this is WAAAAAAAAY too big and we don't have a PTR associated
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

    def test_assert_difference_between_is_present_and_assert_is_present(self):
        """
        we want to support command line applications that care about return status
        """

        self.assertTrue(self.run_with_args(['--is_present', self.pdns.records.testing_a_133.name]))
        self.assertEqual(self.run_with_args(['--assert_is_present', self.pdns.records.testing_a_133.name]), 0)
        self.assertFalse(self.run_with_args(['--is_present', 'nonexistent.name.unknown']))
        with self.assertRaises(PowergloveError):
            self.run_with_args(['--assert_is_present', 'nonexistent.name.unknown'])

    def test_creation_of_text_record(self):
        """
        Tests that providing text record contents leads to the creation of an associated text record
        """
        text_record = 'test.thing.what'

        self.add_and_test_new_hostname(['record_with_associated_text.test.tld', '192.168.132.233',
                                        '--text', text_record])
        self.assertRecordExists(type='TXT', name='record_with_associated_text.test.tld',
                                content=text_record)

    def test_that_creating_an_a_record_defaults_to_no_text_record(self):
        """
        Tests that creating a text record defaults to not creating a text record
        """

        self.add_and_test_new_hostname(['record_with_no_associated_text.test.tld', '192.168.132.234'])
        self.assertRecordDoesNotExist(type='TXT', name='record_with_no_associated_text.test.tld')


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
            self.assertIsNotNone(self.getOneDomain(id=a_record.domain_id).notified_serial)
            if ip is not None:
                self.assertRecordExists(type='PTR', content=added_hostname)
                ptr_record = self.getOneRecord(type='PTR', content=added_hostname)
                self.assertEqual(ip, a_record.content)
                self.assertIsNotNone(self.getOneDomain(id=ptr_record.domain_id).notified_serial)
            if delete:
                self.run_with_args(['--remove', added_hostname])
                self.assertRecordDoesNotExist(type='A', name=added_hostname)

            return added_hostname


    def test_unable_to_handle_no_range(self):
        with self.assertRaises(PowergloveError) as cm:
            self.run_with_args(['--add', 'fall.down'])
        self.assertIn("unable to find a suitable range", cm.exception.output)
