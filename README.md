A script to generate firewall address book entries for JunOS from DNS. It requires working DNS (especially reverse DNS), but will accept domain names, IP addresses, and CIDR (both v4 and v6). You can give as many entries as you like on the CLI, and mix and match the formats at will.

This was written for my own purposes so it's a little opinionated - all our hosts are dual stacked so we create addresses for the v4 and v6 addresses, and combine them into an address set. To keep things simple and consistent (and keep churn down if a host suddenly gains v6 capability), we still use the top level address-set even if there is only a single address.

We also shrink the last three domain components to keep the config terse - this behaviour can be disabled with the `-n` switch.

Dependencies
============
Runtime: Python 3.6 or greater.

Sample Output
=============

config
------

Note that these are just examples - the output is more logical if you use your own hosts.

```
security {
    address-book {
        foo {
            address reddit.com4-1 151.101.1.140;
            address reddit.com4-2 151.101.65.140;
            address reddit.com4-3 151.101.129.140;
            address reddit.com4-4 151.101.193.140;
            address microsoft.com4-1 13.77.161.179;
            address microsoft.com4-2 40.76.4.15;
            address microsoft.com4-3 40.112.72.205;
            address microsoft.com4-4 40.113.200.201;
            address microsoft.com4-5 104.215.148.63;
            address cloudflare.net4-1 104.16.208.90;
            address cloudflare.net4-2 104.17.156.85;
            address google.com6 2a00:1450:4009:80d::200e;
            address google.com4 216.58.213.14;
            address-set reddit.com {
                address reddit.com4-1;
                address reddit.com4-2;
                address reddit.com4-3;
                address reddit.com4-4;
            }
            address-set microsoft.com {
                address microsoft.com4-1;
                address microsoft.com4-2;
                address microsoft.com4-3;
                address microsoft.com4-4;
                address microsoft.com4-5;
            }
            address-set cloudflare.net {
                address cloudflare.net4-1;
                address cloudflare.net4-2;
            }
            address-set google.com {
                address google.com6;
                address google.com4;
            }
            address-set bar {
                address-set reddit.com;
                address-set microsoft.com;
                address-set cloudflare.net;
                address-set google.com;
            }
        }
    }
}
```

set
---

```
set security address-book foo address reddit.com4-1 151.101.1.140
set security address-book foo address reddit.com4-2 151.101.65.140
set security address-book foo address reddit.com4-3 151.101.129.140
set security address-book foo address reddit.com4-4 151.101.193.140
set security address-book foo address microsoft.com4-1 13.77.161.179
set security address-book foo address microsoft.com4-2 40.76.4.15
set security address-book foo address microsoft.com4-3 40.112.72.205
set security address-book foo address microsoft.com4-4 40.113.200.201
set security address-book foo address microsoft.com4-5 104.215.148.63
set security address-book foo address cloudflare.net4-1 104.16.208.90
set security address-book foo address cloudflare.net4-2 104.17.156.85
set security address-book foo address-set reddit.com address reddit.com4-1
set security address-book foo address-set reddit.com address reddit.com4-2
set security address-book foo address-set reddit.com address reddit.com4-3
set security address-book foo address-set reddit.com address reddit.com4-4
set security address-book foo address-set microsoft.com address microsoft.com4-1
set security address-book foo address-set microsoft.com address microsoft.com4-2
set security address-book foo address-set microsoft.com address microsoft.com4-3
set security address-book foo address-set microsoft.com address microsoft.com4-4
set security address-book foo address-set microsoft.com address microsoft.com4-5
set security address-book foo address-set cloudflare.net address cloudflare.net4-1
set security address-book foo address-set cloudflare.net address cloudflare.net4-2
set security address-book foo address-set bar address-set reddit.com
set security address-book foo address-set bar address-set microsoft.com
set security address-book foo address-set bar address-set cloudflare.net```
```

Usage
=====

```
usage: dns2junos [-h] [-a address-book] [-s address-set] [-n] [-4 | -6] [--set | --config] fqdn [fqdn ...]

Convert a fully qualified domain name to an opinionated JunOS address book entry.

If a subnet is provided, we look up the individual hosts via rDNS. We do not concern ourselves with anything except PTR, CNAME, A and AAAA records - if you want to create an address book entry for a mail server, just give us the FQDN of the mail server - not your mail domain.

positional arguments:
  fqdn

optional arguments:
  -h, --help       show this help message and exit
  -a address-book  Address book name
  -s address-set   Add the entries to an additional address-set
  -n               Don't shorten DNS names
  -4               Only consider IPv4 addresses
  -6               Only consider IPv6 addresses
  --set            Emit output as set commands
  --config         Emit output as raw config

Report bugs at https://github.com/TheMysteriousX/dns2junos/issues
```
