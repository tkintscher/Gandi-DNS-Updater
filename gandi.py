#!/usr/bin/env python3

import argparse
import json
import socket
# import subprocess
import urllib.parse
import urllib.request


SELF_RESOLVE_URL = 'http://ifconfig.co'
GANDI_API_URL    = 'https://dns.api.gandi.net/api/v5'



def get_own_address(ipv4=False):
    '''
    Return the (external) IP address of this machine.
    An IPv6 address is returned, unless `ipv4` is set to `True`.

    The external IP address is obtained using the service of `ifconfig.co`.
    '''

    ## ugly alternative calling curl:
    # curl = subprocess.run(['curl', '-4' if ipv4 else '-6', SELF_RESOLVE_URL],
    #                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # return curl.stdout.strip().decode('ascii')

    # resolve provider url to ipv4 or ipv6 address
    url      = SELF_RESOLVE_URL
    url_host = urllib.parse.urlsplit(url).hostname
    url_ip   = socket.getaddrinfo(host=url_host, port=None,
                                  family=socket.AF_INET if ipv4 else socket.AF_INET6,
                                  type=socket.SOCK_STREAM)[0][4][0]
    if not ipv4:
        url_ip = '[{url_ip}]'.format(**locals())

    req = urllib.request.Request(url.replace(url_host, url_ip))
    req.add_header('Host', url_host)
    req.add_header('User-Agent', 'curl/7.21.3 (x86_64-unknown-linux-gnu) libcurl/7.21.3 OpenSSL/1.0.0c zlib/1.2.5')
    with urllib.request.urlopen(req) as conn:
        return conn.read().strip().decode('ascii')


def get_address(hostname, ipv4=False):
    '''
    Resolve the given hostname to an IP address.
    An IPv6 address is returned, unless `ipv4` is set to `True`.
    '''
    addresses = socket.getaddrinfo(host=hostname, port=None, type=socket.SOCK_STREAM)
    for family, _, _, (address, _, _, _) in addresses:
        if family == (socket.AF_INET if ipv4 else socket.AF_INET6):
            return address


def get_address_family(address):
    for version, family in [ (4, socket.AF_INET), 
                             (6, socket.AF_INET6) ]:
        try:
            socket.inet_pton(family, address)
            return version
        except OSError:
            pass

    return False


def gandi_post(apikey, endpoint, data=None):
    '''
    Send `data` to a Gandi API `endpoint`.
    '''
    url     = GANDI_API_URL + endpoint
    data    = json.dumps(data).encode('utf-8') if (data is not None) else None
    headers = { 'X-Api-Key': apikey }
    method  = 'GET' if (data is None) else 'PUT'

    if data is not None:
        headers['Content-Type'] = 'application/json'

    req  = urllib.request.Request(url, headers=headers, data=data, method=method)

    with urllib.request.urlopen(req) as conn:
        return json.loads(conn.read().decode('utf-8'))

def get_zone_uuid(apikey, domain):
    '''
    Get the Gandi-internal UUID for a `domain`.
    '''
    return gandi_post(apikey, '/domains/'+domain)['zone_uuid']

def get_zone_config(apikey, uuid, subdomain, rec_type):
    '''
    Get the configuration for a `subdomain`, which lies inside the domain
    identified by the `uuid`.

    The UUID for a domain can be looked up with the `get_zone_uuid` function.
    '''
    assert rec_type in [ 'A', 'AAAA' ]
    return gandi_post(apikey, '/zones/'+uuid+'/records/'+subdomain+'/'+rec_type)

def set_zone_config(apikey, uuid, subdomain, rec_type, ttl, value):
    '''
    Set configuration `value`s for a `subdomain`, which lies inside the domain
    identified by the `uuid`.

    The UUID for a domain can be looked up with the `get_zone_uuid` function.
    '''
    return gandi_post(apikey, '/zones/'+uuid+'/records/'+subdomain+'/'+rec_type,
                      { 'rrset_ttl': ttl,
                        'rrset_values': [ value ]
                      })


#
# Command-line utility
#
if __name__ == '__main__':
    # command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('api_key',   metavar='GANDI_API_KEY',        help='Gandi API key')
    parser.add_argument('domain',    metavar='subdomain.domain.tld', help='Domain to be updated')
    parser.add_argument('type',      choices=['A', 'AAAA'],          help='IPv4 (A) or v6 (AAAA)')
    parser.add_argument('address',   nargs='?',                      help='IP address to be set')
    args = parser.parse_args()

    assert args.domain.count('.') == 2
    subdomain, domain = args.domain.split('.', 1)
    rec_type          = args.type
    ipv4              = (rec_type == 'A')

    if args.address is None:
        # if no address is given, determine the external address of this machine
        local_address = get_own_address(ipv4)
    elif not get_address_family(args.address):
        # resolve the given address to an IP address
        local_address = get_address(args.address, ipv4)
    else:
        # address seems to be a valid IP address already
        version = get_address_family(args.address)
        assert ((version == 4) and (args.type == 'A')) \
            != ((version == 6) and (args.type == 'AAAA'))
        local_address = args.address
    print('Local address:', local_address)

    # get Gandi's UUID for the domain
    uuid = get_zone_uuid(args.api_key, domain)
    print('Zone UUID:', uuid)

    # get configuration for the subdomain under the UUID
    config = get_zone_config(args.api_key, uuid, subdomain, rec_type)

    # update if necessary
    print('Current value:', config['rrset_values'][0])
    if config['rrset_values'][0] == local_address:
        print('Nothing to be done.')
    else:
        set_zone_config(args.api_key, uuid, subdomain, rec_type,
                        config['rrset_ttl'], local_address)
        print('Updated zone configuration.')
