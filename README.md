Powerglove DNS
==============================
[![Build Status](https://travis-ci.org/appliedsec/Powerglove-DNS.png)](https://travis-ci.org/appliedsec/Powerglove-DNS)

```
# powerglovedns --help
usage: powerglovedns [-h] [--pdns_connect_string PDNS_CONNECT_STRING]
                     [--ttl TTL] [--text TEXT_RECORD_CONTENTS]
                     (--set CONFIG_KEY CONFIG_VALUE | --cname CNAME_FQDN A_Record_FQDN | --is_present FQDN | --assert_is_present FQDN | --remove FQDN | --add FQDN [RANGE ...])

Reserve an ip address in the network's Power DNS install for the given fully-
qualified domain name

optional arguments:
  -h, --help            show this help message and exit
  --pdns_connect_string PDNS_CONNECT_STRING
                        the SQL Alchemy-compatible connection string to Power
                        DNS. Required in either the configuration file or on
                        the commandline
  --set CONFIG_KEY CONFIG_VALUE
                        if provided, save a key-value pair to the
                        configuration file, where it will be used if the
                        command line doesn't set it. Possible keys are:
                        pdns_connect_string
  --cname CNAME_FQDN A_Record_FQDN
                        if provided, create a CNAME alias from the provided
                        cname fully-qualified-domain-name to the provided A
                        record fully-qualified domain name.
  --is_present FQDN     returns boolean True (return code 1) if a provided
                        fully-qualified domain name is present in the DNS A
                        records, boolean False (0 return code) otherwise
  --assert_is_present FQDN
                        returns a 0 return code if a provided fully-qualified
                        domain name is present in the DNS A records, 1
                        otherwise
  --remove FQDN         Remove the provided fully qualified domain name, if
                        specified, no hostnames or cnames will be added
  --add FQDN [RANGE ...]
                        reserve an ip for the FQDN between this range.
                        Acceptable formats are CIDR (e.g. 192.168.132/24), IP
                        Glob (e.g. 192.168.132-133.*), start and stop ip (e.g.
                        192.168.132.2 192.168.133.254), andexplicit ip (e.g.
                        192.168.132.12). No ips ending with 0, 1, or 255 will
                        be used in a given range

add options:
  options that are used in the event of a record being added

  --ttl TTL             the TTL that should be set with the added record
                        [default: 300]
  --text TEXT_RECORD_CONTENTS
                        if specified, make an associated text record with the
                        provided contents (as a string)
```
