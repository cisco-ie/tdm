# ETL
ETL stands for Extract, Transform, Load and is a thought framework for how to go about parsing relatively raw data into data supporting your deliverable outcomes. In TDM, we extract data models from their respective sources, transform the data models into some intermediary representation, and load the relationships easily parseable from the intermediary representation into a source-of-truth, parsed database. We then use this source-of-truth to load other caches of information, such as the Search database.

[[toc]]

The ETL code converts source data to the format of TDM's database schema. TDM's ETL process currently only handles Cisco operating systems but could easily handle other operating systems data if that data pipeline is built.

The TDM ETL code consists of custom Python at the moment. There is no ETL framework involved, just a series of functions being called. We should eventually move to an ETL framework for better features and maintainability. Also, this *desperately* needs to be refactored, recurring, and multithreaded. It makes some assumptions about filesystem layout as well (addressed in [Directory Structure](#directory-structure)).

## Libraries
* [pyang](https://github.com/mbj4668/pyang)  
`pyang` is a beautiful Python YANG tooling which is really useful for exploring YANG models. Dissecting some of the plugins, and a [custom attempt](https://github.com/remingtonc/pyang-as-lib) at using it like a library, we have derived custom YANG model parsing into our desired representation of XPaths which then load into TDM.
* [pysmi](https://github.com/etingof/pysmi)  
An inspiration to `pyang`, `pysmi` does for MIBs what `pyang` does for YANG models. We use `pysmi` to parse MIBs into OIDs and structured into JSON which we then parse to load into TDM.
* [elasticsearch](https://github.com/elastic/elasticsearch-py)  
Low level client for Elasticsearch. We had some difficulty using the Elasticsearch DSL library and sometimes it's easiest to use low-level abstractions.
* [pyArango](https://github.com/tariqdaouda/pyArango)  
Use [python-arango](https://github.com/joowani/python-arango) instead. For some reason this is recommended by ArangoDB in some tutorials, and we decided to use `pyArango` in ETL and `python-arango` in Web purely for comparison of the libraries. `python-arango` has won our hearts, and pyArango is questionably maintained. [1](https://github.com/tariqdaouda/pyArango/issues/105) [2](https://github.com/tariqdaouda/pyArango/issues/111)

## Process
The ETL process is simply a sequential series of steps right now.

### MIBs (SNMP)
There are actually a lot of missing pieces to the MIB loading into TDM. This is less of a technical issue and more of a business issue which just simply hasn't been addressed. We'll get into that after the basic process.

1) Download all MIBs from ftp://ftp.cisco.com/pub/mibs/v2/
2) Transform MIBs to JSON representation with `pysmi`.
3) Parse JSON representation into MIB & OID relationships.
4) Load relationships into TDM as MIB (DataModel) -> OID (DataPath).

What is the big missing piece? The linking of Data Models to Operating Systems/Release versions. Given the SNMP legacy, that kind of release process data just simply doesn't seem to exist via an easily consumable API (please open an issue to tell me I am wrong). For Cisco at least, we can get some level of insight via supportlists at `ftp://ftp.cisco.com/pub/mibs/supportlists/`, but these tend to lean towards being semi-hand-written HTML documents and not very machine consumable. Hence, business problem. :)

### YANG Models
The YANG model loading process is far more complete than the MIBs. This is thanks to a vastly better release process of data models and metadata for the OS via the [YangModels/yang](https://github.com/YangModels/yang/tree/master/vendor/cisco) repository. Currently TDM parses data directly from the YANG repository but it is likely a better idea to re-engineer this pipeline around [YANG Catalog](https://yangcatalog.org/) which is an overlay of the repository and has APIs for even more metadata we can use.

1. `git clone https://github.com/YangModels/yang.git`
2. Skip other vendors or YANG models, go straight to [Cisco](https://github.com/YangModels/yang/tree/master/vendor/cisco).
3. Per OS, per release, parse YANG models via `pyang` into a Python dictionary.
4. Load `OS -> Release -&- Data Model Language (YANG) -> Data Model (YANG Model) -> Data Path (XPath)` into TDM. There is some *really* ugly caching going on here as well that needs to be fixed.

The YANG ETL process is currently wildly inefficient. Like 7 GB RAM inefficient. It happened, it was glossed over, it was not looked at again in favor of our nice Web value-add interface. It needs to be looked at again.

You might notice the weird `Release -&- Data Model Language -> Data Model` specified here. This is a potential reflection of a flaw in TDM's schema design. Currently Data Models are linked to both Releases and Data Model Languages as those both "own" the Data Models in some sense and can't be linearly expressed. The Data Model Language could be a attributes of the Data Models themselves instead of (or alongside!) actual entities but currently this works out as is and requires some more thought.

### Into Elasticsearch!
Once MIBs and YANG models (we should multithread that) are loaded into ArangoDB we denormalize all those relationships and pump it into Elasticsearch to fuel our search capabilities in the Web interface. We index nearly ever property but only use the `human_id`, `machine_id`, and `description` of each DataPath for searching. This currently ends up ~2 million documents denormalized.

## Directory Structure

### Cache
`cache/` is a mounted volume via Docker to aid in debugging of the ETL process.

* `cache/extract` <-> `/data/extract`
* `cache/transform` <-> `/data/transform`

Any stage may write files to `/data/extract/` or `/data/transform/` and have them visible and exposed to the host system via this directory.

## Improvements
* There is a lot of mismatching terminology lately. Mappings and Matches, etc. We need to nail this down and refactor appropriately.
* ETL for MIBs does not populate the data correctly. e.g. Maintaining parent/child relationship with OIDs. This should be fixed and given YANG population parity. We also don't indicate Data Type for OIDs which is a big issue.
* DataPathMatch shouldn't have any sort of "confidence" set by humans, we can't quantify that right now. If we start doing NLP or any machine learning then confidence can be set by that process against the data. A human "confidence" rating is relatively useless.
* We should create a sort of shadow object for all matches/calculations to point to which we can then label as a theoretical concept.
* Should rebuild the ETL process using an ETL framework which provides ETL visibility, pipelines, etc. Not arbitrary code. Potentials... Apache Airflow (limitation on data not passed between tasks), Bonobo (doesn't have nice visualizations)..
* It might be nice to more concretely model DataPaths into YANGDataPath, OIDDataPath, etc. to reduce the search space per DataModelLanguage and have per DataPath-relevant attributes.
