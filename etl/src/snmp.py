#!/usr/bin/env python3
"""Copyright 2018 Cisco Systems

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
import os
import sys
import json
from ftplib import FTP
from pysmi.reader import FileReader
from pysmi.searcher import AnyFileSearcher, StubSearcher
from pysmi.writer import FileWriter
from pysmi.parser import SmiV1CompatParser
from pysmi.codegen import JsonCodeGen
from pysmi.compiler import MibCompiler
from pysmi import error
from pysmi import debug
import logging


class SNMPPopulator:
    protocol = None
    host = None
    base_path = None
    local_mib_dir = None
    local_json_dir = None
    new_json_dir = None
    donotdo_mibs = []
    exclude_mibs = []

    def __init__(self, protocol='ftp', host='ftp.cisco.com', base_path='pub/mibs/v2',
                 local_mib_dir='mibs/', local_json_dir='mibjson/', new_json_dir='newmibjson/',
                 abs_local_dir=False
                 ):
        self.protocol = protocol
        self.host = host
        self.base_path = base_path
        local_dir = os.path.dirname(os.path.abspath(__file__))
        if not abs_local_dir:
            self.local_mib_dir = os.path.join(local_dir, local_mib_dir)
            self.local_json_dir = os.path.join(local_dir, local_json_dir)
            self.new_json_dir = os.path.join(local_dir, new_json_dir)
        else:
            self.local_mib_dir = local_mib_dir
            self.local_json_dir = local_json_dir
            self.new_json_dir = new_json_dir

    def gen_full_hostpath(self):
        return '{0}://{1}/{2}'.format(self.protocol, self.host, self.base_path)

    def download_mibs(self, specific_mibs=None, exclude_mibs=[], refresh=False):
        logging.info(
            'Downloading MIBs from %s/%s to %s',
            self.host, self.base_path, self.local_mib_dir
        )
        with FTP(self.host) as ftp:
            ftp.login()
            mib_filenames = []
            if specific_mibs is None:
                ftp.retrlines(
                    'NLST {0}/*'.format(self.base_path),
                    callback=lambda filename: mib_filenames.append(filename)
                )
            else:
                mib_filenames = specific_mibs.copy()
            num_mibs = len(mib_filenames)
            logging.debug('%i MIBs to download.', num_mibs)
            if not os.path.isdir(self.local_mib_dir):
                os.makedirs(self.local_mib_dir)
            counter = 1
            for filename in mib_filenames:
                try:
                    filename.rindex('.my', -3)
                except:
                    logging.debug('Not a MIB.')
                    counter += 1
                    continue
                logging.debug('MIB %i/%i: %s', counter, num_mibs, filename)
                if filename in exclude_mibs:
                    logging.debug('Excluding.')
                    counter += 1
                    continue
                if not refresh and os.path.isfile(os.path.join(self.local_mib_dir, filename)):
                    logging.debug('Skipping.')
                    counter += 1
                    continue
                with open(os.path.join(self.local_mib_dir, filename), 'wb') as mib_file:
                    ftp.retrbinary(
                        'RETR {0}/{1}'.format(self.base_path, filename),
                        callback=lambda data: mib_file.write(data)
                    )
                counter += 1
        logging.info('Finished downloading MIBs.')
        return True

    def transform_mibs_to_json(self, specific_mibs: object = None, exclude_mibs: object = []) -> object:
        mib_names = []
        if specific_mibs is None:
            for filename in os.listdir(self.local_mib_dir):
                try:
                    filename.rindex('.my', -3)
                except:
                    continue
                mib_names.append(filename)
        else:
            mib_names = specific_mibs.copy()
        logging.info('Compiling MIBs to JSON.')
        try:
            mib_compiler = MibCompiler(
                SmiV1CompatParser(),
                JsonCodeGen(),
                FileWriter(self.local_json_dir).setOptions(suffix='.json')
            )
            mib_compiler.addSources(FileReader(self.local_mib_dir, recursive=True))
            mib_stubs = JsonCodeGen.baseMibs
            searchers = [AnyFileSearcher(self.local_json_dir).setOptions(exts=['.json']), StubSearcher(*mib_stubs)]
            mib_compiler.addSearchers(*searchers)
            if not os.path.isdir(self.local_json_dir):
                os.makedirs(self.local_json_dir)
            processed = mib_compiler.compile(
                *mib_names,
                **dict(
                    noDeps=False,
                    rebuild=True,
                    genTexts=True,
                    writeMibs=True,
                    ignoreErrors=True
                )
            )
            mib_compiler.buildIndex(
                processed,
                ignoreErrors=True
            )
        except error.PySmiError:
            logging.error('ERROR: %s', str(sys.exc_info()[1]))
            sys.exit(1)
        logging.info('Finished compiling MIBs to JSON.')

    def transform_json_to_new(self, specific_mibs=None):
        json_names = []
        logging.info(
            'Reorganizing JSON MIBs and writing to %s',
            self.new_json_dir
        )
        if specific_mibs is None:
            for filename in os.listdir(self.local_json_dir):
                try:
                    filename.rindex('.json', -5)
                except:
                    continue
                json_names.append(filename)
        else:
            json_names = specific_mibs.copy()
        num_json = len(json_names)
        counter = 1
        logging.debug('%i JSON to transform.', num_json)
        if not os.path.isdir(self.new_json_dir):
            os.makedirs(self.new_json_dir)
        for filename in json_names:
            file_path = os.path.join(self.local_json_dir, filename)
            logging.debug('JSON %i/%i: %s', counter, num_json, filename)
            with open(file_path, 'r', encoding='utf8') as f:
                data = json.load(f)
                def create_oid_dict(data):
                    oid = {}
                    oidname = data['oid']
                    oid[oidname] = {}
                    oid[oidname]['oid'] = data['oid']
                    oid[oidname]['name'] = data['name']
                    if ('description') in data:
                        oid[oidname]["description"] = data['description']
                    else:
                        oid[oidname]["description"] = ''

                    if ('syntax') in data:
                        oid[oidname]['dataType'] = data['syntax']['type']
                    else:
                        oid[oidname]['dataType'] = ''
                    return oid
                newdict = {}
                for i in data:
                    if ('oid') in data[i]:
                        newdict.update(create_oid_dict(data[i]))
                new_file_path = os.path.join(self.new_json_dir, filename)
                with open(new_file_path, 'w') as f:
                    json.dump(newdict, f, indent=4)
            counter += 1
        
    def parse_json_to_db(self, db):
        json_filenames = []
        for filename in os.listdir(self.new_json_dir):
            try:
                filename.rindex('.json', -5)
            except:
                continue
            json_filenames.append(filename)
        if not json_filenames:
            logging.error('No files to parse into db!')
            return
        logging.debug('Resetting session to mitigate session timeout (???).')
        db.connection.resetSession('root', 'tdm')
        oid_cache = {}
        dml_node = db['DataModelLanguage']['SMI']
        for filename in json_filenames:
            model_name = filename[:-5]
            """TODO: THIS IS BARE MINIMUM
            content is the RAW MIB content, not JSON.
            parsed_checksum is md5 checksum of content.
            revision is a field that is in the JSON, but not super easy to see..e.g.
            "ciscoWirelessTextualConventions": {
                "name": "ciscoWirelessTextualConventions",
                "oid": "1.3.6.1.4.1.9.9.137",
                "class": "moduleidentity",
                "revisions": [
                {
                    "revision": "2000-04-03 00:00",
                    "description": "Added TEXTUAL-CONVENTIONs for CwrRfType CwrFixedPointScale CwrFixedPointPrecison CwrFixedPointValue P2mpSnapshotAttribute CwrPercentageValue CwrRfFreqRange CwrUpdateTime Modified P2mpRadioSignalAttribute"
                }
                ],
                "lastupdated": "200004030000Z",
                "organization": "Cisco Systems, Inc.",
                "contactinfo": " Cisco Systems Customer Service Postal: 170 W Tasman Drive San Jose, CA 95134 USA Tel: +1 800 553-NETS E-mail: wireless-nms@cisco.com",
                "description": "This module defines textual conventions used in Cisco Wireless MIBs."
            },
            _key is ideally model_name@revision
            revision is the latest revision, we can't know revision content without having each revision sequentially.
            """
            dm_node = db['DataModel'].createDocument(
                {
                    '_key': model_name,
                    'name': model_name,
                    'revision': None,
                    'content': None,
                    'parsed_checksum': None
                }
            )
            db['OfDataModelLanguage'].createEdge().links(dml_node, dm_node)
            mib_json = None
            file_path = os.path.join(self.new_json_dir, filename)
            with open(file_path, 'r') as json_fd:
                mib_json = json.load(json_fd)
            if not mib_json:
                logging.error('Nothing in %s', filename)
                continue
            for oid, oid_info in mib_json.items():
                """ TODO: THIS IS BARE MINIMUM
                is_leaf should actually check if dataType is a primitive data type defined by SMI/MIB specs.
                If it's defined, and not primitive, then we SHOULD derive the primitive data type of the defined
                data type and check that.
                Look in static.py under SMI for primitive data types derived from RFCs.
                We should also link the DataPath to the corresponding DataType node.
                """
                path_node = None
                if oid in oid_cache.keys():
                    logging.error('Duplicate oid %s from %s in %s!', oid, oid_cache[oid]['model'], model_name)
                    path_node = oid_cache[oid]['obj']
                else:
                    path_node = db['DataPath'].createDocument(
                        {
                            'machine_id': oid,
                            'human_id': oid_info['name'],
                            'description': oid_info['description'],
                            'is_leaf': True if oid_info['dataType'] else False,
                            'is_variable': False,
                            'is_configurable': False,
                            'verified': False
                        }
                    )
                    oid_cache[oid] = {
                        'model': model_name,
                        'obj': path_node
                    }
                db['DataPathFromDataModel'].createEdge().links(dm_node, path_node, waitForSync=True)

def populate_snmp(db):
    """Entry point of populating SNMP data."""
    # TODO: Remove hardcoding of paths.
    # Customized to Docker volume pathing.
    # Files will present locally in etl/cache/... for debugging.
    snmppop = SNMPPopulator(
        local_mib_dir='/data/extract/mib/',
        local_json_dir='/data/transform/mibjson/',
        new_json_dir='/data/transform/newmibjson/',
        abs_local_dir=True
    )
    snmppop.download_mibs()
    snmppop.transform_mibs_to_json()
    snmppop.transform_json_to_new()
    snmppop.parse_json_to_db(db)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    #debug.setLogger(debug.Debug('reader', 'searcher', 'compiler'))
    snmppop = SNMPPopulator()
    snmppop.download_mibs()
    snmppop.transform_mibs_to_json()
    snmppop.transform_json_to_new()
