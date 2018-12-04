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
"""All of the Pythonic Data Model representations.
These Python objects reflect what will be in the database.
This class also provides that schema creation functionality.
"""
from pyArango.collection import *
from pyArango.graph import *

class DataPath(Collection):
    """The most basic representation of a "path" to a
    "data point" which can be transformed and utilized
    by control protocols to retrieve the data point.
    """

    _validation = {
        'on_save': False,
        'on_set': False,
        'allow_foreign_fields': True
    }

    _fields = {
        'machine_id': Field(),
        'human_id': Field(),
        'description': Field(),
        'is_leaf': Field(),
        'is_variable': Field(),
        'is_configurable': Field(),
        'verified': Field()
    }

class DataModel(Collection):
    """The data model which provides the definition
    of available data points which we may derive
    DataPaths from.
    """

    _validation = {
        'on_save': False,
        'on_set': False,
        'allow_foreign_fields': True
    }

    _fields = {
        'content': Field(),
        'name': Field(),
        'parsed_checksum': Field(),
        'revision': Field()
    }

class DataModelLanguage(Collection):
    """The known and defined language of data modeling
    which a DataModel is written in.
    """

    _validation = {
        'on_save': False,
        'on_set': False,
        'allow_foreign_fields': True
    }

    _fields = {
        'name': Field(),
        'description': Field()
    }

class OS(Collection):
    """The operating system which DataModels
    may apply to.
    """

    _validation = {
        'on_save': False,
        'on_set': False,
        'allow_foreign_fields': True
    }

    _fields = {
        'name': Field(),
        'description': Field()
    }

class Release(Collection):
    """The OS Release which DataModels
    may apply to.
    """

    _validation = {
        'on_save': False,
        'on_set': False,
        'allow_foreign_fields': True
    }

    _fields = {
        'name': Field(),
        'description': Field()
    }

class ControlProtocol(Collection):
    """The known and defined protocol which
    is capable of transforming or utilizing
    DataModels or DataPaths to retrieve
    the data points.
    """

    _validation = {
        'on_save': False,
        'on_set': False,
        'allow_foreign_fields': True
    }

    _fields = {
        'name': Field(),
        'description': Field()
    }

class TransportProtocol(Collection):
    """The known and defined protocol which a
    ControlProtocol may operate over.
    """

    _validation = {
        'on_save': False,
        'on_set': False,
        'allow_foreign_fields': True
    }

    _fields = {
        'name': Field(),
        'description': Field()
    }

class Encoding(Collection):
    """The encoding of the data which a DataPath
    is communicated via a ControlProtocol and over
    the TransportProtocol.
    """

    _validation = {
        'on_save': False,
        'on_set': False,
        'allow_foreign_fields': True
    }

    _fields = {
        'name': Field(),
        'description': Field()
    }

class DataType(Collection):
    """The defined data type that a data point in
    a DataPath is defined to equate to.
    """

    _validation = {
        'on_save': False,
        'on_set': False,
        'allow_foreign_fields': True
    }

    _fields = {
        'name': Field(),
        'description': Field(),
        'is_primitive': Field()
    }

class Device(Collection):
    """A physical device which may have data models
    and should have corresponding data paths.
    """

    _validation = {
        'on_save': False,
        'on_set': False,
        'allow_foreign_fields': True
    }

    _fields = {
        'name': Field(),
        'description': Field()
    }

class Calculation(Collection):
    """A defined calculation which may be used to indicate
    that a DataPath is calculated via other DataPaths. This does
    not attempt to maintain order of operations. Order of operations
    must be maintained in the equation/description and will not
    automatically apply.
    """

    _validation = {
        'on_save': False,
        'on_set': False,
        'allow_foreign_fields': True
    }

    _fields = {
        'name': Field(),
        'description': Field(),
        'equation': Field(),
        'author': Field()
    }

class DeviceHasDataPath(Edges):
    """Indicates that it has been validated that a Device does
    have a specified DataPath available.
    """

    _fields = {
        'os': Field(),
        'release': Field()
    }

class DeviceHasDataModel(Edges):
    """Indicates that it has been validated that a Device does
    have a specified DataModel.
    """

    _fields = {
        'os': Field(),
        'release': Field()
    }

class OSHasRelease(Edges):
    """OS ownership of a specific Release name."""

    _fields = {}

class ReleaseHasDataModel(Edges):
    """Indication that, theoretically, a specific Release
    should have a DataModel.
    """

    _fields = {}

class ReleaseRevision(Edges):
    """Indicates that a Release is a revision of another
    Release."""

    _fields = {}

class DataPathFromDataModel(Edges):
    """Indicates that a specific DataPath is derivative of
    a certain DataModel.
    """

    _fields = {
        'parse_timestamp': Field()
    }

class OfDataModelLanguage(Edges):
    """Indicates that a DataModel is written in the linked
    DataModelLanguage.
    """

    _fields = {}

class HasControlProtocol(Edges):
    """Indicates that a DataModelLanguage may be manipulated
    by the linked ControlProtocol.
    """

    _fields = {}

class HasEncoding(Edges):
    """Indicates that a ControlProtocol supports the linked
    Encoding.
    """

    _fields = {}

class HasTransportProtocol(Edges):
    """Indicates that a ControlProtocol supports the linked
    TransportProtocol.
    """

    _fields = {}

class DataPathMatch(Edges):
    """Indicates that the linked DataPaths are equivalent.
    timestamp: time of insertion
    author: submitter of match
    validated: whether match is trustworthy
    weight: -1..+inf. -1 indicates incongruent.
    annotation: human consumable annotation on match.
    needs_human: indicates incompatible for machine consumption.
    """

    _fields = {
        'timestamp': Field(),
        'author': Field(),
        'validated': Field(),
        'weight': Field(),
        'annotation': Field(),
        'needs_human': Field()
    }

class DataPathParent(Edges):
    """Indicates that a DataPath is a parent of another DataPath.
    e.g. 1 <- 2
    """

    _fields = {}

class DataPathChild(Edges):
    """Indicates that a DataPath is a child of another DataPath.
    e.g. 1 -> 2
    """

    _fields = {}

class OfDataType(Edges):
    """Indicates that a DataPath is of data type DataType."""

    _fields = {
        'parse_timestamp': Field()
    }

class DataModelChild(Edges):
    """Demonstrates revision child relationships in DataModels."""

    _fields = {}

class DataModelParent(Edges):
    """Demonstrates revision parent relationships in DataModels."""

    _fields = {}

class DataModelDerivedFrom(Edges):
    """Indicates that this DataModel is not a standalone DataModel and
    is actually converted or generated from the existing, linked DataModel.
    """

    _fields = {}

class InCalculation(Edges):
    """Indicates that a DataPath is within the specified Calculation."""

    _fields = {}

class CalculationResult(Edges):
    """Indicates that a DataPath is a result of the specified Calculation."""

    _fields = {}

class DataModelLanguageHasDataType(Edges):
    """Indicates that a DataType is defined within a DataModelLanguage."""

    _fields = {}

def create_collections(db):
    """Creates all the Collections of elements."""
    collection_classes = {
        'DataPath': DataPath,
        'DataModel': DataModel,
        'DataModelLanguage': DataModelLanguage,
        'OS': OS,
        'Release': Release,
        'ControlProtocol': ControlProtocol,
        'TransportProtocol': TransportProtocol,
        'Encoding': Encoding,
        'DataType': DataType,
        'Device': Device,
        'Calculation': Calculation
    }
    for collection_name in collection_classes.keys():
        db.createCollection(collection_name)

def create_edges(db):
    """Creates all the Edge Collections which demonstrate
    relationships between elements of Collections.
    """
    edge_classes = {
        'DeviceHasDataPath': DeviceHasDataPath,
        'DeviceHasDataModel': DeviceHasDataModel,
        'OSHasRelease': OSHasRelease,
        'ReleaseRevision': ReleaseRevision,
        'ReleaseHasDataModel': ReleaseHasDataModel,
        'DataPathFromDataModel': DataPathFromDataModel,
        'OfDataModelLanguage': OfDataModelLanguage,
        'HasControlProtocol': HasControlProtocol,
        'HasEncoding': HasEncoding,
        'HasTransportProtocol': HasTransportProtocol,
        'DataPathMatch': DataPathMatch,
        'DataPathParent': DataPathParent,
        'DataPathChild': DataPathChild,
        'OfDataType': OfDataType,
        'DataModelParent': DataModelParent,
        'DataModelChild': DataModelChild,
        'DataModelDerivedFrom': DataModelDerivedFrom,
        'InCalculation': InCalculation,
        'CalculationResult': CalculationResult,
        'DataModelLanguageHasDataType': DataModelLanguageHasDataType
    }
    for edge_name in edge_classes.keys():
        db.createCollection(edge_name)

def create_indexes(db):
    """Create the indexes which provide uniqueness,
    searchability, etc. on certain properties of elements.
    """
    db['DataPath'].ensureSkiplistIndex(
        fields=['machine_id'],
        unique=True,
        sparse=False
    )
    db['DataPath'].ensureFulltextIndex(
        fields=['machine_id']
    )
    db['DataPath'].ensureFulltextIndex(
        fields=['human_id']
    )
    db['DataPath'].ensureFulltextIndex(
        fields=['description']
    )

def create_schema(db):
    """Create the schema!"""
    create_collections(db)
    create_edges(db)
    create_indexes(db)
