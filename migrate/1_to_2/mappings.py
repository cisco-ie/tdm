#!/usr/bin/env python
"""Copyright 2019 Cisco Systems

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
"""Extremely ugly migration."""
import logging
import json
import yang_parser

def parse_repository(repo_path):
    modules = yang_parser.parse_repository(repo_path)
    parsed_modules = {}
    for module_key, module_revision in modules.items():
        revision_with_data = set()
        for revision_key, module in module_revision.items():
            revision_data = None
            try:
                revision_data = __parse_node_attrs(module, module)
            except Exception:
                logging.exception("Failure while parsing %s!", module_key)
            if not revision_data:
                logging.debug("%s@%s is empty.", module_key, revision_key)
                continue
            revision_with_data.add("%s@%s" % (module_key, revision_key))
            if module_key in parsed_modules.keys() and parsed_modules[module_key]:
                logging.warn(
                    "%s being replaced with %s@%s! Only one revision should be used.",
                    module_key,
                    module_key,
                    revision_key,
                )
            parsed_modules[module_key] = revision_data
        if revision_with_data:
            logging.debug("%s have data.", ", ".join(revision_with_data))
        else:
            logging.debug("%s has no revisions with data.", module_key)
    return parsed_modules


def __parse_node_attrs(node, base_module):
    if not hasattr(node, "i_children"):
        return {}
    children = (
        child
        for child in node.i_children
        if child.keyword in yang_parser.statements.data_definition_keywords
    )
    parsed_children = {}
    multi_map = {}
    for child in children:
        qualified_xpath = yang_parser.get_xpath(
            child, qualified=True, prefix_to_module=True
        )
        if qualified_xpath in parsed_children.keys():
            logging.debug("%s encountered more than once! Muxing." % qualified_xpath)
            if qualified_xpath not in multi_map.keys():
                multi_map[qualified_xpath] = 0
            multi_map[qualified_xpath] += 1
            qualified_xpath += "_%i" % multi_map[qualified_xpath]
        attr_dict = {
            '1_machine_id': '%s%s' % (base_module.arg, yang_parser.old_get_xpath(child, with_prefixes=True)),
            '2_machine_id': '/%s' % ('/'.join(map(lambda x: ':'.join(x), yang_parser.mk_path_list(child)))),
            'children': __parse_node_attrs(child, base_module)
        }
        parsed_children[qualified_xpath] = attr_dict
    return parsed_children

logging.basicConfig(level=logging.INFO)

upgrade_map = {}

# Any paths come out missing, go to instance of TDM
# Datapath Direct the path and add path to version folder
repository_paths = [
    'yang/vendor/cisco/nx/9.3-1',
    'yang/vendor/cisco/xe/16111',
    'yang/vendor/cisco/xr/602',
    'yang/vendor/cisco/xr/631',
    'yang/vendor/cisco/xr/662'
]

found = 0
missing = 0

def upgrade(key):
    if key in upgrade_map.keys():
        global found
        found += 1
        return upgrade_map[key]
    else:
        global missing
        if not key.startswith('1.'):
            missing += 1
            logging.warning('%s not in upgrade map!', key)
        return key

for repo in repository_paths:
    logging.info('Parsing %s ...', repo)
    modules = parse_repository(repo)
    def recurse_nodes(node_tree):
        for node_element in node_tree.values():
            upgrade_map[node_element['1_machine_id']] = node_element['2_machine_id']
            recurse_nodes(node_element['children'])
    module_top_children = {}
    for top_children in modules.values():
        module_top_children.update(top_children)
    recurse_nodes(module_top_children)
tdm_mappings = None
with open('tdm_mappings.json', 'r') as mappings_fd:
    tdm_mappings = json.load(mappings_fd)
logging.info('Upgrading DataPathMatch ...')
for match in tdm_mappings['DataPathMatch']:
    match['_from'] = upgrade(match['_from'])
    match['_to'] = upgrade(match['_to'])
logging.info('%i found, %i missing.', found, missing)
found = 0
missing = 0
logging.info('Upgrading Calculation ...')
for calculation in tdm_mappings['Calculation']:
    new_in_calculation = []
    for path in calculation['InCalculation']:
        new_in_calculation.append(upgrade(path))
    calculation['InCalculation'] = new_in_calculation
    new_result = []
    for path in calculation['CalculationResult']:
        new_result.append(upgrade(path))
    calculation['CalculationResult'] = new_result
logging.info('%i found, %i missing.', found, missing)
with open('upgraded_tdm_mappings.json', 'w') as upgraded_fd:
    json.dump(tdm_mappings, upgraded_fd, indent=4, sort_keys=True)
