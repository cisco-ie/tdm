# TDM Overview

* [Usage](usage/)
* [Development](dev/)

- [TDM Overview](#tdm-overview)
    - [Plan](#plan)
    - [Problem Statement](#problem-statement)
    - [Solution](#solution)
        - [Elaboration](#elaboration)
    - [Components](#components)

* [Crash Course](Crash%20Course.md)
* [Cool Stuff](Cool%20Stuff.md)

## Plan
Anything besides the following must be addressed on an engagement/need basis.

- [x] MVP1 - Consume existing spreadsheets of mappings and provide same experience via UI.
- [x] MVP2 - Provide search and mapping capability via UI.
- [x] Exit Strategy - Open Source++
- [ ] Extended Goals - Recurring ETL process to remove any maintenance requirement and refactor code to be more maintainable.

## Problem Statement
In its current state, network telemetry can be accessed in many different ways that are not easily reconciled – for instance, finding the same information in SNMP MIBs and YANG models. There is no way of determining if the information gathered will have the same values either, or which is more accurate than another. Further, the operational methods of deploying this monitoring varies across platforms and implementations. This makes networking monitoring a fragmented ecosystem of inconsistent and unverified data. Discovering the datapoints in the first place is often tedious and somewhat arcane as well.

## Solution
TDM seeks to solve this problem by providing a simple schema to model all forms of accessing network telemetry and capability to create relationships between individual data points to demonstrate qualities in consistency, validity, and interoperability.

![TDM Schema](/doc/img/tdm_schema.png)

### Elaboration
We are seeking to alleviate two major problems using TDM.

1. The same data is addressed differently across platforms.
2. Data discovery is difficult.

The two problems above are especially prevalent now with data driving business-impacting decisions and with Streaming Telemetry/Model Driven Telemetry* coming to market. Our customers currently experience a difficult and uncertain upgrade path transitioning from SNMP to MDT. We hope that Telemetry Data Mapper will make it easy to map the data available from different protocols like SNMP, gRPC, NETCONF, etc. and serve as a source of truth for transformation and exploration of data across OS/Releases and platforms.

Telemetry Data Mapper encompasses more than just Streaming Telemetry - it seeks to enable mappings between any form of telemetry on any device or platform such as SNMP. The data points that are gathered via MDT or SNMP, etc. are what TDM focuses upon. The data points will be tracked on a per device/platform basis, and have relationships created between them in a database to illustrate equivalency, or whatever else we would like to track and demonstrate. Thus we can begin to see what data points are equivalent across devices and platforms, and begin to holistically collect and analyze the data.

As a side effect of the necessity of these mappings, we will also gain offline visibility in to what data is available for collection and the ability to easily explore the data. Further, we can begin analyzing data coverage, etc. Even more importantly, we can begin to validate the data on a cross-platform basis! There are huge quality assurance benefits to having an offline vision for our platform data.

In order to solve these problems, we must first understand all of the difficulties and arcane methods to get this data, and provide easy presentation and usage. *yay*

## Components

![Architecture](/doc/img/tdm_arch.png)

TDM is made up of several different technologies. These are expanded in their own code sub-directories if not here.
* [ETL Code](/etl/)
* [Web Code](/web/)
* [NGINX / Goaccess](/nginx/)
* [ArangoDB](https://www.arangodb.com/)  
ArangoDB was being used elsewhere in our team and thus we decided to bring it in to another project. Being a graph database, it had some attractive features, flexibility, and GUI that could in theory make it easier for relatively technical users to directly use the database instead of building custom web interfaces. ArangoDB contains our processed source of truth in TDM. The ETL process parses all of the different data we are interested in and formalizes relationships into ArangoDB to enable querying capabilities on the data instead of doing all the work in code. ArangoDB has a nice query language for traversing schemas, as it is a graph database, and simplifies some queries. However, it does come with some limitations in maturity such as lacking "views" (now implemented*), etc. We are currently using it very much like a relational database, and should likely eventually transition to an RDBMS. However, given it works and having operationalized around it, there's no pressing need to do so.
* [Elasticsearch](https://www.elastic.co/products/elasticsearch)  
Elasticsearch is effectively a mitigation of search difficulty in ArangoDB. In order to achieve reasonable performance, we wrote a query which resulted in monstrous RAM usage (32 GB for "bgp") with potential to take up to a minute to return. This was unacceptable. We could revisit aspects of TDM's design, but decided to try out ES. Elasticsearch receives all of the data in TDM in a denormalized form to enable fast and powerful search capabilities. Elasticsearch is perfectly suited to our search needs, and solved a couple search issues at once by implicitly handling fuzziness, scoring of results, and more. Our current usage is by no means perfect and is rather naive, but it's extremely fast and sits at a near constant 1 GB of RAM usage during search loads.
* [Kibana](https://www.elastic.co/products/kibana)  
Kibana provides a nice interface for exploring Elasticsearch and is useful for determining the Elasticsearch query structures to bring into custom interfaces. Elasticsearch's query syntax has many options, so having a tool which enables easy query iteration to see how the structure of the query needs to look is very useful. If TDM's Web UI Search does not meet your requirements - try using Kibana and open an issue for improvement.
