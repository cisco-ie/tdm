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
"""Populate static business data that is otherwise conceptual 
and not able to be directly parsed from data itself.
"""

def populate_data_model_languages(db):
    """Populate everything related to individual Data Model Languages.
    Transport Protocols, Encodings, Control Protocols, Data Types, and DMLs.
    Creates vertices and relationship edges.
    """
    # Define Transport Protocols
    transport_protocols = {
        'TCP': db['TransportProtocol'].createDocument({
            '_key': 'TCP',
            'name': 'TCP',
            'description': 'Transmission Control Protocol'
        }),
        'UDP': db['TransportProtocol'].createDocument({
            '_key': 'UDP',
            'name': 'UDP',
            'description': 'User Datagram Protocol'
        }),
        'SSH': db['TransportProtocol'].createDocument({
            '_key': 'SSH',
            'name': 'SSH',
            'description': 'Secure SHell'
        }),
        'Telnet': db['TransportProtocol'].createDocument({
            '_key': 'Telnet',
            'name': 'Telnet',
            'description': 'Insecure but oh so handy'
        }),
        'HTTP': db['TransportProtocol'].createDocument({
            '_key': 'HTTP',
            'name': 'HTTP',
            'description': 'HyperText Transfer Protocol'
        })
    }
    for doc in transport_protocols.values():
        doc.save()
    # Define Encodings
    encodings = {
        'JSON': db['Encoding'].createDocument({
            '_key': 'JSON',
            'name': 'JSON',
            'description': 'JavaScript Object Notation'
        }),
        'XML': db['Encoding'].createDocument({
            '_key': 'XML',
            'name': 'XML',
            'description': 'eXtensible Markup Language'
        }),
        'GPB': db['Encoding'].createDocument({
            '_key': 'GPB',
            'name': 'GPB',
            'description': 'Google Protocol Buffer'
        }),
        'KV-GPB': db['Encoding'].createDocument({
            '_key': 'KV-GPB',
            'name': 'KV-GPB',
            'description': 'Key/Value Google Protocol Buffer'
        }),
        'BER': db['Encoding'].createDocument({
            '_key': 'BER',
            'name': 'BER',
            'description': 'Basic Encoding Rules, defined in X.209. Used in SNMP.'
        }),
        'Text': db['Encoding'].createDocument({
            '_key': 'Text',
            'name': 'Text',
            'description': 'Text'
        })
    }
    for doc in encodings.values():
        doc.save()
    # Define Control Protocols
    control_protocols = {
        'gRPC': db['ControlProtocol'].createDocument({
            '_key': 'gRPC',
            'name': 'gRPC',
            'description': 'gRPC Remote Procedure Call'
        }),
        'NETCONF': db['ControlProtocol'].createDocument({
            '_key': 'NETCONF',
            'name': 'NETCONF',
            'description': 'Network Configuration Protocol'
        }),
        'SNMP': db['ControlProtocol'].createDocument({
            '_key': 'SNMP',
            'name': 'SNMP',
            'description': 'Simple Network Management Protocol'
        }),
        'MDT': db['ControlProtocol'].createDocument({
            '_key': 'MDT',
            'name': 'MDT',
            'description': 'Model-Driven Telemetry'
        }),
        'CLI': db['ControlProtocol'].createDocument({
            '_key': 'CLI',
            'name': 'CLI',
            'description': 'Command Line Interface'
        }),
        'RESTCONF': db['ControlProtocol'].createDocument({
            '_key': 'RESTCONF',
            'name': 'RESTCONF',
            'description': 'NETCONF -> REST'
        }),
        'NX-API': db['ControlProtocol'].createDocument({
            '_key': 'NX-API',
            'name': 'NX-API',
            'description': 'NX-API'
        })
    }
    for doc in control_protocols.values():
        doc.save()
    # Control Protocols -> Encodings
    cp_has_encodings = {
        'gRPC': ['GPB', 'KV-GPB'],
        'NETCONF': ['XML'],
        'SNMP': ['BER'],
        'MDT': ['GPB', 'KV-GPB', 'JSON'],
        'CLI': ['Text'],
        'RESTCONF': ['XML', 'JSON'],
        'NX-API': ['XML', 'JSON']
    }
    for key, values in cp_has_encodings.items():
        for cp_key in values:
            db['HasEncoding'].createEdge().links(
                control_protocols[key],
                encodings[cp_key]
            )
    # Control Protocols -> Transport Protocols
    cp_has_tps = {
        'gRPC': ['HTTP'],
        'NETCONF': ['SSH'],
        'SNMP': ['UDP', 'TCP'],
        'MDT': ['UDP', 'TCP', 'HTTP'],
        'CLI': ['SSH', 'Telnet'],
        'RESTCONF': ['HTTP'],
        'NX-API': ['HTTP']
    }
    for key, values in cp_has_tps.items():
        for tp_key in values:
            db['HasTransportProtocol'].createEdge().links(
                control_protocols[key],
                transport_protocols[tp_key]
            )
    # Define Data Model Languages
    # Data Model Languages -> Data Types
    # Data Model Languages -> Control Protocols
    data_model_languages = {
        'YANG': {
            'description': 'Yet Another Next Generation',
            'data_types': { # Derived from https://tools.ietf.org/html/rfc6020
                'binary': ('https://tools.ietf.org/html/rfc6020#section-9.8', True),
                'bits': ('https://tools.ietf.org/html/rfc6020#section-9.7', True),
                'boolean': ('https://tools.ietf.org/html/rfc6020#section-9.5', True),
                'decimal64': ('https://tools.ietf.org/html/rfc6020#section-9.3', True),
                'empty': ('https://tools.ietf.org/html/rfc6020#section-9.11', True),
                'enumeration': ('https://tools.ietf.org/html/rfc6020#section-9.6', True),
                'identityref': ('https://tools.ietf.org/html/rfc6020#section-9.10', True),
                'instance-identifier': ('https://tools.ietf.org/html/rfc6020#section-9.13', True),
                'int8': ('https://tools.ietf.org/html/rfc6020#section-9.2', True),
                'int16': ('https://tools.ietf.org/html/rfc6020#section-9.2', True),
                'int32': ('https://tools.ietf.org/html/rfc6020#section-9.2', True),
                'int64': ('https://tools.ietf.org/html/rfc6020#section-9.2', True),
                'leafref': ('https://tools.ietf.org/html/rfc6020#section-9.9', True),
                'string': ('https://tools.ietf.org/html/rfc6020#section-9.4', True),
                'uint8': ('https://tools.ietf.org/html/rfc6020#section-9.2', True),
                'uint16': ('https://tools.ietf.org/html/rfc6020#section-9.2', True),
                'uint32': ('https://tools.ietf.org/html/rfc6020#section-9.2', True),
                'uint64': ('https://tools.ietf.org/html/rfc6020#section-9.2', True),
                'union': ('https://tools.ietf.org/html/rfc6020#section-9.12', True)
            },
            'control_protocols': ['gRPC', 'NETCONF', 'RESTCONF', 'MDT']
        },
        'SMI': {
            'description': 'Structure of Management Information',
            'data_types': { # Derived from https://tools.ietf.org/html/rfc2578
                'Integer32': ('https://tools.ietf.org/html/rfc2578#section-7.1.1', True),
                'INTEGER': ('https://tools.ietf.org/html/rfc2578#section-7.1.1', True),
                'OCTET STRING': ('https://tools.ietf.org/html/rfc2578#section-7.1.2', True),
                'OBJECT IDENTIFIER': ('https://tools.ietf.org/html/rfc2578#section-7.1.3', True),
                'BITS': ('https://tools.ietf.org/html/rfc2578#section-7.1.4', True),
                'IpAddress': ('https://tools.ietf.org/html/rfc2578#section-7.1.5', True),
                'Counter32': ('https://tools.ietf.org/html/rfc2578#section-7.1.6', True),
                'Gauge32': ('https://tools.ietf.org/html/rfc2578#section-7.1.7', True),
                'TimeTicks': ('https://tools.ietf.org/html/rfc2578#section-7.1.8', True),
                'Opaque': ('https://tools.ietf.org/html/rfc2578#section-7.1.9', True),
                'Counter64': ('https://tools.ietf.org/html/rfc2578#section-7.1.10', True),
                'Unsigned32': ('https://tools.ietf.org/html/rfc2578#section-7.1.11', True),
                'Conceptual Tables': ('https://tools.ietf.org/html/rfc2578#section-7.1.12', True)
            },
            'control_protocols': ['MDT']
        },
        'DME': {
            'description': 'Data Management Engine',
            'data_types': {},
            'control_protocols': ['MDT', 'NX-API']
        },
        'CLI': {
            'description': 'Command Line Interface',
            'data_types': {},
            'control_protocols': ['CLI']
        }
    }
    for key, value in data_model_languages.items():
        new_dml = db['DataModelLanguage'].createDocument({
            '_key': arangify_key(key),
            'name': key,
            'description': value['description']
        })
        new_dml.save()
        for dt_key, dt_value in value['data_types'].items():
            new_dt = db['DataType'].createDocument({
                '_key': arangify_key('%s+%s' % (key, dt_key)),
                'name': dt_key,
                'description': dt_value[0],
                'is_primitive': dt_value[1]
            })
            new_dt.save()
            db['DataModelLanguageHasDataType'].createEdge().links(new_dml, new_dt)
        for cp_key in value['control_protocols']:
            db['HasControlProtocol'].createEdge().links(new_dml, control_protocols[cp_key])

def populate_os_releases(db):
    """Populate OSes and releases.
    Derived from YANG repository directories for now.
    https://github.com/YangModels/yang/tree/master/vendor/cisco
    """
    oses = {
        'IOS XE': {
            'description': 'IOS XE',
            'releases': [
                '16.3.1',
                '16.3.2',
                '16.4.1',
                '16.5.1',
                '16.6.1',
                '16.6.2',
                '16.7.1',
                '16.8.1',
                '16.9.1',
                '16.9.3'
            ]
        },
        'IOS XR': {
            'description': 'IOS XR',
            'releases': [
                '5.3.0',
                '5.3.1',
                '5.3.2',
                '5.3.3',
                '5.3.4',
                '6.0.0',
                '6.0.1',
                '6.0.2',
                '6.1.1',
                '6.1.2',
                '6.1.3',
                '6.2.1',
                '6.2.2',
                '6.3.1',
                '6.3.2',
                '6.4.1',
                '6.4.2',
                '6.5.1',
                '6.5.2',
                '6.5.3',
                '6.6.2',
                '7.0.1'
            ]
        },
        'NX-OS': {
            'description': 'NX-OS',
            'releases': [
                '7.0(3)F1(1)',
                '7.0(3)F2(1)',
                '7.0(3)F2(2)',
                '7.0(3)I5(1)',
                '7.0(3)I5(2)',
                '7.0(3)I6(1)',
                '7.0(3)I6(2)',
                '7.0(3)I7(1)',
                '7.0(3)I7(2)',
                '7.0(3)I7(3)',
                '7.0(3)I7(4)',
                '9.2(1)',
                '9.2(2)',
                '9.2(3)'
            ]
        }
    }
    for key, value in oses.items():
        new_os = db['OS'].createDocument({
            '_key': arangify_key(key),
            'name': key,
            'description': value['description']
        })
        new_os.save()
        previous_release = None
        for release in value['releases']:
            new_release = db['Release'].createDocument({
                '_key': arangify_key('%s+%s' % (key, release)),
                'name': release
            })
            new_release.save()
            db['OSHasRelease'].createEdge().links(new_os, new_release)
            if previous_release is not None:
                db['ReleaseRevision'].createEdge().links(previous_release, new_release)
            previous_release = new_release

def arangify_key(key):
    return key.replace(' ', '_')

def populate_static(db):
    populate_os_releases(db)
    populate_data_model_languages(db)
