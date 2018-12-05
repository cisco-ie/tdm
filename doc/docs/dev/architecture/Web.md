# Web
TDM Web provides the API and a UI for prebaked, easier usage and operations against TDM.

[[toc]]

![TDM Web UI](/doc/img/index.png)

## Features
Features of Web have been implemented via [Flask](http://flask.pocoo.org/) in `web/src/web/`. Each feature has an associated "view" defined in `web/src/web/views.py` and [Jinja2](http://jinja.pocoo.org/docs/2.10/) template defined in `web/src/web/templates/`. JavaScript enabling each view is present within the respective Jinja2 template and is all vanilla.

### Search
This feature provides a nice pre-baked search interface to help search for data generically or across all OS/Release/Data Models. Using this interface, it is easy to query keywords of interest and determine potential data availability.

### Matchmaker
Matchmaker provides aid in situations where someone has a list of existing Data Paths (YANG XPaths, SNMP OIDs, etc.) and wishes to find equivalent Data Paths which are named differently but represent the same thing. For instance, OID `ifName` and XPath `openconfig-interfaces:interfaces/interface/state/name`.

### DataPath Direct
DataPath Direct takes a known Data Path and directly links to more information. For instance, navigating to the TDM URL for the `ifName` Data Path.

### All Mappings
This feature simply displays all Data Paths which have mappings.

### Import CSV
If someone has already created mappings for Data Paths but done so in an Excel spreadsheet, the mappings can be easily imported in CSV form into TDM via this interface.

### Documentation
:) Documentation is built from `/doc/` and uses [VuePress](https://vuepress.vuejs.org/).

### Backup/Restore
Backup the TDM database of Data Path Mappings.

## Libraries
* [Flask](http://flask.pocoo.org/)  
Flask is a Python microframework for web-based services development. It's super awesome.
* [python-arango](https://github.com/joowani/python-arango)  
Great Python ArangoDB client.
* [elasticsearch](https://github.com/elastic/elasticsearch-py)  
Low-level Elasticsearch client.
* [CiscoUIKit](https://github.com/CiscoDevNet/CiscoUIKit)  
Provides the HTML/CSS components and styling for the UI.

## API
We are looking at decoupling Web and API functionality, be on the lookout for more soon. The API is currently very loosely defined. If interested, search in `web/src/web/views.py` for routes containing `/api/v1/`.
