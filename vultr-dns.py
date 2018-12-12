#!/usr/bin/env python

import requests
import sys
import os
import string
from time import sleep

# Configure here
VULTR_API_KEY = "put your api key here"
VULTR_BIND_DELAY = 30


def vultr_request(method, path, data=None):
    url = "https://api.vultr.com/v1{}".format(path)

    resp = requests.request(method, url, data=data, headers={
                            "API-Key": VULTR_API_KEY})
    resp.raise_for_status()
    if resp.headers['Content-Type'] == 'application/json':
        return resp.json()
    return resp.text


def normalize_fqdn(fqdn):
    fqdn = string.lower(fqdn)
    return fqdn


def find_zone_for_name(domain):
    resp = vultr_request("GET", "/dns/list")
    zones = [entry['domain'] for entry in resp]

    # api doesn't have a trailing . on its zones
    if domain[-1:] == '.':
        domain = domain[:-1]

    domain_split = domain.split('.')
    while len(domain_split) > 0:
        search = string.join(domain_split, ".")
        if search in zones:
            return search
        domain_split = domain_split[1:]

    raise Exception("Could not identify existing zone for {}".format(domain))


def list_records(zone):
    return vultr_request("GET", "/dns/records?domain={}".format(zone))


def create_record(domain, txt_value):
    to_add = normalize_fqdn('_acme-challenge.{}'.format(domain))
    print("Creating {} TXT: {}".format(to_add, txt_value))
    zone = find_zone_for_name(domain)
    create_params = {'domain': zone, 'name': to_add, 'type': 'TXT',
                     'data': '"{}"'.format(txt_value)}
    vultr_request("POST", "/dns/create_record", create_params)

    print("Will sleep {} seconds to wait for DNS cluster to reload".
          format(VULTR_BIND_DELAY))
    sleep(VULTR_BIND_DELAY)


def remove_record(domain, txt_value):
    to_remove = normalize_fqdn("_acme-challenge.{}".format(domain))
    zone = find_zone_for_name(to_remove)
    recs = list_records(zone)

    print "Removing {} TXT: {}".format(to_remove, txt_value)

    to_remove = to_remove[:-len(zone)-1]

    found = filter(
        lambda rec:
            'name' in rec and rec['name'] == to_remove and
            'type' in rec and rec['type'] == 'TXT' and
            rec['data'] == '"{}"'.format(txt_value),
        recs)

    if len(found) == 0:
        print("Could not find record to remove: {} with value {}".
              format(to_remove, txt_value))
        return

    delete_params = {'domain': zone, 'RECORDID': found[0]['RECORDID']}
    vultr_request("POST", "/dns/delete_record", delete_params)


act = sys.argv[1]

if act == "create":
    create_record(os.environ["CERTBOT_DOMAIN"],
                  os.environ["CERTBOT_VALIDATION"])
elif act == "delete":
    remove_record(os.environ["CERTBOT_DOMAIN"],
                  os.environ["CERTBOT_VALIDATION"])
else:
    print("Unknown action: {}".format(act))
    exit(1)
