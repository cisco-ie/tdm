#!/usr/bin/env python
"""
Copyright 2018 Cisco Systems

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
"""The entry point of the TDM ETL process.
This file initializes the ETL process and calls all
necessary functionality.
"""

import logging
import json
import socket
import errno
import time
from urllib.parse import urlparse
from pyArango.connection import Connection
from models import create_schema
from static import populate_static
from yang import populate_yang
from snmp import populate_snmp
from search import populate_search

def load_config(filename='config.json'):
    config = None
    with open(filename, 'r') as config_fd:
        config = json.load(config_fd)
    return config

def await_url(url, interval=3):
    """Await a certain URL to be open.
    url expects a port parameter in url string.
    Adapted from:
    http://code.activestate.com/recipes/576655-wait-for-network-service-to-appear/
    """
    url_attrs = urlparse(url)
    sock = socket.socket()
    connected = False
    while not connected:
        try:
            sock.connect((url_attrs.hostname, url_attrs.port))
        except Exception:
            time.sleep(interval)
        else:
            sock.close()
            connected = True

def create_database(conn):
    """Create the database if it does not exist."""
    db = None
    if conn.hasDatabase('tdm'):
        db = None
    else:
        db = conn.createDatabase('tdm')
    return db

def main():
    """Entry point."""
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.info('Loading configuration.')
    config = load_config()
    logging.info('Awaiting DBMS availability.')
    await_url(config['arango']['arangoURL'])
    logging.info('Awaiting DBMS connectivity.')
    conn = None
    while conn == None:
        try:
            conn = Connection(**config['arango'])
        except:
            time.sleep(3)
    logging.info('Creating database.')
    db = create_database(conn)
    if not db:
        logging.error('TDM database already exists! Not overwriting.')
    else:
        logging.info('Creating database schema.')
        create_schema(db)
        logging.info('Populating static data.')
        populate_static(db)
        logging.info('Populating MIB data.')
        populate_snmp(db)
        logging.info('Populating YANG data.')
        populate_yang(db)
        logging.info('Populating search database with parsed data.')
        populate_search(db)
        logging.info('ETL process complete!')


if __name__ == '__main__':
    main()
