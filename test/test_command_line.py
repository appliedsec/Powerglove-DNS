import collections
import time

from copy import deepcopy
import sqlalchemy

from sqlalchemy.orm import sessionmaker

from test import PowergloveTestCase
from powerglove_dns import main
from powerglove_dns.powerglove import PowergloveError
from powerglove_dns.model import Record, Domain, Base

def setup_mock_pdns(session):
    """
    Setups a mock PDNS installation with existing domains and records using
    the provided session

    @param session: the sqlalchemy session

    @return: a namedtuple of the PDNS database in the form (domains, records)
        holding the domains in the form of:
            stable_a stable_ptr_134 stable_ptr_135
            testing_a testing_ptr_132 testing_ptr_133
        and with records in the form of:
            stable_a_134 stable_a_135 stable_ptr_134 stable_ptr_135
            testing_a_132 testing_a_133 testing_ptr_132 testing_ptr_133
            cname_record record_with_cname txt_record record_with_txt
    """

    CurrentPdns = collections.namedtuple('CurrentPdns', 'domains records')
    PdnsDomainRows = collections.namedtuple('PdnsDomainRows',
                                         'stable_a stable_ptr_134 '
                                         'stable_ptr_135 testing_a '
                                         'testing_ptr_132 testing_ptr_133')

    PdnsRecordRows = collections.namedtuple('PdnsRecordRows',
                                            'stable_a_134 stable_a_135 '
                                            'stable_ptr_134 stable_ptr_135 '
                                            'testing_a_132 testing_a_133 '
                                            'testing_ptr_132 testing_ptr_133 '
                                            'cname_record record_with_cname '
                                            'txt_record record_with_txt')

    current_domains = PdnsDomainRows(Domain(0, 'stable.tld'),
                                     Domain(1, '134.168.192.in-addr.arpa'),
                                     Domain(2, '135.168.192.in-addr.arpa'),
                                     Domain(3, 'test.tld'),
                                     Domain(4, '132.168.192.in-addr.arpa'),
                                     Domain(5, '133.168.192.in-addr.arpa'))

    current_records = PdnsRecordRows(Record(0, 0, 'test_existing.stable.tld',
                                            'A', '192.168.134.2'),
                                     Record(1, 0, 'test_existing2.stable.tld',
                                            'A', '192.168.135.2'),
                                     Record(2, 1, '2.134.168.192.in-addr.arpa',
                                            'PTR', 'test_existing.stable.tld'),
                                     Record(3, 2, '2.135.168.192.in-addr.arpa',
                                            'PTR', 'test_existing2.stable.tld'),
                                     Record(4, 3, 'test_existing.test.tld',
                                            'A', '192.168.132.2'),
                                     Record(5, 3, 'test_existing2.test.tld',
                                            'A', '192.168.133.2'),
                                     Record(6, 4, '2.132.168.192.in-addr.arpa',
                                            'PTR', 'test_existing.test.tld'),
                                     Record(7, 5, '2.133.168.192.in-addr.arpa',
                                            'PTR', 'test_existing2.test.tld'),
                                     Record(21, 3, 'cnamer.test.tld',
                                            'CNAME', 'cnamee.test.tld'),
                                     Record(22, 3, 'cnamee.test.tld',
                                            'A', '192.168.133.57'),
                                     Record(23, 3, 'text.test.tld',
                                            'TXT', 'this is a text record'),
                                     Record(24, 3, 'text.test.tld',
                                            'A', '192.168.133.61')
                                     )

    Base.metadata.create_all(session.bind)

    # the deepcopy allows the original records to still be used as
    # comparisons when deletes happen on the actual db
    for domain in deepcopy(current_domains):
        session.add(domain)
    session.commit()

    for record in deepcopy(current_records):
        session.add(record)
    session.commit()

    return CurrentPdns(current_domains, current_records)



class PowergloveDNSCommandLineTestCase(PowergloveTestCase):

    def _querySession(self, session, table=Record, **kwargs):
        """
        helper function for querying the session

        @arg table: the declarative-base class object from powerglove_dns.model,
            defaults to Record
        @kwargs: the keyword arguments to query with
        @return: all of the results of the query
        """

        return session.query(table).filter_by(**kwargs).all()

    def getOneRecord(self, session=None, **kwargs):
        """
        @arg session: the database session to use for the query
        @args
        @raise AssertionError: if more or less than one record exists based on
            the rec_type/name
        """
        if session is None:
            session = self.Session()

        results = self._querySession(session, **kwargs)
        if len(results) > 1:
            raise AssertionError('found >1 records for %r: %r' % (kwargs,
                                                                  results))
        elif not results:
            raise AssertionError('No records found for %r' % kwargs)

        return results[0]

    def assertRecordExists(self, session=None, **kwargs):
        """
        @arg rec_type: the type of record, either 'A' or 'PTR' primarily
        @arg name: the name of the record, FQDN for A records, reverse DNS
            for PTR records
        @arg session: the database session to use for the query
        @raise AssertionError: if the record does not exist
        """
        if session is None:
            session = self.Session()
        if not len(self._querySession(session, **kwargs)):
            raise AssertionError('unable to find record from %s' % kwargs)

    def assertRecordDoesNotExist(self, session=None, **kwargs):
        """
        @arg rec_type: the type of record, either 'A' or 'PTR' primarily
        @arg name: the name of the record, FQDN for A records, reverse DNS for
            PTR records
        @arg session: the database session to use for the query
        @raise AssertionError: if the record does exist
        """
        if session is None:
            session = self.Session()
        if len(self._querySession(session, **kwargs)):
            raise AssertionError('unexpectedly found record using %s' % kwargs)

    def run_with_args(self, args):

        return main(args, logger=self.log, session=self.Session,
                          config_file=self.config_file,
                          extra_config_info={'test.tld': '192.168.132-133.*',
                                             'stable.tld': '192.168.134-135.*'})

    def setUp(self):
        url = self.config['sqlalchemy']['url']
        self.Session = sessionmaker(bind=sqlalchemy.create_engine(url))
        self.log.debug('set up the session')
        self.pdns = setup_mock_pdns(self.Session())

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
        self.add_and_test_new_hostname(['must_be_%s' % manual_ip,
                                        manual_ip, manual_ip],
                                       ip=manual_ip)
        self.add_and_test_new_hostname(['as_a_result_must_be_%s' % next_ip,
                                        manual_ip, next_ip], ip=next_ip)
        self.add_and_test_new_hostname(['whatever_basically',
                                        '192.168.132.1',
                                        '192.168.133.255'])
        self.add_and_test_new_hostname(['ip_already_reserved',
                                        manual_ip,
                                        next_ip],
                                       invalid=True)

        with  self.assertRaises(AssertionError):
            self.add_and_test_new_hostname(['mismatched_ip',
                                            '192.168.135.62',
                                            '192.168.135.62'],
                                           ip='192.168.135.63')

    def test_add_and_deletes_with_explicit_range(self):

        manual_ip = '192.168.135.101'
        next_ip = '192.168.135.102'
        name = self.add_and_test_new_hostname(['must_be_%s' % manual_ip, manual_ip, manual_ip],
                                              ip=manual_ip, delete=True)
        self.assertRecordDoesNotExist(type='A', name=name)
        self.assertRecordDoesNotExist(type='PTR', content=name)
        name = self.add_and_test_new_hostname(['due_to_delete_is_still_%s' % manual_ip, manual_ip, next_ip],
                                              ip=manual_ip)
        self.assertRecordExists(type='A', name=name)
        self.assertRecordExists(type='PTR', content=name)

    def test_avoiding_invalid_addresses(self):

        self.add_and_test_new_hostname(['must_not_be_0_255_or_duplicate', '192.168.132.255', '192.168.133.2'],
                                       invalid=True)
        self.add_and_test_new_hostname(['found_valid_address', '192.168.132.255', '192.168.133.3'],
                                       ip='192.168.133.3')

    def test_duplicate_hostname(self):

        self.add_and_test_new_hostname(['brand_new_name', '192.168.132.150', '192.168.132.151'])
        self.add_and_test_new_hostname(['brand_new_name', '192.168.132.155', '192.168.132.156'], invalid=True)

    def test_catching_invalid_commandline_arguments(self):

        self.add_and_test_new_hostname(['invalid_explicit', '192.168.132.150', '192.168.132.5'], invalid=True)
        self.add_and_test_new_hostname(['invalid_CIDR', '192.168/2'], invalid=True)
        self.add_and_test_new_hostname(['invalid_IPGlob', '192.168.*.*'], invalid=True)

    def test_adding_with_CIDR(self):

        self.add_and_test_new_hostname(['32_bit_mask', '192.168.135.100/32'])
        self.add_and_test_new_hostname(['23_bit_mask', '192.168.132/23'])
        self.add_and_test_new_hostname(['23_bit_mask_same_domain', '192.168.133/23'])
        self.add_and_test_new_hostname(['outside_the_range', '192.168.132/22'], invalid=True)

    def test_adding_with_IPGlob(self):

        self.add_and_test_new_hostname(['32_bit_mask', '192.168.135.100-101'])
        self.add_and_test_new_hostname(['23_bit_mask', '192.168.132-133.*'])
        self.add_and_test_new_hostname(['outside_the_range', '192.168.132-135.*'], invalid=True)
        self.add_and_test_new_hostname(['bridges_the_domain', '192.168.133-134.*'], invalid=True)

    def test_adding_with_implicit_domain(self):

        self.add_and_test_new_hostname(['new_test', '--domain', 'test.tld'])
        self.add_and_test_new_hostname(['new_stable', '--domain', 'stable.tld'])
        self.add_and_test_new_hostname(['unknown_domain', '--domain', 'what.tld'], invalid=True)
        self.add_and_test_new_hostname(['omitted_domain'], invalid=True)

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

        self.add_and_test_new_hostname(['record_with_associated_text', '--domain', 'test.tld',
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

    def test_unable_to_handle_implicit_mapping(self):
        with self.assertRaises(PowergloveError) as cm:
            self.run_with_args(['fall.down.',
                                '--domain',
                                'go.boom'])
        self.assertEqual(cm.exception.output, "unable to handle implicit mapping with domain: go.boom")

    def test_unable_to_handle_no_range_or_domain(self):
        with self.assertRaises(PowergloveError) as cm:
            self.run_with_args(['fall.down.'])
        self.assertEqual(cm.exception.output, "unable to handle implicit mapping without a range or domain")
