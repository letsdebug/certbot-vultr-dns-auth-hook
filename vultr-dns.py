#!/usr/bin/env python

import requests
import sys
import os
from time import sleep

# Configure here
VULTR_API_KEY = "put your api key here"
VULTR_BIND_DELAY = 60


def vultr_request(method, path, json=None):
    url = "https://api.vultr.com/v2{}".format(path)

    resp = requests.request(
        method,
        url,
        json=json,
        headers={"Authorization": "Bearer " + VULTR_API_KEY},
    )
    resp.raise_for_status()
    if resp.headers["Content-Type"] == "application/json":
        return resp.json()
    return resp.text


def normalize_fqdn(fqdn):
    return fqdn.lower()


def find_zone_for_name(domain):
    """
    https://www.vultr.com/api/#operation/list-dns-domains
    """
    resp = vultr_request("GET", "/domains")
    zones = [entry["domain"] for entry in resp["domains"]]

    # api doesn't have a trailing . on its zones
    if domain[-1:] == ".":
        domain = domain[:-1]

    domain_split = domain.split(".")
    while len(domain_split) > 0:
        search = ".".join(domain_split)
        if search in zones:
            return search
        domain_split = domain_split[1:]

    raise Exception("Could not identify existing zone for {}".format(domain))


def list_records(zone):
    """
    https://www.vultr.com/api/#operation/list-dns-domain-records
    """
    return vultr_request("GET", "/domains/{}/records".format(zone))


def create_record(domain, txt_value):
    """
    https://www.vultr.com/api/#operation/create-dns-domain-record
    """
    to_add = normalize_fqdn("_acme-challenge.{}".format(domain))
    print("Creating {} TXT: {}".format(to_add, txt_value))
    zone = find_zone_for_name(domain)
    create_params = {
        "name": "_acme-challenge",
        "type": "TXT",
        "data": '"{}"'.format(txt_value),
    }
    
    vultr_request("POST", "/domains/{}/records".format(zone), json=create_params)

    print(
        "Will sleep {} seconds to wait for DNS cluster to reload".format(
            VULTR_BIND_DELAY
        )
    )
    sleep(VULTR_BIND_DELAY)


def remove_record(domain, txt_value):
    """
    https://www.vultr.com/api/#operation/delete-dns-domain-record
    """
    to_remove = normalize_fqdn("_acme-challenge.{}".format(domain))
    zone = find_zone_for_name(to_remove)
    recs = list_records(zone)["records"]

    print("Removing {} TXT: {}".format(to_remove, txt_value))

    to_remove = to_remove[: -len(zone) - 1]

    found = list(
        filter(
            lambda rec: "name" in rec
            and rec["name"] == to_remove
            and "type" in rec
            and rec["type"] == "TXT"
            and rec["data"] == '"{}"'.format(txt_value),
            recs,
        )
    )

    if len(found) == 0:
        print(
            "Could not find record to remove: {} with value {}".format(
                to_remove, txt_value
            )
        )
        return

    vultr_request("DELETE", "/domains/{}/records/{}".format(zone, found[0]["id"]))


act = sys.argv[1]

if act == "create":
    create_record(os.environ["CERTBOT_DOMAIN"], os.environ["CERTBOT_VALIDATION"])
elif act == "delete":
    remove_record(os.environ["CERTBOT_DOMAIN"], os.environ["CERTBOT_VALIDATION"])
else:
    print("Unknown action: {}".format(act))
    exit(1)
