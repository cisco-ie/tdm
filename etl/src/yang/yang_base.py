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
"""Provide TDM specific functionality for transforming YANG.
TODO: Revise with yang_parser.py
"""
import os
import logging
from pyang import statements
from . import yang_parser

class YANGBase:

    def __init__(self, base_models_path, os_models_path, version_folder_map):
        self.base_models_path = base_models_path
        self.os_models_path = os_models_path
        self.version_folder_map = version_folder_map
        self.fq_os_models_path = self.get_fq_os_models_path()
        self.version_path_map = self.get_version_path_map()

    def get_version_path_map(self):
        return {
            version: os.path.join(self.fq_os_models_path, version_folder)
            for version, version_folder in self.version_folder_map.items()
        }

    def get_fq_os_models_path(self):
        """Fully qualifies OS model file paths."""
        return os.path.join(self.base_models_path, self.os_models_path)

    def get_version_path(self, version):
        """Get the path for the specified release."""
        version_path = None
        try: 
            version_path = os.path.join(
                self.fq_os_models_path, 
                self.version_folder_map[version]
            )
        except Exception:
            raise ValueError('Version does not exist!')
        return version_path

    def parse_versions(self):
        """Parse all the Releases and their corresponding DataModels."""
        version_module_map = {}
        for version, version_path in self.version_path_map.items():
            version_data = version_module_map[version] = {}
            modules = yang_parser.parse_repository(version_path)
            logging.info('Found %d module(s) for %s.', len(modules.keys()), version)
            for module_key, module_revision in modules.items():
                module_data = version_data[module_key] = {}
                for revision_key, module in module_revision.items():
                    module_data[revision_key] = self.parse_module_oper_attrs(module)
                logging.debug('Parsed %d revision(s) for %s.', len(module_data.keys()), module_key)
            logging.debug('Parsed %d module(s) for %s.', len(version_data.keys()), version)
        logging.debug('Parsed %d version(s).', len(version_module_map.keys()))
        return version_module_map

    def parse_module_oper_attrs(self, module):
        """Parse out the readable DataPaths from parsed data models.
        """
        if not hasattr(module, 'i_children'):
            return {}
        module_children = (
            child for child in module.i_children
            if child.keyword in statements.data_definition_keywords
        )
        parsed_modules = {}
        for child in module_children:
            attr_dict = {
                'machine_id': '/%s' % ('/'.join(map(lambda x: ':'.join(x), yang_parser.mk_path_list(child)))),
                'qualified_xpath': yang_parser.get_xpath(child, qualified=True, prefix_to_module=True),
                'xpath': yang_parser.get_xpath(child, prefix_to_module=True),
                'type': yang_parser.get_qualified_type(child),
                'primitive_type': yang_parser.get_primitive_type(child),
                'rw': True if getattr(child, 'i_config', False) else False,
                'description': yang_parser.get_description(child),
                'children': self.parse_module_oper_attrs(child)
            }
            parsed_modules[attr_dict['machine_id']] = attr_dict
        return parsed_modules
