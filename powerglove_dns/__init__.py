import argparse
import datetime
import sys


from powerglove_dns.powerglove import PowergloveDns

parser = argparse.ArgumentParser(description="Reserve an ip address in the "
                                             "network's powerdns install")

parser.add_argument('--remove', metavar='FQDN',
                    help='Remove the provided fully qualified domain name, '
                         'if specified, no hostnames or cnames will be added')
parser.add_argument('--ttl', type=int, default=300,
                    help='the TTL that should be set with the added record '
                         '[default: %(default)s]')
parser.add_argument('--domain', metavar='name', default=None,
                    help='instead of specifying an IPRange or CIDR, specify '
                         'the domain you wish to place the hostname (e.g. '
                         'test.tld or example.tld)')
parser.add_argument('--is_present', metavar='FQDN', dest='fqdn_to_test',
                    help='returns True if a provided fully-qualified domain '
                         'name is present in the DNS A records')
parser.add_argument('--text', metavar='TEXT_RECORD_CONTENTS',
                    dest='text_record_contents',
                    default='created by DNS assistant on '
                            '{0}'.format(datetime.datetime.utcnow()),
                    help='if specified, make a text record with the provided '
                         'contents (as a string)')
parser.add_argument('--cname', metavar=('CNAME FQDN', 'A Record FQDN'),
                    dest='cname', default=None, nargs=2,
                    help='if provided, create a CNAME alias from the provided'
                         'cname fully-qualified-domain-name to the provided'
                         'A record fully-qualified domain name. No new '
                         'hostnames will be added')

parser.add_argument('hostname', metavar='hostname', nargs='?',
                    help='specify the hostname (NOT full-qualified domain '
                         'name) that you want to reserve an IP for.  It will '
                         'be paired with the appropriate domain name to form '
                         'a fully qualified domain name. Not read if any of '
                         'the following options are set: --remove, --cname, '
                         '--is_present')

parser.add_argument('range', metavar='IP', nargs='*',
                    help='reserve an ip between this range (*.*.*.0, *.*.*.1 '
                         'and *.*.*.255 will not be used). Acceptable formats '
                         'are CIDR (e.g. 192.168.133/23), IP Glob (e.g. '
                         '192.168.133-134.*), expicit pair of first/last IPs '
                         '(e.g. 192.168.133.0 192.168.134.255), or may be '
                         'omitted if --domain is specified.')

def main(args=None, **assistant_kwargs):

    args = parser.parse_args(args)

    assistant = PowergloveDns(**assistant_kwargs)
    if args.fqdn_to_test:

        return assistant.fqdn_is_present(args.fqdn_to_test)

    elif args.remove:
        return assistant.remove_fqdn(args.remove)

    elif args.cname:
        return assistant.add_cname_record(*args.cname)

    else:

        return assistant.add_a_record(args.hostname,
                                      args.range,
                                      args.domain,
                                      args.ttl,
                                      args.text_record_contents)



if __name__ == '__main__':

    if main():
        sys.exit(0)
    else:
        sys.exit(1)