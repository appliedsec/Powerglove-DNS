import argparse
import datetime
import sys


from powerglove_dns.powerglove import PowergloveDns

parser = argparse.ArgumentParser(description='Reserve an ip address in the network\'s Power DNS install '
                                             'for the given fully-qualified domain name')

parser.add_argument('--pdns_connect_string', 
                    help='the SQL Alchemy-compatible connection string to Power DNS. '
                         'Required in either the configuration file or on the commandline')

add_group = parser.add_argument_group('add options',
                                      'options that are used in the event of a record being added')

add_group.add_argument('--ttl', type=int, default=300,
                       help='the TTL that should be set with the added record '
                            '[default: %(default)s]')
add_group.add_argument('--text', metavar='TEXT_RECORD_CONTENTS',
                       dest='text_record_contents',
                       default='created by Powerglove-DNS on '
                               '{0}'.format(datetime.datetime.utcnow()),
                       help='if specified, make a text record with the provided '
                            'contents (as a string)')

action_group = parser.add_mutually_exclusive_group(required=True)

action_group.add_argument('--cname', metavar=('CNAME_FQDN', 'A_Record_FQDN'),
                          dest='cname', default=None, nargs=2,
                          help='if provided, create a CNAME alias from the provided'
                               'cname fully-qualified-domain-name to the provided'
                               'A record fully-qualified domain name. No new '
                               'hostnames will be added')

action_group.add_argument('--is_present', metavar='FQDN', dest='fqdn_to_test',
                          help='returns boolean True (return code 1) if a provided fully-qualified domain '
                               'name is present in the DNS A records, boolean False (0 return code) otherwise')

action_group.add_argument('--assert_is_present', metavar='FQDN', dest='fqdn_to_assert',
                          help='returns a 0 return code if a provided fully-qualified domain '
                               'name is present in the DNS A records, 1 otherwise')

action_group.add_argument('--remove', metavar='FQDN',
                          help='Remove the provided fully qualified domain name, '
                               'if specified, no hostnames or cnames will be added')

action_group.add_argument('--add', metavar=('FQDN', 'RANGE'), nargs='+',
                          help='reserve an ip for the FQDN between this range. '
                               'Acceptable formats are CIDR (e.g. 192.168.132/24), '
                               'IP Glob (e.g. 192.168.132-133.*), '
                               'start and stop ip (e.g. 192.168.132.2 192.168.133.254), and'
                               'explicit ip (e.g. 192.168.132.12). No ips ending with '
                               '0, 1, or 255 will be used in a given range')


def main(args=None, logger=None, session=None):

    args = parser.parse_args(args)

    assistant = PowergloveDns(session=session, logger=logger)

    if args.fqdn_to_test:
        return assistant.fqdn_is_present(args.fqdn_to_test)

    elif args.fqdn_to_assert:
        return not assistant.fqdn_is_present(args.fqdn_to_assert)

    elif args.remove:
        return assistant.remove_fqdn(args.remove)

    elif args.cname:
        return assistant.add_cname_record(*args.cname)

    elif args.add:
        return assistant.add_a_record(args.add[0], args.add[1:], args.ttl, args.text_record_contents)
    else:
        raise RuntimeError('command specified given args: %r' % args)



if __name__ == '__main__':

    if main():
        sys.exit(0)
    else:
        sys.exit(1)