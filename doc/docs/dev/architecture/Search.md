# Search
Search in TDM is based off of ElasticSearch. Initial Search using ArangoDB was effective, but extremely latent and resource intensive. Some broad terms resulted in ~60GB memory usage and took nearly a minute to return. In contrast, ElasticSearch returns in fractions of a second and holds at a steady ~1-2GB memory usage.

ElasticSearch is *not* a source-of-truth for TDM. ElasticSearch should always be thought of as a cache of data which could potentially be out-of-sync with the ArangoDB instance of TDM which all other operations use. ElasticSearch is very-specifically a pointed, use-case solution to the original searchability issues.

## Indexing
Setup the index in ES for our data. Derived from:
* [Example Python](https://github.com/elastic/elasticsearch-py/blob/master/example/load.py#L17)
* [Analysis Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis.html)
* [Custom Analyzer](https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-custom-analyzer.html)
* [Simple Pattern Split Tokenizer](https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-simplepatternsplit-tokenizer.html)
* [Snowball Token Filter](https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-snowball-tokenfilter.html)
* [Unique Token Filter](https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-unique-tokenfilter.html)

This index specifies a custom analyzer and provides the `machine_id` and `human_id` of the DataPaths as fulltext search and as terms for aggregation.

```json
{
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "generic_path_analyzer": {
                    "type": "custom",
                    "tokenizer": "generic_path_tokenizer",
                    "filter": [
                        "preserve_word_delimiter",
                        "lowercase",
                        "network_synonym"
                    ]
                }
            },
            "tokenizer": {
                "generic_path_tokenizer": {
                    "type": "simple_pattern_split",
                    "tokenizer": "[\\.\\-\\/\\:]"
                }
            },
            "filter": {
                "preserve_word_delimiter": {
                    "type": "word_delimiter",
                    "preserve_original": true
                },
                "network_synonym": {
                    "type": "synonym",
                    "expand": true,
                    "synonyms": [
                        "optic, transceiver",
                        "intf, interface, if, int",
                        "ucast, unicast",
                        "mcast, multicast",
                        "pkt, packet",
                        "in, inbound"
                    ]
                }
            }
        }
    },
    "mappings": {
        "doc": {
            "properties": {
                "dp_key": {
                    "type": "keyword"
                },
                "dp_machine_id": {
                    "type": "text",
                    "analyzer": "generic_path_analyzer",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },
                "dp_human_id": {
                    "type": "text",
                    "analyzer": "generic_path_analyzer",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },
                "dp_description": {
                    "type": "text",
                    "analyzer": "snowball"
                },
                "dp_is_leaf": {
                    "type": "boolean"
                },
                "dp_is_configurable": {
                    "type": "boolean"
                },
                "dml_key": {
                    "type": "keyword"
                },
                "dml_name": {
                    "type": "keyword"
                },
                "dm_key": {
                    "type": "keyword"
                },
                "dm_name": {
                    "type": "keyword"
                },
                "dm_revision": {
                    "type": "keyword"
                },
                "release_key": {
                    "type": "keyword"
                },
                "release_name": {
                    "type": "keyword"
                },
                "os_key": {
                    "type": "keyword"
                },
                "os_name": {
                    "type": "keyword"
                }
            }
        }
    }
}
```

Loading of the data takes every permutation of a DataPath and its OS/Releases and creates a new document per permutation. This is not necessarily the *best* way to go about loading the data, but it was the clearest path forward. This does mean that there is a significant duplication albeit unique/qualified in document.

## Query
The ElasticSearch query in its current form performs an aggregation on the DataPath `human_id`. The results are ordered according to relevancy per the scoring of the query. An example query form is presented below.

```json
{
    "size": 0,
    "sort": [
        "_score"
    ],
    "query": {
        "bool": {
            "must": [
                {
                    "multi_match": {
                        "query": "openconfig interface name",
                        "operator": "and",
                        "type": "most_fields",
                        "fields": [
                            "dp_human_id^3",
                            "dp_machine_id",
                            "dp_description"
                        ]
                    }
                }
            ],
            "filter": []
        }
    },
    "aggs": {
        "human_id": {
            "terms": {
                "field": "dp_human_id.keyword",
                "size": 150,
                "order": {
                    "relevance": "desc"
                }
            },
            "aggs": {
                "relevance": {
                    "max": {
                        "script": "_score"
                    }
                },
                "dp_key": {
                    "terms": {
                        "field": "dp_key"
                    },
                    "aggs": {
                        "machine_id": {
                            "terms": {
                                "field": "dp_machine_id.keyword"
                            }
                        }
                    }
                }
            }
        }
    }
}
```

### ArangoDB Query
ArangoDB has some fulltext capabilities that we initially utilized. The query template is below. This query is wildly inefficient, but was the only one to provide a consistent upper-bound time window of return that was acceptable for usage.

```
LET given_os_releases = @filter_os_releases
LET given_dmls = @filter_dmls
LET filter_str = CONCAT_SEPARATOR(",", UNIQUE(SPLIT(SUBSTITUTE(@filter_str, [" ", "-", "/", ":"], ","), ",")))

LET dml_ids = FLATTEN(
    FOR dml IN DataModelLanguage
        FILTER dml.name IN given_dmls
        RETURN dml._id
)

LET dml_dm_ids = FLATTEN(
    FOR dml_dm IN OfDataModelLanguage
        FILTER dml_dm._from IN dml_ids
        RETURN dml_dm._to
)

LET dml_dm_dp_ids = FLATTEN(
    FOR dm_dp IN DataPathFromDataModel
        FILTER dm_dp._from IN dml_dm_ids
        RETURN dm_dp._to
)

LET filtered_dml_dm_dp_human_ids = FLATTEN(
    FOR dp IN FULLTEXT(DataPath, "human_id", filter_str)
        FILTER dp._id IN dml_dm_dp_ids
        RETURN dp._id
)

LET filtered_dml_dm_dp_machine_ids = FLATTEN(
    FOR dp IN FULLTEXT(DataPath, "machine_id", filter_str)
        FILTER dp._id IN dml_dm_dp_ids
        RETURN dp._id
)

LET filtered_dml_dm_dp_ids = UNION_DISTINCT(filtered_dml_dm_dp_human_ids, filtered_dml_dm_dp_machine_ids)

LET filtered_dml_dp_dm_ids = FLATTEN(
    FOR dm_dp IN DataPathFromDataModel
        FILTER dm_dp._to IN filtered_dml_dm_dp_ids
        RETURN dm_dp._from
)

RETURN MERGE(
    FOR os IN OS
        FILTER os.name IN ATTRIBUTES(given_os_releases)
        SORT os.name
        RETURN {
            [ os.name ]: MERGE(
                LET os_releases = FLATTEN(
                    FOR os_release IN OSHasRelease
                        FILTER os_release._from == os._id
                        RETURN os_release._to
                )
                FOR release IN Release
                    FILTER release._id IN os_releases
                    FILTER release.name IN TRANSLATE(os.name, given_os_releases)
                    SORT release.name
                    RETURN {
                        [ release.name ]: MERGE(
                            LET filtered_release_dms = FLATTEN(
                                FOR release_dm IN ReleaseHasDataModel
                                    FILTER release_dm._from == release._id
                                    FILTER release_dm._to IN filtered_dml_dp_dm_ids
                                    RETURN release_dm._to
                            )
                            FOR dml IN DataModelLanguage
                                FILTER dml._id IN dml_ids
                                RETURN {
                                    [ dml.name ]: MERGE(
                                        LET filtered_release_dml_dms = FLATTEN(
                                            FOR dml_dm IN OfDataModelLanguage
                                                FILTER dml_dm._from == dml._id
                                                FILTER dml_dm._to IN filtered_release_dms
                                                RETURN dml_dm._to
                                        )
                                        FOR dm IN DataModel
                                            FILTER dm._id IN filtered_release_dml_dms
                                            RETURN {
                                                [ dm.name ]: FLATTEN(
                                                    LET filtered_release_dml_dm_dps = FLATTEN(
                                                        FOR dm_dp IN DataPathFromDataModel
                                                            FILTER dm_dp._from IN filtered_release_dml_dms
                                                            FILTER dm_dp._from == dm._id
                                                            RETURN dm_dp._to
                                                    )
                                                    FOR dp IN DataPath
                                                        FILTER dp._id IN filtered_release_dml_dm_dps
                                                        FILTER dp._id IN filtered_dml_dm_dp_ids
                                                        FILTER dp.is_configurable == False
                                                        FILTER dp.is_leaf == True
                                                        SORT dp.human_id
                                                        LIMIT @start_index, @max_return_count
                                                        RETURN {
                                                            "_key": dp._key,
                                                            "human_id": dp.human_id
                                                        }
                                                )
                                            }
                                    )
                                }
                        )
                    }
            )
        }
)
```
