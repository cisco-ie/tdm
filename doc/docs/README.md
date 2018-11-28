# Overview
**Welcome to TDM!** This documentation should help you get started being productive with TDM.

[[toc]]

## [Guides](/guides/)
If you want to get started using TDM productively, this is where to start.

## [Developer Documentation](/dev/)
If you're interested in programatically using or contributing to TDM, this is where to start.

## Problem
In its current state, network telemetry can be accessed in many different ways that are not easily reconciled – for instance, finding the same information in SNMP MIBs and NETCONF/YANG modules. Discovering the datapaths is often tedious and somewhat arcane, and there is no way of determining if the information gathered will have the same values, or which is more accurate than another. Further, the operational methods of deploying this monitoring varies across platforms and implementations. This makes networking monitoring a fragmented ecosystem of inconsistent and unverified data. There needs to be manageability, and cross-domain insight into data availability.

## Solution
TDM seeks to solve this problem by providing a platform to generically access network telemetry and capability purported to be supported by an OS/release or platform, and create relationships between individual datapaths to demonstrate qualities in consistency, validity, and interoperability. This will be both exposed by UI for human usage, and API for automated usage. TDM will not seek to provide domain-specific manageability, but serve as an overlay insight tool.

![TDM UI](/doc/img/index.png)

### Elaboration
We are seeking to alleviate two major problems using TDM.

1. The same data is addressed differently across platforms.
2. Data discovery is difficult.

The two problems above are especially prevalent now with data driving business-impacting decisions and with Streaming Telemetry/Model-Driven Telemetry* coming to market. We currently experience a difficult and uncertain upgrade path transitioning from SNMP to MDT. We hope that Telemetry Data Mapper will make it easy to map the data available from different protocols like SNMP, gRPC, NETCONF, etc. and serve as a source of truth for transformation and exploration of data across OS/releases and platforms.

Telemetry Data Mapper encompasses more than just SNMP/Model-Driven Telemetry - it seeks to enable mappings between any form of telemetry on any device or platform. Datapaths identifying a unit of information are tracked, and the datapaths will be tracked on a per device/platform basis, and have relationships created between them in a database to illustrate equivalency, or whatever else we would like to track and demonstrate. Thus we can begin to see what data points are equivalent across devices and platforms, and begin to holistically collect and analyze the data.

As a side effect of the necessity of these mappings, we will also gain offline visibility in to what data is available for collection and the ability to easily explore the data. Further, we can begin analyzing data coverage, etc. Even more importantly, we can begin to validate the data on a cross-platform basis! There are huge quality assurance benefits to having an offline vision for platform data.

In order to solve these problems, we must first understand all of the difficulties and arcane methods to get this data, and provide easy presentation and usage. *yay*
