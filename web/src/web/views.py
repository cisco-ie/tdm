import json
import csv
import time
import io
from collections import OrderedDict
import flask
from itertools import chain
from arango import ArangoClient
from elasticsearch import Elasticsearch
from werkzeug.utils import secure_filename
from . import forms
from . import app

@app.route('/')
def index():
    return flask.render_template('index.html')

@app.route('/datapath/matches', methods=['GET'])
def datapath_matches():
    return flask.render_template(
        'matches.html',
        dml_matches=fetch_all_matches()
    )

def fetch_all_matches():
    all_matches_query = """
    RETURN MERGE(
    FOR dml IN DataModelLanguage
        RETURN {
        [ dml.name ]: (
            FOR v, e, p IN 3..3 OUTBOUND dml OfDataModelLanguage, DataPathFromDataModel, ANY DataPathMatch
            SORT p.vertices[2].human_id
            RETURN DISTINCT({
                '_key': p.vertices[2]._key,
                'human_id': p.vertices[2].human_id
            })
        )
        }
    )
    """
    return query_db(all_matches_query)

@app.route('/matchmaker')
def matchmaker():
    match_form = forms.MatchForm()
    return flask.render_template('matchmaker.html', match_form=match_form)

@app.route('/datapath/match/<int:_key>', methods=['POST'])
def datapath_match(_key):
    match_form = forms.DataPathMatchForm()
    if match_form.validate_on_submit():
        basepath_key = int(_key)
        matchpath_key = int(match_form.matchpath_key.data)
        author = match_form.author.data.strip()
        annotation = match_form.annotation.data.strip()
        weight = int(match_form.weight.data)
        try:
            map_datapath_single_by_key(basepath_key, matchpath_key, author, weight, annotation)
        except Exception as e:
            flask.flash(getattr(e, 'message', repr(e)))
    else:
        error_msg = ''
        for field, errors in match_form.errors.items():
            error_msg += '<strong>%s</strong><br>%s<br>' % (field, '<br>'.join(errors))
        flask.flash(error_msg)
    return flask.redirect(flask.url_for('datapath_details', _key=int(_key)))

@app.route('/datapath/view/<int:_key>')
def datapath_details(_key):
    match_form = forms.DataPathMatchForm()
    datapath_oses = set()
    for dp_graph in fetch_datapath_os_graph(_key):
        dp_os = dp_graph['os_name']
        if dp_os:
            if dp_graph['os_release']:
                dp_os = '%s - %s' % (dp_os, dp_graph['os_release'])
            datapath_oses.add(dp_os)
    datapath_dmls = set()
    datapath_models = {}
    for dp_graph in fetch_datapath_dml_graph(_key):
        dml_name = dp_graph['dml_name']
        if dml_name:
            datapath_dmls.add(dml_name)
        datamodel_name = dp_graph['datamodel_name']
        if datamodel_name:
            if datamodel_name not in datapath_models.keys():
                datapath_models[datamodel_name] = []
            datapath_models[datamodel_name].append({'revision': dp_graph['datamodel_revision'] or '', 'dml': dml_name})
    return flask.render_template('datapath.html',
        datapath=fetch_datapath(_key),
        datapath_models=datapath_models,
        datapath_oses=datapath_oses,
        datapath_dmls=datapath_dmls,
        datapath_parent=fetch_datapath_parent(_key),
        datapath_children=fetch_datapath_children(_key),
        datapath_datatypes=fetch_datapath_datatype(_key),
        datapath_mappings=fetch_datapath_mappings(_key),
        match_form=match_form
    )

def fetch_datapath_os_graph(_key):
    datapath_os_graph_query = """
    LET datapath = DOCUMENT(CONCAT('DataPath/', @key))
    FOR v, e, p IN 1..3 INBOUND datapath DataPathFromDataModel, ReleaseHasDataModel, OSHasRelease
    RETURN {
        "datamodel_name": p.vertices[1].name,
        "datamodel_revision": p.vertices[1].revision,
        "os_release": p.vertices[2].name,
        "os_name": p.vertices[3].name
    }
    """
    bind_vars = {'key': _key}
    return query_db(datapath_os_graph_query, bind_vars, unlist=False)

def fetch_datapath_dml_graph(_key):
    datapath_dml_graph_query = """
    LET datapath = DOCUMENT(CONCAT('DataPath/', @key))
    FOR v, e, p IN 2..2 INBOUND datapath DataPathFromDataModel, OfDataModelLanguage
    RETURN {
        "datamodel_name": p.vertices[1].name,
        "datamodel_revision": p.vertices[1].revision,
        "dml_name": p.vertices[2].name
    }
    """
    bind_vars = {'key': _key}
    return query_db(datapath_dml_graph_query, bind_vars, unlist=False)

def fetch_datapath_mappings(_key):
    datapath_mappings_query = """
        LET dp_id = CONCAT("DataPath/", @key)
        FOR dp_match IN DataPathMatch
            FILTER dp_match._from == dp_id || dp_match._to == dp_id
            LET dp = DOCUMENT(dp_match._from == dp_id ? dp_match._to : dp_match._from)
            RETURN {
                '_key': dp._key,
                'human_id': dp.human_id
            }
    """
    bind_vars = {'key': _key}
    return query_db(datapath_mappings_query, bind_vars, unlist=False)

@app.route('/datapath/direct', methods=['GET', 'POST'])
def datapath_direct():
    direct_form = forms.DirectForm()
    multi_paths = []
    if direct_form.validate_on_submit():
        datapath_id = direct_form.path_id.data.strip()
        direct_dps = fetch_datapath_arbitrary_id(datapath_id)
        if len(direct_dps) > 1:
            flask.flash('Multiple potential DataPaths!', 'warning')
            multi_paths = direct_dps
        elif not direct_dps:
            flask.flash('No matching DataPaths found!', 'warning')
        else:
            return flask.redirect(flask.url_for('datapath_details', _key=direct_dps[0]['_key']), code=303)
    return flask.render_template('datapath_direct.html', direct_form=direct_form, multi_paths=multi_paths)

def fetch_datapath_arbitrary_id(path):
    datapath_arbitrary_id_query = """
        FOR dp IN DataPath
            FILTER dp.human_id == @path || dp.machine_id == @path
            RETURN {
                '_key': dp._key,
                'machine_id': dp.machine_id
            }
    """
    bind_vars = {'path': path}
    return query_db(datapath_arbitrary_id_query, bind_vars, unlist=False)

def fetch_datapath_datatype(_key):
    datapath_datatype_query = """
        LET dp_id = CONCAT("DataPath/", @key)
        FOR dp_dt IN OfDataType
            FILTER dp_dt._from == dp_id
            LET dt_doc = DOCUMENT(dp_dt._to)
            RETURN {
                "_key": dt_doc._key,
                "name": dt_doc.name
            }
    """
    bind_vars = {'key': _key}
    return query_db(datapath_datatype_query, bind_vars, unlist=False)

def fetch_datapath_parent(_key):
    datapath_parent_query = """
        LET dp_id = CONCAT("DataPath/", @key)
        FOR dp_parent IN DataPathParent
            FILTER dp_parent._from == dp_id
            SORT dp_parent._to
            LET dp_parent_doc = DOCUMENT(dp_parent._to)
            RETURN {
                "_key": dp_parent_doc._key,
                "human_id": dp_parent_doc.human_id
            }
    """
    bind_vars = {'key': _key}
    return query_db(datapath_parent_query, bind_vars, unlist=False)

def fetch_datapath_children(_key):
    datapath_children_query = """
        LET dp_id = CONCAT("DataPath/", @key)
        FOR dp_child IN DataPathChild
            FILTER dp_child._from == dp_id
            SORT dp_child._to
            LET dp_child_doc = DOCUMENT(dp_child._to)
            RETURN {
                "_key": dp_child_doc._key,
                "human_id": dp_child_doc.human_id
            }
    """
    bind_vars = {'key': _key}
    return query_db(datapath_children_query, bind_vars, unlist=False)

def fetch_datapath_models(_key):
    datapath_model_query = """
        LET dp_id = CONCAT("DataPath/", @key)
        FOR model_child IN DataPathFromDataModel
            FILTER model_child._to == dp_id
            SORT model_child._from
            LET model_doc = DOCUMENT(model_child._from)
            RETURN {
                "name": model_doc.name,
                "revision": model_doc.revision
            }
    """
    bind_vars = {'key': _key}
    return query_db(datapath_model_query, bind_vars, unlist=False)

def fetch_datapath(_key):
    datapath_query = """RETURN DOCUMENT(CONCAT("DataPath/", @key))"""
    bind_vars = {'key': _key}
    return query_db(datapath_query, bind_vars)

def fetch_matches(given_dps):
    match_query = """
    LET given_dps = @given_dps
    FOR dp IN DataPath
        FILTER dp.human_id IN @given_dps || dp.machine_id IN @given_dps
        LET result = {
            "_key": dp._key,
            "human_id": dp.human_id,
            "machine_id": dp.machine_id,
            "matches": FLATTEN(
                FOR dp_eq IN DataPathMatch
                    FILTER dp_eq._from == dp._id || dp_eq._to == dp._id
                    LET tdm_dp = dp_eq._from == dp._id ? DOCUMENT(dp_eq._to) : DOCUMENT(dp_eq._from)
                    SORT tdm_dp.human_id
                    RETURN {
                        "_key": tdm_dp._key,
                        "human_id": tdm_dp.human_id,
                        "machine_id": tdm_dp.machine_id
                    }
            )
        }
        FILTER LENGTH(result.matches) != 0
        SORT result.human_id
        RETURN result
    """
    bind_vars = {'given_dps': given_dps}
    return query_db(match_query, bind_vars, unlist=False)

@app.route('/matches', methods=['POST'])
def matches():
    match_form = forms.MatchForm()
    if not match_form.validate_on_submit():
        return 'Invalid submission!'
    given_dps = [dp.strip('./,') for dp in match_form.paths.data.split()]
    if not given_dps:
        return 'Nothing specified to match!'
    matches = fetch_matches(given_dps)
    return flask.jsonify(matches)

def fetch_calculations(given_dps):
    calculations_query = """
    WITH DataPath, Calculation
    LET given_dps = @given_dps
    FOR dp IN DataPath
    FILTER dp.human_id IN given_dps || dp.machine_id IN given_dps
    LET result = {
        "_key": dp._key,
        "human_id": dp.human_id,
        "machine_id": dp.machine_id,
        "calculations": {
        "as_result": (
            FOR calc_result IN CalculationResult
            FILTER calc_result._to == dp._id
            LET calculation = DOCUMENT(calc_result._from)
            RETURN {
                "_key": calculation._key,
                "name": calculation.name,
                "result": {
                "_key": dp._key,
                "human_id": dp.human_id,
                "machine_id": dp.machine_id
                },
                "factors": (
                FOR calc_factor IN InCalculation
                    FILTER calc_factor._to == calculation._id
                    LET factor_dp = DOCUMENT(calc_factor._from)
                    RETURN {
                    "_key": factor_dp._key,
                    "human_id": factor_dp.human_id,
                    "machine_id": factor_dp.machine_id
                    }
                )
            }
        ),
        "as_factor": (
            FOR calc_factor IN InCalculation
            FILTER calc_factor._from == dp._id
            LET calculation = DOCUMENT(calc_factor._to)
            RETURN {
                "_key": calculation._key,
                "name": calculation.name,
                "result": FIRST(
                FOR result IN CalculationResult
                    FILTER calculation._id == result._from
                    LET result_dp = DOCUMENT(result._to)
                    RETURN {
                    "_key": result_dp._key,
                    "human_id": result_dp.human_id,
                    "machine_id": result_dp.machine_id
                    }
                ),
                "factors": (
                FOR calc_calc_factor IN InCalculation
                    FILTER calc_calc_factor._to == calculation._id
                    LET factor_dp = DOCUMENT(calc_calc_factor._from)
                    RETURN {
                    "_key": factor_dp._key,
                    "human_id": factor_dp.human_id,
                    "machine_id": factor_dp.machine_id
                    }
                )
            }
        )
        }
    }
    FILTER LENGTH(result.calculations.as_result) != 0 || LENGTH(result.calculations.as_factor) != 0
    SORT result.human_id
    RETURN result
    """
    bind_vars = {'given_dps': given_dps}
    return query_db(calculations_query, bind_vars, unlist=False)

def fetch_calculations_as_result(given_dps):
    calculations_query = """
    WITH DataPath, Calculation
    LET given_dps = @given_dps
    FOR dp IN DataPath
    FILTER dp.human_id IN given_dps || dp.machine_id IN given_dps
    LET result = {
        "_key": dp._key,
        "human_id": dp.human_id,
        "machine_id": dp.machine_id,
        "calculations": (
            FOR calc_result IN CalculationResult
            FILTER calc_result._to == dp._id
            LET calculation = DOCUMENT(calc_result._from)
            RETURN {
                "_key": calculation._key,
                "name": calculation.name,
                "factors": (
                FOR calc_factor IN InCalculation
                    FILTER calc_factor._to == calculation._id
                    LET factor_dp = DOCUMENT(calc_factor._from)
                    RETURN {
                    "_key": factor_dp._key,
                    "human_id": factor_dp.human_id,
                    "machine_id": factor_dp.machine_id
                    }
                )
            }
        )
    }
    FILTER LENGTH(result.calculations) != 0
    SORT result.human_id
    RETURN result
    """
    bind_vars = {'given_dps': given_dps}
    return query_db(calculations_query, bind_vars, unlist=False)

def fetch_calculations_as_factor(given_dps):
    calculations_query = """
    WITH DataPath, Calculation
    LET given_dps = @given_dps
    FOR dp IN DataPath
    FILTER dp.human_id IN given_dps || dp.machine_id IN given_dps
    LET result = {
        "_key": dp._key,
        "human_id": dp.human_id,
        "machine_id": dp.machine_id,
        "calculations": (
            FOR calc_factor IN InCalculation
            FILTER calc_factor._from == dp._id
            LET calculation = DOCUMENT(calc_factor._to)
            RETURN {
                "_key": calculation._key,
                "name": calculation.name,
                "result": FIRST(
                FOR result IN CalculationResult
                    FILTER calculation._id == result._from
                    LET result_dp = DOCUMENT(result._to)
                    RETURN {
                    "_key": result_dp._key,
                    "human_id": result_dp.human_id,
                    "machine_id": result_dp.machine_id
                    }
                ),
                "factors": (
                FOR calc_calc_factor IN InCalculation
                    FILTER calc_calc_factor._to == calculation._id
                    LET factor_dp = DOCUMENT(calc_calc_factor._from)
                    RETURN {
                    "_key": factor_dp._key,
                    "human_id": factor_dp.human_id,
                    "machine_id": factor_dp.machine_id
                    }
                )
            }
        )
    }
    FILTER LENGTH(result.calculations) != 0
    SORT result.human_id
    RETURN result
    """
    bind_vars = {'given_dps': given_dps}
    return query_db(calculations_query, bind_vars, unlist=False)

@app.route('/calculations_as_result', methods=['POST'])
def calculations_as_result():
    match_form = forms.MatchForm()
    if not match_form.validate_on_submit():
        return 'Invalid submission!'
    given_dps = match_form.paths.data.split()
    if not given_dps:
        return 'Nothing specified to match!'
    calculations = fetch_calculations_as_result(given_dps)
    return flask.jsonify(calculations)

@app.route('/calculations_as_factor', methods=['POST'])
def calculations_as_factor():
    match_form = forms.MatchForm()
    if not match_form.validate_on_submit():
        return 'Invalid submission!'
    given_dps = match_form.paths.data.split()
    if not given_dps:
        return 'Nothing specified to match!'
    calculations = fetch_calculations_as_factor(given_dps)
    return flask.jsonify(calculations)

@app.route('/calculations', methods=['POST'])
def calculations():
    match_form = forms.MatchForm()
    if not match_form.validate_on_submit():
        return 'Invalid submission!'
    given_dps = match_form.paths.data.split()
    if not given_dps:
        return 'Nothing specified to match!'
    calculations = fetch_calculations(given_dps)
    return flask.jsonify(calculations)

def fetch_collection_counts(given_collections):
    collection_count_query = """
    LET given_collections = @given_collections
    RETURN MERGE(
    FOR collection IN given_collections
        RETURN {
        [ collection ]: COLLECTION_COUNT(collection)
        }
    )
    """
    bind_vars = {'given_collections': given_collections}
    return query_db(collection_count_query, bind_vars)

@app.route('/collection-counts', methods=['POST'])
def collection_counts():
    requested_counts = flask.request.get_json()
    if not requested_counts:
        return 'Nothing specified to match!'
    collection_counts = fetch_collection_counts(requested_counts)
    return flask.jsonify(collection_counts)

@app.route('/search', methods=['GET'])
def search():
    search_form = construct_search_form()
    return flask.render_template('search.html', search_form=search_form)

@app.route('/search_es', methods=['GET'])
def search_es():
    search_form = construct_search_form(es=True)
    return flask.render_template('search_es.html', search_form=search_form)

@app.route('/api/v1/search', methods=['POST'])
def search_api():
    search_form = construct_search_form()
    if not search_form.validate_on_submit():
        return flask.jsonify(search_form.errors), 400
    filter_os_releases = {}
    for filter_os_release in search_form.oses.data:
        filter_os, filter_release = filter_os_release.split(' - ')
        filter_os = filter_os.strip()
        filter_release = filter_release.strip()
        if filter_os not in filter_os_releases:
            filter_os_releases[filter_os] = []
        filter_os_releases[filter_os].append(filter_release)
    filter_dmls = search_form.dmls.data
    filter_str = search_form.filter_str.data.strip()
    start_index = int(search_form.start_index.data)
    max_return_count = int(search_form.max_return_count.data)
    exclude_config = search_form.exclude_config.data
    only_leaves = search_form.only_leaves.data
    search_query_return = fetch_search_data_paths(
        filter_os_releases, filter_dmls, filter_str,
        exclude_config, only_leaves, start_index, max_return_count
    )
    return flask.jsonify(search_query_return)

@app.route('/api/v1/search/es', methods=['POST'])
def search_deep_api():
    search_form = construct_search_form(es=True)
    if not search_form.validate_on_submit():
        return flask.jsonify(search_form.errors), 400
    filter_os_releases = {}
    for filter_os_release in search_form.oses.data:
        filter_os, filter_release = filter_os_release.split(' - ')
        filter_os = filter_os.strip()
        filter_release = filter_release.strip()
        if filter_os not in filter_os_releases:
            filter_os_releases[filter_os] = []
        filter_os_releases[filter_os].append(filter_release)
    filter_dmls = search_form.dmls.data
    filter_str = search_form.filter_str.data.strip().lower()
    num_results = int(search_form.num_results.data)
    exclude_config = search_form.exclude_config.data
    only_leaves = search_form.only_leaves.data
    search_query_return = fetch_search_data_paths_es(
        filter_os_releases, filter_dmls, filter_str,
        exclude_config, only_leaves, num_results
    )
    return_dict = OrderedDict()
    return_dict['took'] = search_query_return['took']
    return_dict['hits'] = search_query_return['hits']['total']
    return_dict['human_id'] = OrderedDict()
    sorted_human_ids = sorted(search_query_return['aggregations']['human_id']['buckets'], key=lambda k: k['relevance']['value'], reverse=True)
    for human_id in sorted_human_ids:
        curr_human_id = return_dict['human_id'][human_id['key']] = {}
        curr_human_id['relevance'] = human_id['relevance']['value']
        curr_human_id['machine_id'] = {}
        for _key in human_id['dp_key']['buckets']:
            curr_human_id['machine_id'][_key['key']] = _key['machine_id']['buckets'][0]['key']
    # Flask sorts JSON output to improve cacheability, we have disabled this in __init__
    # We should actually restructure this response with relevance as a key instead of relying on ordering
    # in something which is explicitly designated as not requiring ordering (JSON).
    return flask.jsonify(return_dict)

def fetch_search_data_paths_es(filter_os_releases, filter_dmls, filter_str, exclude_config=True, only_leaves=True, num_results=150):
    search_body = {
        'size': 0,
        'sort': [
            '_score'
        ],
        'query': {
            'bool': {
                'must': [
                    {
                        'multi_match': {
                            'query': filter_str,
                            'operator': 'and',
                            'type': 'most_fields',
                            'fields': ['dp_human_id^3', 'dp_machine_id', 'dp_description']
                        }
                    }
                ],
                'filter': []
            }
        },
        'aggs': {
            'human_id': {
                'terms': {
                    'field': 'dp_human_id.keyword',
                    'size': num_results,
                    'order': {
                        'relevance': 'desc'
                    }
                },
                'aggs': {
                    'relevance': {
                        'max': {
                            'script': '_score'
                        }
                    },
                    'dp_key': {
                        'terms': {
                            'field': 'dp_key'
                        },
                        'aggs': {
                            'machine_id': {
                                'terms': {
                                    'field': 'dp_machine_id.keyword'
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    def gen_multi_choice_filter(term, choices):
        return {
            'bool': {
                'minimum_should_match': 1,
                'should': [
                    {
                        'match_phrase': {
                            term: choice
                        }
                    } for choice in choices
                ]
            }
        }
    def gen_boolean_filter(term, state):
        return {
            'match_phrase': {
                term: {
                    'query': state
                }
            }
        }
    if filter_os_releases or filter_dmls or exclude_config or only_leaves:
        query_filter = search_body['query']['bool']['filter']
        if filter_os_releases:
            query_filter.append(
                gen_multi_choice_filter(
                    'os_name',
                    filter_os_releases.keys()
                )
            )
            query_filter.append(
                gen_multi_choice_filter(
                    'release_name',
                    set(
                        chain.from_iterable(
                            filter_os_releases.values()
                        )
                    )
                )
            )
        if filter_dmls:
            query_filter.append(
                gen_multi_choice_filter(
                    'dml_name',
                    filter_dmls
                )
            )
        if exclude_config:
            query_filter.append(
                gen_boolean_filter('dp_is_configurable', False)
            )
        if only_leaves:
            query_filter.append(
                gen_boolean_filter('dp_is_leaf', True)
            )
        else:
            query_filter.append(
                gen_boolean_filter('dp_is_leaf', False)
            )
    client = Elasticsearch('http://search:9200')
    response = client.search(
        index='datapath',
        body=search_body
    )
    return response

def fetch_search_data_paths(filter_os_releases, filter_dmls, filter_str, exclude_config=True, only_leaves=True, start_index=0, max_return_count=10):
    search_data_paths_query = """
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
                                                            %s
                                                            %s
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
    """ % (
        'FILTER dp.is_configurable == False' if exclude_config else '',
        'FILTER dp.is_leaf == True' if only_leaves else ''
    )
    bind_vars = {
        'filter_os_releases': filter_os_releases,
        'filter_dmls': filter_dmls,
        'filter_str': filter_str,
        'start_index': start_index,
        'max_return_count': max_return_count
    }
    return query_db(search_data_paths_query, bind_vars)

def construct_search_form(es=False):
    search_form = None
    if es:
        search_form = forms.SearchFormES()
    else:
        search_form = forms.SearchForm()
    search_form.oses.choices = [(pair, pair) for pair in fetch_os_releases()]
    search_form.dmls.choices = [(pair, pair) for pair in fetch_dmls()]
    return search_form

def fetch_os_releases():
    os_releases_query = """
    FOR os IN OS
        FOR os_release IN OSHasRelease
        FILTER os_release._from == os._id
            FOR release IN Release
            FILTER release._id == os_release._to
            SORT os.name ASC, release.name DESC
            RETURN CONCAT_SEPARATOR(" - ", os.name, release.name)
    """
    return query_db(os_releases_query)

def fetch_dmls():
    dmls_query = """
    FOR dml IN DataModelLanguage
        SORT dml.name
        RETURN dml.name
    """
    return query_db(dmls_query)

@app.route('/map-bulk', methods=['GET'])
def html_map_bulk():
    return flask.render_template('map_bulk.html')

@app.route('/map-backup', methods=['GET'])
def html_map_backup():
    return flask.render_template('map_backup.html')

@app.route('/api/v1/datapath/arbitrary-id', methods=['POST'])
def api_datapath_from_arbitrary_id():
    api_req = flask.request.get_json()
    datapaths = fetch_datapath_arbitrary_id(api_req['id'])
    key = None
    error = None
    if not datapaths:
        error = 'No DataPaths found for ID!'
    elif len(datapaths) > 1:
        error = 'Multiple DataPaths found for ID! <a href="%s" target="_blank">Try being more specific with a Machine ID. :)</a>' % flask.url_for('datapath_direct')
    else:
        key = datapaths[0]['_key']
    return flask.jsonify(
        {
            'error': error,
            'key': key
        }
    )

@app.route('/api/v1/map/datapath/bulk', methods=['POST'])
def api_map_bulk():
    """Expects CSV with columns _from and _to.
    """
    mappings_file = None
    if not flask.request.files:
        return 'No files uploaded!', 400
    elif 'file' not in flask.request.files.keys():
        return 'Unexpected file submission!', 400
    else:
        mappings_file = flask.request.files['file']
    if not mappings_file:
        return 'No file uploaded!', 400
    elif not mappings_file.filename:
        return 'No filename for uploaded file!', 400
    elif not allowed_file(mappings_file.filename):
        return 'File type is not allowed!', 400
    elif not allowed_file(secure_filename(mappings_file.filename)):
        return 'File appears insecure and not allowed!', 400
    bulk_results = {'success': [], 'fail': []}
    with open(mappings_file.save()) as bulk_fd:
        bulk_csv = csv.DictReader(bulk_fd)
        for row in bulk_csv:
            try:
                map_datapath_single(row['First DataPath'], row['Second DataPath'], row['Author'], row['Annotation'])
                bulk_results['success'] += [[row['_from'], row['_to']]]
            except Exception:
                bulk_results['fail'] += [[row['_from'], row['_to']]]
    return flask.jsonify(bulk_results)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['json', 'csv']

@app.route('/api/v1/map/load/native', methods=['POST'])
def api_map_load_native():
    mappings_file = None
    if not flask.request.files:
        return 'No files uploaded!', 400
    elif 'file' not in flask.request.files.keys():
        return 'Unexpected file submission!', 400
    else:
        mappings_file = flask.request.files['file']
    if not mappings_file:
        return 'No file uploaded!', 400
    elif not mappings_file.filename:
        return 'No filename for uploaded file!', 400
    elif not allowed_file(mappings_file.filename):
        return 'File type is not allowed!', 400
    elif not allowed_file(secure_filename(mappings_file.filename)):
        return 'File appears insecure and not allowed!', 400
    mappings_json = json.load(mappings_file)
    failures = {
        'DataPathMatch': [],
        'Calculation': []
    }
    for mapping in mappings_json['DataPathMatch']:
        status = True
        try:
            # TODO: JSON key validations
            map_datapath_single(**mapping)
        except Exception as e:
            failures['DataPathMatch'].append(
                {
                    '_from': mapping['_from'],
                    '_to': mapping['_to'],
                    'message': str(e)
                }
            )
    for calculation in mappings_json['Calculation']:
        status = True
        try:
            # TODO: JSON key validations
            map_datapath_calculation_single(**calculation)
        except Exception as e:
            failures['Calculation'].append(
                {
                    'name': calculation['name'],
                    'InCalculation': calculation['InCalculation'],
                    'CalculationResult': calculation['CalculationResult'],
                    'message': str(e)
                }
            )
    return flask.jsonify(failures)

def map_datapath_calculation_single(name, description, equation, author, InCalculation, CalculationResult):
    in_calculation_ids = set()
    calculation_result_ids = set()
    check_fields = ['machine_id', 'human_id']
    for in_calc in InCalculation:
        in_calc_doc = check_collection_fields('DataPath', check_fields, in_calc)
        if in_calc_doc is not None:
            in_calculation_ids.add(in_calc_doc.next()['_id'])
    for calc_result in CalculationResult:
        calc_result_doc = check_collection_fields('DataPath', check_fields, calc_result)
        if calc_result_doc is not None:
            calculation_result_ids.add(calc_result_doc.next()['_id'])
    client = ArangoClient(protocol='http', host='dbms')
    db = client.db('tdm', username='root', password='tdm')
    calculation_collection = db.collection('Calculation')
    calculation_exists = calculation_collection.find({'name': name})
    if calculation_exists.count() > 0:
        raise Exception('Calculation of name %s already exists!' % name)
    app.logger.debug('Adding calculation %s', name)
    calc_doc = calculation_collection.insert(
        {
            'name': name,
            'description': description,
            'equation': equation,
            'author': author
        }
    )
    for dp_id in in_calculation_ids:
        add_mapping('InCalculation', dp_id, calc_doc['_id'])
    for dp_id in calculation_result_ids:
        add_mapping('CalculationResult', calc_doc['_id'], dp_id)

def map_datapath_single(_from, _to, author, annotation, timestamp=None, validated=False, weight=0, needs_human=True):
    dp_one_id = None
    dp_two_id = None
    check_fields = ['machine_id', 'human_id']
    dp_one_doc = check_collection_fields('DataPath', check_fields, _from)
    if dp_one_doc is not None:
        dp_one_id = dp_one_doc.next()['_id']
    dp_two_doc = check_collection_fields('DataPath', check_fields, _to)
    if dp_two_doc is not None:
        dp_two_id = dp_two_doc.next()['_id']
    if dp_one_id is None or dp_two_id is None:
        exception_messages = []
        if dp_one_id is None:
            exception_messages.append('Could not find %s!' % _from)
        if dp_two_id is None:
            exception_messages.append('Could not find %s!' % _to)
        raise Exception(' '.join(exception_messages))
    match_body = {
        'timestamp': timestamp or time.time(),
        'author': author,
        'validated': validated,
        'weight': weight,
        'annotation': annotation,
        'needs_human': needs_human or True if annotation else False
    }
    app.logger.debug('Mapping %s <-> %s', _from, _to)
    add_mapping('DataPathMatch', dp_one_id, dp_two_id, match_body)

@app.route('/api/v1/map/datapath/single', methods=['POST'])
def api_map_datapath_single():
    required_api_keys = {'mapOne', 'mapTwo', 'author'}
    api_req = flask.request.get_json()
    if not api_req:
        return flask.jsonify({'error': 'Invalid JSON!'}), 400
    if not required_api_keys.issubset(set(api_req.keys())):
        return flask.jsonify({'error': 'Required keys missing!'}), 400
    map_one = api_req['mapOne']
    map_two = api_req['mapTwo']
    author = api_req['author']
    annotation = api_req['annotation'] if 'annotation' in api_req.keys() else None
    try:
        map_datapath_single(map_one, map_two, author, annotation)
        return flask.jsonify({'error': None, 'result': True})
    except Exception as e:
        return flask.jsonify({'error': str(e), 'result': False}), 400

def map_datapath_single_by_key(basepath_key, matchpath_key, author, weight, annotation):
    basepath = fetch_datapath(basepath_key)
    if not basepath:
        raise Exception('Specified base DataPath not found!')
    matchpath = fetch_datapath(matchpath_key)
    if not matchpath:
        raise Exception('Specified matching DataPath not found!')
    client = ArangoClient(protocol='http', host='dbms')
    db = client.db('tdm', username='root', password='tdm')
    datapath_matches = db.collection('DataPathMatch')
    datapath_match_exist = datapath_matches.find({'_from': basepath['_id'], '_to': matchpath['_id']})
    if datapath_match_exist.count() != 0:
        raise Exception('Mapping already exists!')
    datapath_match_exist = datapath_matches.find({'_to': basepath['_id'], '_from': matchpath['_id']})
    if datapath_match_exist.count() != 0:
        raise Exception('Mapping already exists!')
    app.logger.debug('Mapping %s <-> %s', basepath['_id'], matchpath['_id'])
    datapath_matches.insert(
        {
            '_from': basepath['_id'],
            '_to': matchpath['_id'],
            'timestamp': time.time(),
            'author': author,
            'validated': False,
            'weight': weight,
            'annotation': annotation,
            'needs_human': False if not annotation or weight == 100 else True
        }
    )

def check_collection_fields(collection, fields, value, return_single=True, db=None):
    if db is None:
        client = ArangoClient(protocol='http', host='dbms')
        db = client.db('tdm', username='root', password='tdm')
    collection_ref = db.collection(collection)
    return_val = None
    exception_messages = []
    for field in fields:
        check = collection_ref.find({field: value})
        if return_single and check.count() > 1:
            exception_messages.append('More than one document exists for (%s: %s)!' % (field, value))
        elif check.count() > 0:
            return_val = check
            break
        else:
            exception_messages.append('Unable to find (%s: %s)!' % (field, value))
    if return_val is None and exception_messages:
        raise Exception(' '.join(exception_messages))
    return return_val

def add_mapping(edge_collection, from_id, to_id, body=None, check_bidirectional=True, db=None):
    if db is None:
        client = ArangoClient(protocol='http', host='dbms')
        db = client.db('tdm', username='root', password='tdm')
    collection_ref = db.collection(edge_collection)
    mapping = collection_ref.find({'_from': from_id, '_to': to_id})
    if mapping.count() != 0:
        raise Exception('Mapping already exists!')
    if check_bidirectional is True:
        mapping = collection_ref.find({'_to': from_id, '_from': to_id})
        if mapping.count() != 0:
            raise Exception('Mapping already exists!')
    if not body:
        body = {}
    body['_from'] = from_id
    body['_to'] = to_id
    collection_ref.insert(body)

def map_datapath_single(_from, _to, author, annotation, timestamp=None, validated=False, weight=0, needs_human=True):
    dp_one_id = None
    dp_two_id = None
    check_fields = ['machine_id', 'human_id']
    dp_one_doc = check_collection_fields('DataPath', check_fields, _from)
    if dp_one_doc is not None:
        dp_one_id = dp_one_doc.next()['_id']
    dp_two_doc = check_collection_fields('DataPath', check_fields, _to)
    if dp_two_doc is not None:
        dp_two_id = dp_two_doc.next()['_id']
    if dp_one_id is None or dp_two_id is None:
        exception_messages = []
        if dp_one_id is None:
            exception_messages.append('Could not find %s!' % _from)
        if dp_two_id is None:
            exception_messages.append('Could not find %s!' % _to)
        raise Exception(' '.join(exception_messages))
    match_body = {
        'timestamp': timestamp or time.time(),
        'author': author,
        'validated': validated,
        'weight': weight,
        'annotation': annotation,
        'needs_human': needs_human or True if annotation else False
    }
    app.logger.debug('Mapping %s <-> %s', _from, _to)
    add_mapping('DataPathMatch', dp_one_id, dp_two_id, match_body)

@app.route('/api/v1/map/dump/csv')
def api_dump_mappings_csv():
    mappings = fetch_dump_mappings()
    output_csv = io.StringIO()
    csv_writer = csv.DictWriter(
        output_csv,
        fieldnames=['First DataPath', 'Second DataPath', 'Author', 'Annotation']
    )
    csv_writer.writeheader()
    for mapping in mappings:
        pretty_mapping = {
            'First DataPath': mapping['first_dp'],
            'Second DataPath': mapping['second_dp'],
            'Author': mapping['author'],
            'Annotation': mapping['annotation']
        }
        csv_writer.writerow(pretty_mapping)
    return send_stringio(output_csv, 'text/csv', 'tdm_mappings.csv')

@app.route('/api/v1/map/dump/native')
def api_dump_mappings_native():
    mappings = fetch_dump_mappings_native()
    output_json = io.StringIO()
    json.dump(
        mappings,
        output_json
    )
    return send_stringio(output_json, 'application/json', 'tdm_mappings.json')

def send_stringio(stringio_obj, mimetype, filename):
    """We typically use StringIO but send_file requires BytesIO. Errorless.
    Wrap it.
    """
    stringio_obj.flush()
    stringio_obj.seek(0)
    output_buffer = io.BytesIO(stringio_obj.getvalue().encode())
    output_buffer.flush()
    stringio_obj.close()
    output_buffer.seek(0)
    return flask.send_file(
        output_buffer,
        mimetype=mimetype,
        attachment_filename=filename,
        as_attachment=True,
        cache_timeout=-1
    )

def fetch_dump_mappings_native():
    dump_aql = """
    RETURN {
        "DataPathMatch": (
            FOR dpm IN DataPathMatch
            RETURN {
                "_from": DOCUMENT(dpm._from).machine_id,
                "_to": DOCUMENT(dpm._to).machine_id,
                "author": dpm.author,
                "annotation": dpm.annotation,
                "timestamp": dpm.timestamp,
                "validated": dpm.validated,
                "weight": dpm.weight,
                "needs_human": dpm.needs_human
            }
        ),
        "Calculation": (
            FOR calc IN Calculation
            RETURN {
                "name": calc.name,
                "description": calc.description,
                "equation": calc.equation,
                "author": calc.author,
                "InCalculation": FLATTEN(
                FOR incalc IN InCalculation
                    FILTER incalc._to == calc._id
                    RETURN DOCUMENT(incalc._from).machine_id
                ),
                "CalculationResult": FLATTEN(
                FOR calcresult IN CalculationResult
                    FILTER calcresult._from == calc._id
                    RETURN DOCUMENT(calcresult._to).machine_id
                )
            }
        )
    }
    """
    return query_db(dump_aql)

def fetch_dump_mappings():
    dump_aql = """
    FOR dpm IN DataPathMatch
        RETURN {
            "first_dp": DOCUMENT(dpm._from).machine_id,
            "second_dp": DOCUMENT(dpm._to).machine_id,
            "author": dpm.author,
            "annotation": dpm.annotation
        }
    """
    return query_db(dump_aql)

def query_db(query, bind_vars=None, unlist=True):
    """Generically query database."""
    client = ArangoClient(protocol='http', host='dbms')
    db = client.db('tdm', username='root',password='tdm')
    cursor = db.aql.execute(query, bind_vars=bind_vars)
    # TODO: Pass as generator instead of fill array
    return_elements = [element for element in cursor]
    if unlist and len(return_elements) == 1:
        return_elements = return_elements[0]
    return return_elements

"""Ugly Jinja2 bandaid for XPath issues."""
def machine_id_to_8040(value):
    """Reformats the machine_id bastardized XPath to RFC 8040 compliance."""
    xpath_elements = value.split('/')
    module = xpath_elements[0]
    prefixed_elements = xpath_elements[1:]
    initial_prefix = prefixed_elements[0].split(':')[0]
    adjusted_elements = ['']
    for index, element in enumerate(prefixed_elements):
        prefix, element = element.split(':')
        if prefix == initial_prefix:
            adjusted_elements.append('%s:%s' % (module, element))
        else:
            adjusted_elements.extend(prefixed_elements[index:])
            break
    return machine_id_to_prefixed('/'.join(adjusted_elements))

def machine_id_to_prefixed(value):
    """Reformats the machine_id to simplified prefixed specification."""
    qualified_xpath = value[value.index('/'):]
    xpath_elements = qualified_xpath.split('/')[1:]
    running_prefix = None
    xpath_prefixed_elements = ['']
    for qualified_element in xpath_elements:
        prefix, element = qualified_element.split(':')
        if prefix == running_prefix:
            xpath_prefixed_elements.append(element)
        else:
            xpath_prefixed_elements.append('%s:%s' % (prefix, element))
            running_prefix = prefix
    return '/'.join(xpath_prefixed_elements)

app.jinja_env.filters['machine_id_to_8040'] = machine_id_to_8040
app.jinja_env.filters['machine_id_to_prefixed'] = machine_id_to_prefixed
"""End bandaid."""
