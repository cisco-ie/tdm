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
"""Load YANG models in to the database representation
of OS/Releases/DataModels/DataPaths/DataTypes. Heavy parsing.
Extremely non-optimal. ~10GB memory usage.
"""
import os
import json
import logging
from .yang_base import YANGBase

"""Commented out releases have model bugs.
TODO: Resolve model bugs.
TODO: Move to a configuration file somehow.
"""
os_version_folder_map = {
    'nx': {
        '7.0(3)F1(1)': '7.0-3-F1-1',
        '7.0(3)F2(1)': '7.0-3-F2-1',
        '7.0(3)F2(2)': '7.0-3-F2-2',
        '7.0(3)I5(1)': '7.0-3-I5-1',
        '7.0(3)I5(2)': '7.0-3-I5-2',
        '7.0(3)I6(1)': '7.0-3-I6-1',
        '7.0(3)I6(2)': '7.0-3-I6-2',
        '7.0(3)I7(1)': '7.0-3-I7-1',
        '7.0(3)I7(2)': '7.0-3-I7-2',
        '7.0(3)I7(3)': '7.0-3-I7-3',
        '7.0(3)I7(4)': '7.0-3-I7-4',
        '9.2(1)': '9.2-1',
        '9.2(2)': '9.2-2',
        '9.2(3)': '9.2-3'
    },
    'xe': {
        '16.3.1': '1631',
        '16.3.2': '1632',
        '16.4.1': '1641',
        '16.5.1': '1651',
        '16.6.1': '1661',
        '16.6.2': '1662',
        '16.7.1': '1671',
        '16.8.1': '1681',
        '16.9.1': '1691',
        '16.9.3': '1693'
    },
    'xr': {
        '5.3.0': '530',
        '5.3.1': '531',
        '5.3.2': '532',
        '5.3.3': '533',
        '5.3.4': '534',
        '6.0.0': '600',
        '6.0.1': '601',
        '6.0.2': '602',
        '6.1.1': '611',
        '6.1.2': '612',
        '6.1.3': '613',
        '6.2.1': '621',
        '6.2.2': '622',
        '6.3.1': '631',
        '6.3.2': '632',
        '6.4.1': '641',
        '6.4.2': '642',
        '6.5.1': '651',
        '6.5.2': '652',
        '6.5.3': '653',
        '6.6.2': '662',
        '7.0.1': '701'
    }
}

# TODO: Create common functionality for this mapping.
os_map = {
    'nx': 'NX-OS',
    'xe': 'IOS_XE',
    'xr': 'IOS_XR'
}

def acquire_source():
    """Acquire the YANG models in to the
    /data/extract/yang location. Relies on priori knowledge
    to know where to parse.
    TODO: Generalize a priori knowledge to configuration.
    """
    base_path = '/data/extract/'
    yang_base_path = os.path.join(base_path, 'yang/')
    cisco_yang_base_path = os.path.join(yang_base_path, 'vendor/cisco/')
    if os.path.exists(yang_base_path):
        logging.debug('YANG repo exists! Pulling latest models.')
        os.system('cd %s && git pull' % yang_base_path)
    else:
        logging.debug('Cloning YANG repo for first time.')
        os.system('cd %s && git clone --recursive https://github.com/cisco-ie/yang.git -b fix-ietf-types-cisco' % base_path)
        logging.debug('Cloned to %s.', yang_base_path)
    return cisco_yang_base_path

# TODO: Optimize the caches.
dm_cache = {}
dp_cache = {}
dt_cache = {}
# This is the most memory inefficient thing I've ever done.
dm_dp_cache = set()
dp_dt_cache = set()
dp_link_cache = set()

# TODO: Revise everything beneath this line.
def populate_yang(db):
    """Entry point of populating YANG data."""
    logging.info('Acquiring YANG models for data extraction.')
    base_model_path = acquire_source()
    for os_key, version_map in os_version_folder_map.items():
        logging.info('Transforming %s data.', os_map[os_key])
        versioned_data = YANGBase(
            base_model_path,
            os_key,
            version_map
        ).parse_versions()
        logging.debug('Resetting session to mitigate session timeout (???).')
        db.connection.resetSession('root', 'tdm')
        for version, modules in versioned_data.items():
            logging.info('Loading %s %s data.', os_map[os_key], version)
            add_version_modules(db, os_key, version, modules)

def add_version_modules(db, os_key, version, modules):
    """Add the DataModels to the corresponding OS/Release."""
    version_key = '%s+%s' % (os_map[os_key], version)
    version_node = db['Release'][version_key]
    dml_node = db['DataModelLanguage']['YANG']
    for module_name, revisions in modules.items():
        parent_dm = None
        for revision in sorted(revisions.keys()):
            module = revisions[revision]
            dm_key = '%s+%s' % (module_name, revision)
            dm_node = None
            if dm_key in dm_cache.keys():
                dm_node = dm_cache[dm_key]
            else:
                dm_node = db['DataModel'].createDocument({
                    '_key': dm_key,
                    'name': module_name,
                    'revision': revision,
                    'content': None,
                    'parsed_checksum': None
                })
                db['OfDataModelLanguage'].createEdge().links(dml_node, dm_node)
                dm_cache[dm_key] = dm_node
            if parent_dm is not None:
                db['DataModelParent'].createEdge().links(dm_node, parent_dm, waitForSync=True)
                db['DataModelChild'].createEdge().links(parent_dm, dm_node, waitForSync=True)
            parent_dm = dm_node
            db['ReleaseHasDataModel'].createEdge().links(version_node, dm_node, waitForSync=True)
            add_data_paths_to_dm(db, dm_node, module)

def add_data_paths_to_dm(db, dm_node, module, dp_parent=None):
    """Add the parsed DataPaths from the corresponding DataModels."""
    for _, path_data in module.items():
        path_key = path_data['machine_id']
        path_node = None
        if path_key in dp_cache.keys():
            path_node = dp_cache[path_key]
        else:
            path_node = db['DataPath'].createDocument({
                'machine_id': path_key,
                'human_id': path_data['xpath'],
                'description': path_data['description'],
                'is_leaf': False if path_data['children'] else True,
                'is_variable': False,
                'is_configurable': path_data['rw'],
                'verified': False
            })
            dp_cache[path_key] = path_node
        if {dm_node['_key'], path_node['_key']} not in dm_dp_cache:
            db['DataPathFromDataModel'].createEdge().links(dm_node, path_node, waitForSync=True)
            dm_dp_cache.add(frozenset({dm_node['_key'], path_node['_key']}))
        if path_data['primitive_type'] is not None:
            type_node = None
            type_key = 'YANG+%s' % path_data['primitive_type']
            if type_key in dt_cache.keys():
                type_node = dt_cache[type_key]
            else:
                try:
                    type_node = db['DataType'][type_key]
                    dt_cache[type_key] = type_node
                except KeyError:
                    logging.error('Could not resolve DataType %s!', type_key)
                    raise
            if {path_node['_key'], type_node['_key']} not in dp_dt_cache:
                db['OfDataType'].createEdge().links(path_node, type_node, waitForSync=True)
                dp_dt_cache.add(frozenset({path_node['_key'], type_node['_key']}))
        if dp_parent is not None and {dp_parent['_key'], path_node['_key']} not in dp_link_cache:
            db['DataPathChild'].createEdge().links(dp_parent, path_node, waitForSync=True)
            db['DataPathParent'].createEdge().links(path_node, dp_parent, waitForSync=True)
            dp_link_cache.add(frozenset({dp_parent['_key'], path_node['_key']}))
        if path_data['children']:
            add_data_paths_to_dm(db, dm_node, path_data['children'], path_node)
