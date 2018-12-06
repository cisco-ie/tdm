"""Load a search database with TDM data for fast/efficient searches
from search web interface. Uses ElasticSearch.
"""
import logging
from elasticsearch import Elasticsearch
from elasticsearch.helpers import streaming_bulk
from elasticsearch.exceptions import TransportError


def populate_search(db, search_host='search:9200', index='datapath', doc_type='doc'):
    logging.getLogger('elasticsearch').setLevel(logging.WARN)
    logging.info('Acquiring DataPaths from TDM...')
    query_iterable = query_all_datapaths(db)
    logging.info('Setting up ES...')
    es = Elasticsearch(search_host)
    setup_search_db(es, index)
    logging.info('Populating ES with DataPaths...')
    populate_search_db(es, query_iterable, index, doc_type)

def query_all_datapaths(db):
    """Queries TDM and flattens the DataPath structure for our search purposes.
    2 stage query due to not all DataPaths being linked to OS/Releases (OIDs).
    """
    query = """
    RETURN FLATTEN(
        FOR dp IN DataPath
            FOR v, e, p IN 2..2 INBOUND dp DataPathFromDataModel, OfDataModelLanguage
                LET dp_min = {
                    "dp_key": p.vertices[0]._key,
                    "dp_machine_id": p.vertices[0].machine_id,
                    "dp_human_id": p.vertices[0].human_id,
                    "dp_description": p.vertices[0].description,
                    "dp_is_leaf": p.vertices[0].is_leaf,
                    "dp_is_configurable": p.vertices[0].is_configurable,
                    "dml_key": p.vertices[2]._key,
                    "dml_name": p.vertices[2].name
                }
                LET dp_ext = (
                    FOR _v, _e, _p IN 2..2 INBOUND p.vertices[1] ReleaseHasDataModel, OSHasRelease
                        RETURN {
                            "dm_key": _p.vertices[0]._key,
                            "dm_name": _p.vertices[0].name,
                            "dm_revision": _p.vertices[0].revision,
                            "release_key": _p.vertices[1]._key,
                            "release_name": _p.vertices[1].name,
                            "os_key": _p.vertices[2]._key,
                            "os_name": _p.vertices[2].name
                        }
                )
                RETURN LENGTH(dp_ext) != 0 ? (FOR ext IN dp_ext RETURN MERGE(dp_min, ext)) : dp_min
    )
    """
    return db.AQLQuery(query, rawResults=True, batchSize=1000)

def setup_search_db(es, index):
    """Setup the index in ES for our data. Derived from:
    https://github.com/elastic/elasticsearch-py/blob/master/example/load.py#L17
    https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis.html
    https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-custom-analyzer.html
    https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-simplepatternsplit-tokenizer.html
    https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-snowball-tokenfilter.html
    https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-unique-tokenfilter.html
    Applies a custom analyzer and provides the machine_id and human_id of the DataPaths as
    fulltext search and as terms for aggregation.
    """
    # Specifies both text and keyword for both fulltext and agg capability
    path_mapping = {
        'type': 'text',
        'analyzer': 'generic_path_analyzer',
        'fields': {
            'keyword': {
                'type': 'keyword'
            }
        }
    }
    index_payload = {
        'settings': {
            'number_of_shards': 1,
            'number_of_replicas': 0,
            'analysis': {
                'analyzer': {
                    'generic_path_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'generic_path_tokenizer',
                        'filter': [
                            'preserve_word_delimiter',
                            'lowercase',
                            'network_synonym'
                        ]
                    }
                },
                'tokenizer': {
                    'generic_path_tokenizer': {
                        'type': 'simple_pattern_split',
                        'tokenizer': '[\.\-\/\:]'
                    }
                },
                'filter': {
                    'preserve_word_delimiter': {
                        'type': 'word_delimiter',
                        'preserve_original': True
                    },
                    'network_synonym': {
                        'type': 'synonym',
                        'expand': True,
                        'synonyms': [
                            'optic, transceiver',
                            'intf, interface, if, int',
                            'ucast, unicast',
                            'mcast, multicast',
                            'pkt, packet',
                            'in, inbound'
                        ]
                    }
                }
            }
        },
        'mappings': {
            'doc': {
                'properties': {
                    'dp_key': {'type': 'keyword'},
                    'dp_machine_id': path_mapping,
                    'dp_human_id': path_mapping,
                    'dp_description': {'type': 'text', 'analyzer': 'snowball'},
                    'dp_is_leaf': {'type': 'boolean'},
                    'dp_is_configurable': {'type': 'boolean'},
                    'dml_key': {'type': 'keyword'},
                    'dml_name': {'type': 'keyword'},
                    'dm_key': {'type': 'keyword'},
                    'dm_name': {'type': 'keyword'},
                    'dm_revision': {'type': 'keyword'},
                    'release_key': {'type': 'keyword'},
                    'release_name': {'type': 'keyword'},
                    'os_key': {'type': 'keyword'},
                    'os_name': {'type': 'keyword'}
                }
            }
        }
    }
    try:
        es.indices.create(
            index=index,
            body=index_payload,
        )
    except TransportError as e:
        if e.error == 'index_already_exists_exception':
            logging.info('Index already exists in ES!')
        else:
            logging.exception('Error when creating index in ES!')

def populate_search_db(es, query_iterable, index, doc_type):
    """Populate ElasticSearch with the flattened DataPaths.
    Derived from https://github.com/elastic/elasticsearch-py/blob/master/example/load.py#L102
    """
    def iter_add_id(iterable):
        """We need to add a uid before insertion (I think).
        Every example seen has an _id property in the struct.
        """
        counter = 0
        for result in iterable:
            if not isinstance(result, (list,)):
                logging.error('Expected result to be list in iterable!')
            for element in result:
                element['_id'] = counter
                counter += 1
                yield element
    for ok, result in streaming_bulk(
            es,
            iter_add_id(query_iterable),
            index=index,
            doc_type=doc_type
        ):
        action, result = result.popitem()
        doc_id = '/%s/%s/%s' % (index, doc_type, result['_id'])
        if not ok:
            logging.error('Failed to %s document %s: %r' % (action, doc_id, result))
