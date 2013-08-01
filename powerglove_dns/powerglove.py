import itertools
import os
import logging
import logging.config
import time

import configobj
import netaddr
import sqlalchemy

from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from netaddr import IPAddress

from model import Record, Domain


class PowergloveError(Exception):
    """
    Generic Powerglove DNS Error
    """
    def __init__(self, string, *str_args, **str_kwargs):
        """
        Simplifying string output
        """
        super(PowergloveError, self).__init__()
        if str_args or str_kwargs:
            self.output = string.format(*str_args, **str_kwargs)
        else:
            self.output = string

    def __str__(self):
        return repr(self.output)


class PowergloveFqdnNotFoundError(PowergloveError):
    """
    Error for being unable to find an expected hostname
    """


class PowergloveDns(object):
    """
    Class for interacting with a Power DNS Database

    @cvar def_config_file: path to default settings config file
    @type def_config_file: C{str}
    """
    def_config_file = os.path.join(os.path.expanduser('~'), '.powergloverc')
    allowed_configuration_keys = ('pdns_connect_string',)

    def __init__(self, pdns_sqla_url=None, logger=None):
        """
        Initialize the Powerglove DNS object, if session is provided it will be
        used as the instance session. Otherwise, if pdns_sqla_url is
        provided then it takes precendence over a provided/default config file
        for creating a new session

        @param pdns_sqla_url: the url for the Power DNS installation
        @type pdns_sqla_url: C{str}
        @param session: the existing SQL Alchemy Session
        @param self.log: the self.log instance to use, else, a new one
            is created
        """

        if logger is None:
            self.log = logging.getLogger(self.__class__.__name__)
        else:
            self.log = logger

        self._setup_sqlalchemy_session(pdns_sqla_url, self.def_config_file)

    @classmethod
    def set_config(cls, key, value, config_file=None):

        if config_file is None:
            config_file = cls.def_config_file

        if key not in cls.allowed_configuration_keys:
            raise PowergloveError('%r not an allowed configuration key. Possible values are %s' %
                                  (key, ', '.join(cls.allowed_configuration_keys)))

        config = configobj.ConfigObj(config_file)
        config[key] = value
        config.write()

    def _setup_sqlalchemy_session(self, pdns_sqla_url, config_file):

        if pdns_sqla_url:
            self.sqla_session_obj = pdns_sqla_url
            return

        if not pdns_sqla_url and (config_file is None or not os.path.exists(config_file)):
            raise PowergloveError('Non-existent configuration file %r and the command line '
                                  'doesn\'t specify Power DNS connection; see --help' % config_file)

        config = configobj.ConfigObj(config_file)

        pdns_sqla_url = config.get('pdns_connect_string')
        if not pdns_sqla_url:
            raise PowergloveError("config file %r doesn't specify a 'pdns_connect_string'" % config_file)

        try:
            self.sqla_session_obj = pdns_sqla_url
        except Exception:
            self.log.error('unknown error getting a SQL-Alchemy session with %r', pdns_sqla_url)
            raise

    @property
    def sqla_session_obj(self):
        """
        get the previously set up session object
        @return: L{sqlalchemy.Session}
        """

        return self._session_obj

    @sqla_session_obj.setter
    def sqla_session_obj(self, url):
        """
        set the session object using the provided URL

        @param url: the SQLAlchemy url that the engine will be created with
        @type url: C{str}
        """
        self._sqla_engine = sqlalchemy.create_engine(url)
        self._session_obj = sessionmaker(bind=self._sqla_engine)

    @property
    def session(self):
        """
        Return the session instance

        @return: the session instance of the type return from sqla_session_obj
        """
        if not hasattr(self, '_session'):
            self._session = self.sqla_session_obj()

        return self._session

    @property
    def domains(self):
        """
        @return: a C{dict} mapping the domain name
        """

        return dict([(record.name, record)
                     for record in self.session.query(Domain).all()])

    @property
    def a_domains(self):
        """
        @return: a C{dict} mapping the A domain name to the domain
        """

        return dict([(dom_name, dom) for dom_name, dom in self.domains.items()
                     if not dom_name.endswith('.in-addr.arpa')])

    @property
    def ptr_domains(self):
        """
        @return: a C{dict} mapping the PTR domain name to the domain
        """

        return dict([(dom_name, dom) for dom_name, dom in self.domains.items()
                     if dom_name.endswith('.in-addr.arpa')])

    def get_existing_records(self, rec_type='A', **criteria):
        if rec_type not in ('A', 'PTR', 'SOA', 'CNAME', 'TXT'):
            raise PowergloveError('invalid record type {0} specified',
                                    rec_type)
        try:
            return self.session.query(Record).filter_by(type=rec_type,
                                                        **criteria).all()
        except NoResultFound:
            return []

    def get_record(self, rec_type='A', **criteria):
        if rec_type not in ('A', 'PTR', 'SOA', 'CNAME', 'TXT'):
            raise PowergloveError('invalid record type {0} specified',
                                    rec_type)

        try:
            return self.session.query(Record).filter_by(type=rec_type,
                                                        **criteria).one()
        except NoResultFound:
            return None

    def get_records(self, rec_type='A', **criteria):
        if rec_type not in ('A', 'PTR', 'SOA', 'CNAME', 'TXT'):
            raise PowergloveError('invalid record type {0} specified',
                                    rec_type)

        return self.session.query(Record).filter_by(type=rec_type,
                                                    **criteria).all()

    def _get_closest_domain_match_from_string(self, record_string, domains):
        """
        convenience function for finding the closest matching domain for a string record (a more specific domain wins
        if more than one domain matches

        @param record_string:
        @param domains:
        @return:
        """

        def _split_reverse(dot_delimited_string):
            return tuple(reversed(dot_delimited_string.split('.')))

        record_string_parts = _split_reverse(record_string)

        inferred_domain = None
        max_matches = 0
        for name, domain in domains.iteritems():
            matches = 0
            complete_match = True
            domain_parts = _split_reverse(name)
            for domain_part, record_name_part in zip(domain_parts, record_string_parts):
                if domain_part == record_name_part:
                    matches += 1
                else:
                    complete_match = False
            if matches > max_matches and complete_match:
                max_matches = matches
                inferred_domain = domain

        if inferred_domain:
            return inferred_domain
        else:
            raise PowergloveError('unable to get a domain from associated string: %r' % record_string)

    def get_ptr_domain_from_ptr_record_name(self, ptr_name):
        """

        @param ptr_name: the PTR record name to get a domain from
        @return: the associated Domain as a C{Domain} as determined based on the PTR record name
        """

        return self._get_closest_domain_match_from_string(ptr_name, self.ptr_domains)


    def get_a_domain_from_fqdn(self, fqdn):
        """

        @param fqdn: the C{str} fully-qualified domain name
        @return: the associated Domain as a C{Domain} as determined based on the FQDN
        """

        return self._get_closest_domain_match_from_string(fqdn, self.a_domains)

    def update_domain_serial(self, domain_id):

        domain_to_update = [dom for dom in self.domains.itervalues() if dom.id == domain_id][0]
        domain_to_update.touch_serial()
        self.log.debug('updated serial for %r', domain_to_update)
        self.session.add(domain_to_update)
        self.session.commit()

    def reverse_ip_to_ptr_record(self, ip_address):
        if isinstance(ip_address, IPAddress):
            ip = ip_address
        else:
            ip = IPAddress(ip_address)

        return str(ip.reverse_dns).rstrip('.') #the trailing period is not included in the power DNS PTR records

    def remove_fqdn(self, fqdn):
        """
        Remove the records associated with the provided hostname:
        - if the record is a CNAME, remove the CNAME and TXT records
        - if the record is an A, remove the TXT, PTR, and A records

        @param fqdn: the fully-qualified-domain for the records to remove
        @raise PowergloveFqdnNotFoundError: if the FQDN does not match up
            either an A or CNAME record
        """

        a_record = self.get_record(name=fqdn)
        cname_record = self.get_record('CNAME', name=fqdn)

        if a_record:
            return self._remove_a_record(a_record)
        elif cname_record:
            return self._remove_cname_record(cname_record)
        else:
            raise PowergloveFqdnNotFoundError('No records associated with '
                                              'fully-qualified-domain-name:'
                                              '{0}', fqdn)

    def _remove_cname_record(self, cname_record):
        """
        @param cname_record: the CNAME record to remove
        """

        self.log.info('removing CNAME alias: %s', cname_record)
        self.update_domain_serial(cname_record.domain_id)
        self.session.delete(cname_record)
        self.session.commit()

    def _remove_a_record(self, a_record):
        """
        @param a_record: the A record to remove (along with associated records)
        @raise PowergloveError: If the CNAMES exist for the provided A record
        """

        cnames = self.get_existing_records(rec_type='CNAME',
                                           content=a_record.name)

        if cnames:
            raise PowergloveError('CNAMES exist for the specified FQDN {0}:\n{1}',
                                  a_record.name,
                                  ' '.join(cname.name for cname in cnames))


        ptr_records = self.get_existing_records(rec_type='PTR',
                                                content=a_record.name)
        txt_records = self.get_existing_records(rec_type='TXT',
                                                name=a_record.name)


        self.log.info('removing associated A/PTR/TXT records for FQDN: %s',
                      a_record.name)

        domain_ids = set([a_record.domain_id])
        for record in itertools.chain(ptr_records, txt_records):
            self.log.debug('removing %s', record)
            domain_ids.add(record.domain_id)
            self.session.delete(record)
        for domain_id in domain_ids:
            self.update_domain_serial(domain_id)

        self.session.delete(a_record)
        self.session.commit()

    def get_ip_range(self, ip_range):
        """
        Get an L{netaddr.IPRange} corresponding with the provided range

        @param ip_range:
        @type ip_range: C{tuple} of length 0 through 2, all elements must be
            C{str} and will be parsed as IP address, CIDRs, or IPRanges
        @param domain: If range is length 0, the domain will be used to provide
            a default range for the given domain (e.g. 'test.tld')
        @type domain: C{str}
        @return: the L{netaddr.IPRange} associated with the provided range or
            domain
        """

        if not len(ip_range) <= 2:
            raise PowergloveError('unknown range specified: %r' % ip_range)

        if len(ip_range) == 2:
            lower, upper = ip_range
            try:
                ip_range = netaddr.ip.IPRange(lower, upper)
            except netaddr.AddrFormatError, exc:
                raise PowergloveError(exc)
            return ip_range
        elif len(ip_range) == 1:
            _ip = ip_range[0]
            if isinstance(_ip, basestring) and '/' in _ip:
                _ip=netaddr.ip.glob.cidr_to_glob(_ip)
            if not netaddr.ip.glob.valid_glob(_ip):
                raise TypeError('unable to convert %r to IPRange' % _ip)
            else:
                return netaddr.ip.glob.glob_to_iprange(_ip)
        else:
            raise PowergloveError('unable to find a suitable range '
                                    'using {0}', ip_range)

    def is_valid_address(self, ip):
        invalid_last_octet = ('0', '1', '255')

        return not str(ip).split('.')[-1] in invalid_last_octet

    def get_FQDN(self, hostname_prefix, domain):
        return '%s.%s' % (hostname_prefix, domain)

    def add_cname_record(self, cname_fqdn, a_fqdn):
        """
        Reserve an alias at the provided FQDN for an existing FQDN

        @param cname_fqdn: the FQDN of the alias
        @type cname_fqdn: C{str}
        @param a_fqdn: the hostname for where the alias points to
        @type a_fqdn: C{str}
        @return: C{tuple} consisting of (CNAME FQDN, A FQDN)

        """

        if not self.fqdn_is_present(a_fqdn):
            raise PowergloveError('attempting to create an alias for a '
                                    'non-existant FQDN: {0}', a_fqdn)

        a_record = self.get_record(name=a_fqdn)

        cname_record = Record(name=cname_fqdn,
                              domain_id=a_record.domain_id,
                              type='CNAME',
                              content=a_fqdn,
                              id=None)

        self.session.add(cname_record)
        self.update_domain_serial(a_record.domain_id)
        self.session.commit()

        self.log.info('created CNAME alias %r', cname_record)
        return cname_record.name, cname_record.content

    def add_a_record(self, fqdn, ip_range=None,
                     ttl=None, text_contents=None):
        """
        Make an IP reservation for a given hostname

        @param fqdn: the fully-qualified domain to reserve with
            an ip in the given ip_range
        @type fqdn: C{str}
        @param ip_range: The representation of the the IP Range to choose an IP
            from, will be parsed by get_ip_range, so if present, should be in
            form of L{netaddr.IPRange},L{netaddr.IPGlob}, CIDR, or include both
            start and end IP Addresses
        @type ip_range: None, C{tuple} of max two C{str}
        @param ttl: the TTL to use for the given records
        @type ttl: C{int}
        @param text_contents: the contents for a TXT record associated with the
            A record
        @type text_contents: C{str}
        @return: C{tuple} consisting of (a_record.name, selected_ip_address)
        """


        ip_range = self.get_ip_range(ip_range)

        if self.fqdn_is_present(fqdn):
            raise PowergloveError('fully-qualified domain name {0} exists.', fqdn)

        self.log.debug('attempting to add a record for FQDN '
                       '"%r" within ip_range %r',
                       fqdn, ip_range)

        selected_ip_address = self.get_available_ip_address(ip_range)

        a_domain = self.get_a_domain_from_fqdn(fqdn)

        a_record = Record(name=fqdn,
                        domain_id=a_domain.id,
                        type='A',
                        ttl=ttl,
                        content = str(selected_ip_address),
                        change_date=int(time.time()),
                        id=None)

        self.update_domain_serial(a_record.domain_id)

        self.log.debug('setting up "A" record: %r' % a_record)
        created_records = self.create_associated_records(a_record,
                                                         text_contents)
        self.log.debug('adding records to Power DNS')
        self.session.add(a_record)
        self.session.add_all(created_records.values())
        self.session.commit()
        self.log.info('Created A Record: %r', a_record)
        return a_record.name, selected_ip_address

    def fqdn_is_present(self, fqdn):
        """
        returns True if the provided FQDN is present in PDNS, false otherwise.
        Checks both A records and CNAME records

        @param fqdn: the Fully-Qualified-Domain-Name to test
        @type fqdn: C{str}
        """

        return any([self.get_record(name=fqdn),
                    self.get_record(rec_type='CNAME', name=fqdn)])

    def get_available_ip_address(self, ip_range):
        """
        returns a currently-available IP Address from within the provided range
        
        @param ip_range: the IP range to select from
        @type ip_range: L{netaddr.IPRange}
        @return: the selected IP Address
        @rtype: L{netaddr.IPAdress}
        """

        a_rec_gen = (IPAddress(a_record.content)
                     for a_record in self.get_existing_records())
        reserved_ip_addresses = netaddr.ip.sets.IPSet(a_rec_gen)
        self.log.debug('found reserved IP addresses: %r',
                       reserved_ip_addresses)

        selected_ip_address = None

        for ip in ip_range:
            if self.is_valid_address(ip) and ip not in reserved_ip_addresses:
                selected_ip_address = ip
                break

        if selected_ip_address is None:
            raise PowergloveError('unable to find suitable ipaddress given'
                                    'range {0} and existing address {1}',
                                    ip_range, reserved_ip_addresses)

        return selected_ip_address

    def create_associated_records(self, record,
                                  text_contents=None):
        """

        @param record: Either the A or CNAME record for which created
            associated records will be created
        @param text_contents: the content of the associated text record (should there be one)

        @return: C{dict} holding all the created records, ready for committing
        """
        created_records = dict()
        if record.type == 'A':
            ptr_name = self.reverse_ip_to_ptr_record(record.content)
            ptr_dom = self.get_ptr_domain_from_ptr_record_name(ptr_name)

            ptr_kwargs = dict(name=ptr_name,
                              content=record.name,
                              change_date=int(time.time()),
                              type='PTR',
                              domain_id=ptr_dom.id,
                              ttl=record.ttl,
                              id=None)

            ptr_record = Record(**ptr_kwargs)
            created_records['PTR'] = ptr_record

            self.update_domain_serial(ptr_dom.id)
            self.log.debug('setting up "PTR" record: %r', ptr_record)

        if text_contents:
            txt_record = Record(name=record.name,
                                domain_id=record.domain_id,
                                type='TXT',
                                content=text_contents,
                                ttl=record.ttl,
                                id=None)
            created_records['TXT'] = txt_record
            self.log.debug('setting up "TXT" record: %r', txt_record)
        # Is it more correct to NOT update the domain for a A and TEXT
        # record created in the same invocation?
        self.update_domain_serial(record.domain_id)

        return created_records




