#! /usr/bin/env python3

import dns.resolver
import sys

if sys.version_info < (3, 6):
    print("Python 3.6 or higher is required, please see https://www.python.org/ or your OS package repository", file=sys.stderr)
    sys.exit(2)

import argparse
import ipaddress

help_text = """
Convert a fully qualified domain name to an opinionated JunOS address book entry.

If a subnet is provided, we look up the individual hosts via rDNS. We do not concern ourselves with anything except PTR, CNAME, A and AAAA records - if you want to create an address book entry for a mail server, just give us the FQDN of the mail server - not your mail domain.
"""

epilog_text = """
Report bugs at https://github.com/TheMysteriousX/dns2junos/issues
"""

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=help_text, epilog=epilog_text,)
parser.add_argument("-a", dest="address_book", type=str, metavar="address-book", default="global", help="Address book name")
parser.add_argument("-s", type=str, metavar="address-set", help="Add the entries to an additional address-set")
parser.add_argument("-n", action="store_false", help="Don't shorten DNS names")
parser.add_argument("-d", dest="delete", action="store_true", help="Remove existing address sets in set commands")
parser.add_argument("--dos-my-dns-server", action="store_true", help=argparse.SUPPRESS)
parser.add_argument('fqdn', type=str, nargs='+')

ip = parser.add_mutually_exclusive_group()
ip.add_argument("-4", dest='ip4', action="store_true", help="Only consider IPv4 addresses")
ip.add_argument("-6", dest='ip6', action="store_true", help='Only consider IPv6 addresses')

fmt = parser.add_mutually_exclusive_group()
fmt.add_argument("--set", dest='set', action="store_true", help="Emit output as set commands")
fmt.add_argument("--config", dest='config', action="store_true", help="Emit output as raw config")

cli_args = None
address_map = {}
address_sets = {}


def shorten(host):
    if cli_args.n:
        words = host.split(".")

        # Name is too short
        if len(words) < 4:
            return host

        return ".".join(words[:-3] + ["".join([word[0] for word in words[-3:]])])

    return host


def format_name(name, index):
    if index != 0:
        index = f"-{index}"
    else:
        index = ""

    return f"{name}{index}"


def format_entry(address_book, address_type, name, value):
    return f"set security address-book {address_book} {address_type} {name} {value}"


def format_set_entry(action, address_book, address_type, name, target_type='', value=''):
    return f"{action} security address-book {address_book} {address_type} {name} {target_type} {value}"


def store(host, ip):
    global address_map
    host = shorten(str(host).rstrip('.'))

    if isinstance(ip, ipaddress.IPv4Address):
        address_map.setdefault(''.join([str(host).rstrip('.'), '4']), []).append(ip)
    elif isinstance(ip, ipaddress.IPv6Address):
        address_map.setdefault(''.join([str(host).rstrip('.'), '6']), []).append(ip)


def render_to_set():
    for host, addresses in address_map.items():
        addresses.sort()
        i = 0

        for address in addresses:
            if len(addresses) > 1:
                # We've got more than one address of this family - tack on a -n
                i += 1

            address_sets.setdefault(host.rstrip('46'), []).append(format_name(host, i))
            print(format_entry(cli_args.address_book, 'address', format_name(host, i), address))

    for host, addresses in address_sets.items():
        if cli_args.delete:
            print(format_set_entry('delete', cli_args.address_book, 'address-set', host))

        for address in addresses:
            print(format_set_entry('set', cli_args.address_book, 'address-set', host, 'address', address))

    if cli_args.s:
        if cli_args.delete:
            print(format_set_entry('delete', cli_args.address_book, 'address-set', cli_args.s))

        for host in address_sets.keys():
            print(format_set_entry('set', cli_args.address_book, 'address-set', cli_args.s, 'address-set', host))


def indented_print(text, level):
    print(('    ' * level) + text)


def render_to_config():
    # Please excuse the mess - I didn't feel like writing a full on recursive config generator for generating a snippet
    indented_print('security {', 0)
    indented_print('address-book {', 1)
    indented_print(cli_args.address_book + ' {', 2)

    for host, addresses in address_map.items():
        addresses.sort()
        i = 0
        for address in addresses:
            if len(addresses) > 1:
                i += 1

            address_sets.setdefault(host.rstrip('46'), []).append(format_name(host, i))
            indented_print('address ' + format_name(host, i) + ' ' + str(address) + ';', 3)

    for host, addresses in address_sets.items():
        indented_print('address-set ' + host + ' {', 3)
        for address in addresses:
            indented_print('address ' + address + ';', 4)
        indented_print('}', 3)

    if cli_args.s:
        indented_print('address-set ' + cli_args.s + ' {', 3)
        for host in address_sets.keys():
            indented_print('address-set ' + host + ';', 4)
        indented_print('}', 3)

    indented_print('}', 2)
    indented_print('}', 1)
    indented_print('}', 0)


def main(*args, **kwargs):
    global address_map, address_sets, cli_args
    cli_args = parser.parse_args()

    address_map = {}

    for domain in cli_args.fqdn:
        # First, are we doing a backward resolution of a subnet or address?
        try:
            net = ipaddress.ip_network(domain)

            if (net.num_addresses > 1024 and not cli_args.dos_my_dns_server):
                print(f"{net.num_addresses} addresses requested - please use '--dos-my-dns-server' to recursively build anything larger than a /22")
                sys.exit(1)
            for ip in net.hosts():
                try:
                    host = dns.resolver.resolve(dns.reversename.from_address(str(ip)), 'PTR')

                    # Rather than store the resulting address, modify cli_args.fqdn and fall through to allow other addresses to resolve. Lazy, but effective
                    [cli_args.fqdn.append(x.to_text()) for x in host]
                except (dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
                    # No PTR at this address
                    pass
                continue
        except ValueError:
            # Not a network or an IP
            pass

        # Must be a forward lookup - canonise the name
        cname = dns.resolver.canonical_name(domain)

        if not cli_args.ip4:
            try:
                ips = dns.resolver.resolve(cname, 'AAAA')
                [store(domain, ipaddress.ip_address(str(x))) for x in ips]
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
                # No addresses of this family
                pass

        if not cli_args.ip6:
            try:
                ips = dns.resolver.resolve(cname, 'A')
                [store(domain, ipaddress.ip_address(str(x))) for x in ips]
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
                # No addresses of this family
                pass

    if not address_map:
        print("No addresses found - make sure that provided hosts are both forward and reverse resolvable")
        sys.exit(1)

    if cli_args.config:
        render_to_config()
        sys.exit(0)

    render_to_set()
    sys.exit(0)


if __name__ == "__main__":
    main()
