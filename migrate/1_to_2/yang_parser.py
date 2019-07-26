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
"""Parse YANG modules using pyang functionality.
Mainly utility functions manipulating pyang.
"""
import os
import re
import logging
from pyang import Context, FileRepository
from pyang import syntax
from pyang import statements

def parse_repository(repository_path, filter_pattern=''):
    """Parse a directory as a Repository of YANG modules."""
    file_repository = FileRepository(
        path=repository_path,
        use_env=False,
        no_path_recurse=False,
    )
    context = Context(repository=file_repository)
    context.validate()
    module_revs = context.revs
    logging.debug('Found %d module(s) in %s.', len(module_revs.keys()), repository_path)
    if filter_pattern:
        module_revs = get_filtered_modules(context, filter_pattern)
        logging.debug('Filtered to %d module(s).', len(module_revs.keys()))
    modules = parse_modules(context)
    return modules

def parse_modules(context):
    """Parse the unparsed, top-level Modules in a Context.
    TODO: This feels buggy.
    """
    # Force Context to parse all Modules
    for module_name, module_revs in context.revs.copy().items():
        for module_rev in module_revs:
            context.search_module(0, module_name, module_rev[0])
    # Reparse Modules in to a more structured dict
    modules = {}
    for module_meta, module in context.modules.items():
        module_name = module_meta[0]
        module_revision = module_meta[1]
        logging.debug('Found %s@%s', module_name, module_revision)
        if module_name in modules.keys():
            module_set = modules[module_name]
            if module_revision in module_set.keys():
                raise Exception('Module revision referenced more than once!')
            else:
                module_set[module_revision] = module
        else:
            modules[module_name] = {module_revision: module}
    return modules

def parse_module(context, module_file_path):
    """Parse a Module in to a Context."""
    filename = os.path.basename(module_file_path)
    module_data = None
    with open(module_file_path, 'r') as module_fd:
        module_data = module_fd.read()
    # Some model filenames indicate revision, etc.
    filename_attributes = syntax.re_filename.search(filename)
    module = None
    if filename_attributes is None:
        module = context.add_module(filename, module_data)
    else:
        (name, revision, module_format) = filename_attributes.groups()
        module = context.add_module(
            filename, module_data, name, revision, module_format,
            expect_failure_error=False
        )
    return module

def get_filtered_modules(context, filter_pattern):
    """Filter the Modules based on regex pattern."""
    re_filter = re.compile(filter_pattern)
    filtered_modules = {}
    for module_name, revs in context.revs.items():
        logging.debug(module_name)
        if not re_filter.search(module_name):
            continue
        filtered_modules[module_name] = revs
    return filtered_modules

def mk_path_list(stmt):
    """Derives a list of tuples containing
    (module name, prefix, xpath)
    per node in the statement.
    """
    resolved_names = []
    def resolve_stmt(stmt, resolved_names):
        if stmt.keyword in ['choice', 'case']:
            resolve_stmt(stmt.parent, resolved_names)
            return
        def qualified_name_elements(stmt):
            """(module name, prefix, name)"""
            return (stmt.i_module.arg, stmt.i_module.i_prefix, stmt.arg)
        if stmt.parent.keyword in ['module', 'submodule']:
            resolved_names.append(qualified_name_elements(stmt))
            return
        else:
            resolve_stmt(stmt.parent, resolved_names)
            resolved_names.append(qualified_name_elements(stmt))
            return
    resolve_stmt(stmt, resolved_names)
    return resolved_names

def mk_path_str(stmt, with_prefixes=False, prefix_onchange=False, prefix_to_module=False, resolve_top_prefix_to_module=False):
    """Returns the XPath path of the node.
    with_prefixes indicates whether or not to prefix every node.
    prefix_onchange modifies the behavior of with_prefixes and only adds prefixes when the prefix changes mid-XPath.
    prefix_to_module replaces prefixes with the module name of the prefix.
    resolve_top_prefix_to_module resolves the module-level prefix to the module name.
    Prefixes may be included in the path if the prefix changes mid-path.
    """
    resolved_names = mk_path_list(stmt)
    xpath_elements = []
    last_prefix = None
    for index, resolved_name in enumerate(resolved_names):
        module_name, prefix, node_name = resolved_name
        xpath_element = node_name
        if with_prefixes or (prefix_onchange and prefix != last_prefix):
            new_prefix = prefix
            if prefix_to_module or (index == 0 and resolve_top_prefix_to_module):
                new_prefix = module_name
            xpath_element = '%s:%s' % (new_prefix, node_name)
        xpath_elements.append(xpath_element)
        last_prefix = prefix
    return '/%s' % '/'.join(xpath_elements)

def get_xpath(stmt, qualified=False, prefix_to_module=False):
    """Gets the XPath of the statement.
    Unless qualified=True, does not include prefixes unless the prefix changes mid-XPath.
    qualified will add a prefix to each node.
    prefix_to_module will resolve prefixes to module names instead.
    For RFC 8040, set prefix_to_module=True.
    /prefix:root/node/prefix:node/...
    qualified=True: /prefix:root/prefix:node/prefix:node/...
    qualified=True, prefix_to_module=True: /module:root/module:node/module:node/...
    prefix_to_module=True: /module:root/node/module:node/...
    """
    return mk_path_str(stmt, with_prefixes=qualified, prefix_onchange=True, prefix_to_module=prefix_to_module)

def old_get_xpath(stmt, with_prefixes=False):
    """Returns the XPath path of the node"""
    if stmt.keyword in ['choice', 'case']:
        return mk_path_str(stmt.parent, with_prefixes)
    def name(stmt):
        if with_prefixes:
            return '%s:%s' % (stmt.i_module.i_prefix, stmt.arg)
        else:
            return stmt.arg
    if stmt.parent.keyword in ['module', 'submodule']:
        return '/%s' % name(stmt)
    else:
        xpath = mk_path_str(stmt.parent, with_prefixes)
        return '%s/%s' % (xpath, name(stmt))

def get_type(stmt):
    """Gets the immediate, top-level type of the node.
    TODO: Add get_prefixed_type method to get prefixed types.
    """
    type_obj = stmt.search_one('type')
    # Return type value if exists
    return getattr(type_obj, 'arg', None)

def get_qualified_type(stmt):
    """Gets the qualified, top-level type of the node.
    This enters the typedef if defined instead of using the prefix
    to ensure absolute distinction.
    """
    type_obj = stmt.search_one('type')
    fq_type_name = None
    if type_obj:
        if getattr(type_obj, 'i_typedef', None):
            # If type_obj has typedef, substitute.
            # Absolute module:type instead of prefix:type
            type_obj = type_obj.i_typedef
        type_name = type_obj.arg
        if check_primitive_type(type_obj):
            # Doesn't make sense to qualify a primitive..I think.
            fq_type_name = type_name
        else:
            type_module = type_obj.i_orig_module.arg
            fq_type_name = '%s:%s' % (type_module, type_name)
    return fq_type_name

def get_primitive_type(stmt):
    """Recurses through the typedefs and returns
    the most primitive YANG type defined.
    """
    type_obj = stmt.search_one('type')
    type_name = getattr(type_obj, 'arg', None)
    typedef_obj = getattr(type_obj, 'i_typedef', None)
    if typedef_obj:
        type_name = get_primitive_type(typedef_obj)
    elif type_obj and not check_primitive_type(type_obj):
        raise Exception('%s is not a primitive! Incomplete parse tree?' % type_name)
    return type_name

def check_primitive_type(stmt):
    """i_type_spec appears to indicate primitive type.
    """
    return True if getattr(stmt, 'i_type_spec', None) else False

def get_description(stmt):
    """Retrieves the description of the statement if present.
    """
    description_obj = stmt.search_one('description')
    # Return description value if exists
    return getattr(description_obj, 'arg', None)
