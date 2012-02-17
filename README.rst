Powerglove DNS
==============================

powerglove DNS is a simple for reserving an IP and hostname pair in a Power DNS installation

usage: powerglove-dns [-h] [--remove FQDN] [--ttl TTL] [--domain name]
                     [--is_present FQDN] [--text TEXT_RECORD_CONTENTS]
                     [--cname CNAME FQDN A Record FQDN]
                     [hostname] [IP [IP ...]]

Reserve an ip address in the network's powerdns install

positional arguments:
  hostname              specify the hostname (NOT full-qualified domain name)
                        that you want to reserve an IP for. It will be paired
                        with the appropriate domain name to form a fully
                        qualified domain name. Not read if any of the
                        following options are set: --remove, --cname,
                        --is_present
  IP                    reserve an ip between this range (*.*.*.0, *.*.*.1 and
                        *.*.*.255 will not be used). Acceptable formats are
                        CIDR (e.g. 192.168.133/23), IP Glob (e.g.
                        192.168.133-134.*), expicit pair of first/last IPs
                        (e.g. 192.168.133.0 192.168.134.255), or may be
                        omitted if --domain is specified.

optional arguments:
  -h, --help            show this help message and exit
  --remove FQDN         Remove the provided fully qualified domain name, if
                        specified, no hostnames or cnames will be added
  --ttl TTL             the TTL that should be set with the added record
                        [default: 300]
  --domain name         instead of specifying an IPRange or CIDR, specify the
                        domain you wish to place the hostname (e.g. test.tld
                        or example.tld)
  --is_present FQDN     returns True if a provided fully-qualified domain name
                        is present in the DNS A records
  --text TEXT_RECORD_CONTENTS
                        if specified, make a text record with the provided
                        contents (as a string)
  --cname CNAME FQDN A Record FQDN
                        if provided, create a CNAME alias from the
                        provided cname fully-qualified-domain-name to the
                        provided A record fully-qualified domain name. No new
                        hostnames will be added

    