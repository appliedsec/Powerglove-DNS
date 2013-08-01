import collections
import logging
import os

from tempfile import NamedTemporaryFile

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from copy import deepcopy

import sqlalchemy

from mock import patch
from sqlalchemy.orm import sessionmaker

from powerglove_dns import PowergloveDns
from powerglove_dns.model import Domain, Base, Record

logging.basicConfig(level=logging.DEBUG)

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
                                         'tld_a '
                                         'stable_a testing_a '
                                         'super_stable_a super_testing_a '
                                         'testing_ptr_132 testing_ptr_133 '
                                         'stable_ptr_134 stable_ptr_135 '
                                         'wide_domain_ptr_10_10 wide_domain_ptr_10')

    current_domains = PdnsDomainRows(
        Domain(0, 'tld'),
        Domain(1, 'stable.tld'),
        Domain(2, 'test.tld'),
        Domain(3, 'super.stable.tld'),
        Domain(4, 'super.test.tld'),
        Domain(5, '132.168.192.in-addr.arpa'),
        Domain(6, '133.168.192.in-addr.arpa'),
        Domain(7, '134.168.192.in-addr.arpa'),
        Domain(8, '135.168.192.in-addr.arpa'),
        Domain(9, '10.10.in-addr.arpa'),
        Domain(10, '10.in-addr.arpa'),
    )

    current_domains = current_domains

    PdnsRecordRows = collections.namedtuple('PdnsRecordRows',
                                            'stable_a_134 stable_a_135 '
                                            'stable_ptr_134 stable_ptr_135 '
                                            'testing_a_132 testing_a_133 '
                                            'testing_ptr_132 testing_ptr_133 '
                                            'cname_record record_with_cname '
                                            'txt_record record_with_txt tld_a tld_ptr')

    current_records = PdnsRecordRows(Record(0, current_domains.stable_a.id, 'test_existing.stable.tld',
                                            'A', '192.168.134.2'),
                                     Record(1, current_domains.stable_a.id, 'test_existing2.stable.tld',
                                            'A', '192.168.135.2'),
                                     Record(2, current_domains.stable_ptr_134.id, '2.134.168.192.in-addr.arpa',
                                            'PTR', 'test_existing.stable.tld'),
                                     Record(3, current_domains.stable_ptr_135.id, '2.135.168.192.in-addr.arpa',
                                            'PTR', 'test_existing2.stable.tld'),
                                     Record(4, current_domains.testing_a.id, 'test_existing.test.tld',
                                            'A', '192.168.132.2'),
                                     Record(5, current_domains.testing_a.id, 'test_existing2.test.tld',
                                            'A', '192.168.133.2'),
                                     Record(6, current_domains.testing_ptr_132.id, '2.132.168.192.in-addr.arpa',
                                            'PTR', 'test_existing.test.tld'),
                                     Record(7, current_domains.testing_ptr_133.id, '2.133.168.192.in-addr.arpa',
                                            'PTR', 'test_existing2.test.tld'),
                                     Record(21, current_domains.testing_a.id, 'cnamer.test.tld',
                                            'CNAME', 'cnamee.test.tld'),
                                     Record(22, current_domains.testing_a.id, 'cnamee.test.tld',
                                            'A', '192.168.133.57'),
                                     Record(23, current_domains.testing_a.id, 'text.test.tld',
                                            'TXT', 'this is a text record'),
                                     Record(24, current_domains.testing_a.id, 'text.test.tld',
                                            'A', '192.168.133.61'),
                                     Record(25, current_domains.tld_a.id, 'big.domain.tld',
                                            'A', '10.10.111.61'),
                                     Record(26, current_domains.wide_domain_ptr_10_10.id, '61.111.10.10.in-addr.arpa',
                                            'PTR', 'big.domain.tld')
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

class BasePowergloveTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = logging.getLogger('%s.%s' % (cls.__module__, cls.__name__))
        cls.log.debug('test case initialized')

    @classmethod
    def tearDownClass(cls):
        cls.log.debug('shutting down test case')


class PowergloveTestCase(BasePowergloveTestCase):

    def get_temporary_file(self):
        """
        simplifies getting and cleaning up a temporary file
        """
        temp = NamedTemporaryFile(delete=False)
        self.addCleanup(os.unlink, temp.name)

        return temp

    def get_session_from_connect_string(self, sqla_connect_string):
        return sessionmaker(bind=sqlalchemy.create_engine(sqla_connect_string))

    def _setup_test_sqlite_database(self):
        """
        @return: the SQLA connection string
        """

        temp = self.get_temporary_file()
        sqla_connect_string = 'sqlite:///%s' % temp.name
        self.log.debug('setting up the main session with %s', sqla_connect_string)
        self.Session = self.get_session_from_connect_string(sqla_connect_string)
        self.log.debug('set up the session')
        self.pdns = setup_mock_pdns(self.Session())

        return sqla_connect_string


    def _setup_test_config_file(self, sqla_connect_string):
        """
        @return:
        """
        temp = self.get_temporary_file()

        with temp as temp_config_file:
            temp_config_file.write('pdns_connect_string = %r' % sqla_connect_string)

        config_patcher = patch.object(PowergloveDns, 'def_config_file', new=temp.name)
        self.addCleanup(config_patcher.stop)
        config_patcher.start()


    def setUp(self):
        self.original_sqla_connect_string = self._setup_test_sqlite_database()
        self._setup_test_config_file(self.original_sqla_connect_string)


    def _querySession(self, session, table=Record, **kwargs):
        """
        helper function for querying the session

        @arg table: the declarative-base class object from powerglove_dns.model,
            defaults to Record
        @kwargs: the keyword arguments to query with
        @return: all of the results of the query
        """

        return session.query(table).filter_by(**kwargs).all()

    def getOneDomain(self, session=None, **kwargs):
        """
        @arg session: the database session to use for the query
        @args
        @raise AssertionError: if more or less than one record exists based on
            the rec_type/name
        """
        if session is None:
            session = self.Session()

        results = self._querySession(session, table=Domain, **kwargs)
        if len(results) > 1:
            raise AssertionError('found >1 records for %r: %r' % (kwargs,
                                                                  results))
        elif not results:
            raise AssertionError('No records found for %r' % kwargs)

        return results[0]

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
