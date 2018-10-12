# TDM Web
TDM Web provides the API and a UI for prebaked, easier usage and operations against TDM.

The current structure is pretty messy and there is not a clear separation of concerns between the UI elements and APIs. There is also no real planning on the API as well. Basically, we need some serious refactoring. :)

## Features
* Data (DataPath) Search  
This feature provides a nice pre-baked search interface to help search for data generically or across all OS/Releases/Data Models.
* Bulk Mapping Check  
Provide a list of Data Paths (YANG XPaths, SNMP OIDs, etc.) and find the equivalent things! OID <-> XPath.
* Individual Data (DataPath) View  
Jump straight to a detailed view of a certain Data Path.
* Mapping Import/Export  
Backup the TDM database of Data Path Mappings.

## Libraries
* [Flask](http://flask.pocoo.org/)  
Flask is a Python microframework for web-based services development. It's super awesome.
* [python-arango](https://github.com/joowani/python-arango)  
Great Python ArangoDB client.
* [elasticsearch](https://github.com/elastic/elasticsearch-py)  
Low-level Elasticsearch client.

## Improvements
* Matchmaker should filter on OS/Release and DataModelLanguage, as well as platforms.
* We should have a DataModel view which displays the DataPaths in a tree view. YANG Catalog accommodates this but we can't link back to TDM if we do that.
* Should clean up views.py with clean separation of the HTML views and APIs as well as logical organization of functions.
* DataPath view should indicate the associated OS/Releases/Platforms, and the displayed Matches should indicate their verification status and other interesting properties. A "Details" view should be present to get all the detailed attributes of the mapping.
* DataPath Match should be limited to leaf nodes only.
* DataPath View pathing should rely on the Machine ID not the _key. _key will vary per ETL. (???)
