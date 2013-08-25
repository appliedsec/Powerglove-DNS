import argparse
import datetime
import sys


from powerglove_dns.powerglove import PowergloveDns, PowergloveError

parser = argparse.ArgumentParser(description='Reserve an ip address in the network\'s Power DNS install '
                                             'for the given fully-qualified domain name')

parser.add_argument('--pdns_connect_string', dest='pdns_connect_string', default=None,
                    help='the SQL Alchemy-compatible connection string to Power DNS. '
                         'Required in either the configuration file or on the commandline')

add_group = parser.add_argument_group('add options',
                                      'options that are used in the event of a record being added')

add_group.add_argument('--ttl', type=int, default=300,
                       help='the TTL that should be set with the added record '
                            '[default: %(default)s]')
add_group.add_argument('--text', metavar='TEXT_RECORD_CONTENTS',
                       dest='text_record_contents',
                       default=None,
                       help='if specified, make an associated text record with the provided '
                            'contents (as a string)')

action_group = parser.add_mutually_exclusive_group(required=True)

action_group.add_argument('--set', metavar=('CONFIG_KEY', 'CONFIG_VALUE'),
                          dest='set', default=None, nargs=2,
                          help='if provided, save a key-value pair to the configuration file, where it will '
                               'be used if the command line doesn\'t set it. Possible keys are: '
                               '%s' % ', '.join(PowergloveDns.allowed_configuration_keys))

action_group.add_argument('--cname', metavar=('CNAME_FQDN', 'A_Record_FQDN'),
                          dest='cname', default=None, nargs=2,
                          help='if provided, create a CNAME alias from the provided '
                               'cname fully-qualified-domain-name to the provided '
                               'A record fully-qualified domain name.')

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


def main(args=None, logger=None):

    args = parser.parse_args(args)

    if args.set:
        PowergloveDns.set_config(*args.set)
        return

    assistant = PowergloveDns(pdns_sqla_url=args.pdns_connect_string, logger=logger)

    if args.fqdn_to_test:
        return assistant.fqdn_is_present(args.fqdn_to_test)

    elif args.fqdn_to_assert:
        if not assistant.fqdn_is_present(args.fqdn_to_assert):
            raise PowergloveError('no A or CNAME record named %s is present' % args.fqdn_to_assert)
        return 0

    elif args.remove:
        return assistant.remove_fqdn(args.remove)

    elif args.cname:
        return assistant.add_cname_record(*args.cname)

    elif args.add:
        return assistant.add_a_record(args.add[0], args.add[1:], args.ttl, args.text_record_contents)
    else:
        raise RuntimeError('unknown command specified given args: %r' % args)



if __name__ == '__main__':

    try:
        return_code = main()
    except Exception as e:
        sys.stdout.write(e)
        raise
    else:
        sys.exit(return_code)