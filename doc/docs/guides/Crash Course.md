# Crash Course
This document aims to rapidly get technical users up to speed on concepts/technologies behind TDM to more effectively understand what is happening and begin developing. This crash course only briefly covers information regarding validation, such as how to request the data - we primarily focus on broader concepts. This also assumes some level of familiarity with basic terminology such as "CLI".

[[toc]]

## Data Sources

### Foreword
The term "Path" or "Data Path" will be used several times in the following discussion. A Path simply represents a certain way to address a certain data point. For instance `0x000001` could be considered a Path to a point in memory as a flat data map. Or in terms of a hierarchical data structure:
```json
{
  "Cisco": {
    "Data": {
      "Point": 1,
      "Rocks": true
    }
  }
}
```
We *could* represent the data as "Paths" of `Cisco/Data/Point` and `Cisco/Data/Rocks` to reference each individual data point separately, or use `Cisco/Data` to retrieve both `Point` and `Rocks` at the same time. We *could* also represent this data as `Cisco.Data.Point`, etc. A Path is simply a specification of some kind which navigates data.

### CLI
CLI is largely an unstructured data format which is easy for humans to parse but difficult for machines. Humans are able to relatively easily understand the relationships between output from CLI, but machines do not necessarily interpret things like "tables" of content with potentially different units, etc. easily. There is no declarative schema. Machines like things to be very cleanly labeled and associated - thus the movement toward data-models such as MIBs and YANG modules which pre-define the data. A large problem with CLI, looking at TDM, is that every Path in CLI, while hierarchical, contains different information. When we pull a top level path of CLI there is no guarantee that the sublevel Path output will be in the top-level Path, unlike YANG or SNMP which will always include the same data at sublevels. CLIs can become more specific and completely change in output from the top-down. Thus we must map each CLI command individually and cannot necessarily automatically infer that a higher-level CLI Path will have a lower-level's information.

In terms of the difficulty indexing CLI data, there are some platforms which are taking an interesting approach to this issue by allowing for the underlying data representation to be outputted in its structured format as opposed to the human format. NX-OS is a good example of this kind of support, and is demonstrated in the second example below.

#### CLI Example (Path)
Every level of a CLI command would be considered a component of its Path. The ` ` (space) is the delimiter for each CLI element of the hierarchy.

```
show
show ipv4
show ipv4 interface
show ipv4 interface summary
```

Demonstrating the hierarchichal data inconsistencies:
```
RP/0/RP0/CPU0:dr02#show ipv4 interface
Tue Feb 13 12:28:18.205 PST
Loopback0 is Up, ipv4 protocol is Up
  Vrf is default (vrfid 0x60000000)
  Internet address is 10.1.1.52/32
  MTU is 1500 (1500 is available to IP)
  Helper address is not set
  Directed broadcast forwarding is disabled
  Outgoing access list is not set
  Inbound  common access list is not set, access list is not set
  Proxy ARP is disabled
  ICMP redirects are never sent
  ICMP unreachables are always sent
  ICMP mask replies are never sent
  Table Id is 0xe0000000
MgmtEth0/RP0/CPU0/0 is Up, ipv4 protocol is Up
  Vrf is default (vrfid 0x60000000)
  Internet address is 10.200.96.13/24
  MTU is 1514 (1500 is available to IP)
  Helper address is not set
  Multicast reserved groups joined: 224.0.0.2 224.0.0.1
  Directed broadcast forwarding is disabled
  Outgoing access list is not set
  Inbound  common access list is not set, access list is not set
  Proxy ARP is disabled
  ICMP redirects are never sent
  ICMP unreachables are always sent
  ICMP mask replies are never sent
  Table Id is 0xe0000000

RP/0/RP0/CPU0:dr02#show ipv4 interface summary
Tue Feb 13 14:31:57.208 PST

IP address      State   State           State           State
config          up,up   up,down         down,down       shutdown,down
----------------------------------------------------------------------
Assigned        21      0               1               0
Unnumbered      0       0               0               0
Unassigned      0       0               2               51
```

Notice how there is not necessarily a direct correlation in the data. Some aspects of it may be inferred, but are not directly represented. Now for the NX-OS, structured JSON representation that is possible.

```
rswA6# show ip interface brief

IP Interface Status for VRF "default"(1)
Interface            IP Address      Interface Status
Vlan62               172.31.156.1    protocol-up/link-up/admin-up
Eth1/29              172.31.1.113    protocol-up/link-up/admin-up
Eth1/30              172.31.1.115    protocol-up/link-up/admin-up
Eth1/31              172.31.1.117    protocol-up/link-up/admin-up
Eth1/32              172.31.1.119    protocol-up/link-up/admin-up

rswA6# show ip interface brief | json
{"TABLE_intf": {"ROW_intf": [{"vrf-name-out": "default", "intf-name": "Vlan62", "proto-state": "up", "link-state": "up", "admin-state": "up", "iod": "2", "prefix": "172.31.156.1", "ip-disabled": "FALSE"}, {"vrf-name-out": "default", "intf-name": "Eth1/29", "proto-state": "up", "link-state": "up", "admin-state": "up", "iod": "36", "prefix": "172.31.1.113", "ip-disabled": "FALSE"}, {"vrf-name-out": "default", "intf-name": "Eth1/30", "proto-state": "up", "link-state": "up", "admin-state": "up", "iod": "37", "prefix": "172.31.1.115", "ip-disabled": "FALSE"}, {"vrf-name-out": "default", "intf-name": "Eth1/31", "proto-state": "up", "link-state": "up", "admin-state": "up", "iod": "38", "prefix": "172.31.1.117", "ip-disabled": "FALSE"}, {"vrf-name-out": "default", "intf-name": "Eth1/32", "proto-state": "up", "link-state": "up", "admin-state": "up", "iod": "39", "prefix": "172.31.1.119", "ip-disabled": "FALSE"}]}}
```

This enables, in some cases, for CLI to be easily "indexable" with individual data points. However, it is difficult to define a common "CLI" schema which addresses both structured and unstructured data. This is a yet unsolved problem in TDM - what is our Path schema for CLI? Individual CLI command buckets, with no attempt to index elements, appears to be the easiest methodology. We will not pay a significant amount of attention to it now, and focus on fully structured data models.

### MIBs (SNMP)
[SNMP](https://tools.ietf.org/html/rfc1157) (Simple Network Management Protocol) uses [MIB](https://tools.ietf.org/html/rfc3418)s (Management Information Base) which define [OID](https://tools.ietf.org/html/rfc3061)s (Object Identifier) which are able to be referenced to pull certain points of data from the device. MIBs are written in [SMI](https://tools.ietf.org/html/rfc2578) (Structured Management Information) language, which is derived but different from [ASN.1](https://www.itu.int/ITU-T/studygroups/com17/languages/). SNMP is the "protocol", MIBs are the "models", and SMI is the "modeling language". There are multiple versions of SNMP and SMI which separately have their own capabilities and support - which we are not going to try and think about at the moment. The most widely supported version is SNMPv2 so we are focusing almost explicitly on SNMPv2. SNMP et al. has many revisions and a lot of complexity that we are simply going to gloss over and pretend is totally homogenous. We don't care about its intricacies as long as we're able to consistently retrieve data from a device using a certain representation of the data - which we have in the form of OIDs!

#### OID Example (Path)
```
# In the format machines like...
1.3.6.1.4.1.9.9.187.1.2.5.1.25
# Or, in human readable form...
iso.org.dod.internet.private.enterprises.cisco.ciscoMgmt.ciscoBgp4MIB.ciscoBgp4MIBObjects.cbgpPeer.cbgpPeer2Table.cbgpPeer2Entry.cbgpPeer2RemoteAs
```

#### Data Model Exploration
Exploring MIB data models is most easily accomplished via net-snmp's [snmptranslate](http://www.net-snmp.org/docs/man/snmptranslate.html). This tool can translate MIBs to OIDs, and provide a tree-like data exploration interface. There are many other commercial and graphical toolings around SNMP that exist as well which will not be covered due to primarily being interested in low-level, machine-parseable outputs to input in to TDM.

#### Data Exploration
SNMP is the protocol used to actually retrieve data from a live device, and there are tons of products built around gathering SNMP data and displaying it. The [net-snmp](http://www.net-snmp.org/) toolings are the most well known and supported for walking, getting individual data points, etc.

### YANG Modules (NETCONF, RESTCONF, gRPC)
[NETCONF](https://tools.ietf.org/html/rfc6241) (Network Configuration Protocol) and [gRPC](https://grpc.io/) (gRPC 😉) use [YANG](https://tools.ietf.org/html/rfc6020) (Yet Another Next Generation) modules which define [XPath](https://www.w3.org/TR/xpath20/)s (XML Path Language) which are able to be referenced to pull certain points of data from the device. YANG moduls are written in the YANG language. It's convoluted in that there is no formal separation of terminology. NETCONF & gRPC are the "protocols", YANG modules are the "models", and YANG is the "modeling language". NETCONF and gRPC can specify and filter data in two ways - XPaths and Subtrees. For TDM's purposes we are going to focus explicitly on XPaths as they are easily expressed akin to OIDs. XPaths are able to be translated to NETCONF XML and gRPC JSON, thus XPaths are our most basic representation of a YANG-module defined data element.

#### XPath Example (Path)
```
Cisco-IOS-XR-infra-syslog-oper:syslog/logging-statistics/console-logging-stats/is-log-enabled
```

#### Data Model Exploration
Cisco publicly publishes purportedly supported YANG modules, per OS and per version, on [GitHub](https://github.com/YangModels/yang/tree/master/vendor/cisco). This raw information is what we currently use as our base of YANG information. There is also the [YANG Catalog](https://yangcatalog.org/) providing a superset of information and an ongoing metadata database which we should likely retool around. There is a proliferation of tools for exploration of YANG modules. The current, easiest tool to use is [`pyang`](https://github.com/mbj4668/pyang) which is similar to [`pysmi`](https://github.com/etingof/pysmi) or `snmptranslate`. It enables exploration of a YANG module in its compiled, hierarchical tree form (or other outputs) to get a better idea of how the data will look in its XPath form. There is also [YANG Suite](http://ys.yangcatalog.org/) hosted on YANG Catalog, and [yang-explorer](https://github.com/CiscoDevNet/yang-explorer) which provide useful GUIs. `pyang` is our main focus due to its ability to output low level manipulations of YANG modules programatically.

#### Data Exploration
Data exploration of YANG modules varies on a per-platform basis. NETCONF is the most well-supported cross-platform methodology. [Advanced NETCONF Explorer (ANX)](https://github.com/cisco-ie/anx) is an excellent tool for exploring an online device's NETCONF/gRPC/gNMI data. [ncclient](https://github.com/ncclient/ncclient) is the most well supported low-level NETCONF explorer. There are some IOS XR specific gRPC connection libraries that may be used to explore data via gRPC as well, such as [ios-xr-grpc-python](https://github.com/cisco-grpc-connection-libs/ios-xr-grpc-python).

### DME (NX-API, NX-OS Streaming Telemetry)
DME (Data Management Engine) is an NX-OS specific data structure which provides data accessible via DN (Distinguished Name) Paths. DME is the source of information in NX-OS for [streaming telemetry](https://www.cisco.com/c/en/us/td/docs/switches/datacenter/nexus9000/sw/7-x/programmability/guide/b_Cisco_Nexus_9000_Series_NX-OS_Programmability_Guide_7x/b_Cisco_Nexus_9000_Series_NX-OS_Programmability_Guide_7x_chapter_011000.html#id_40248), alongside CLI. NX-OS provides an "NX-API" which in conjunction with DME is akin to NETCONF:YANG. NX-API/DME:NETCONF/YANG. DME is similar to MIBs and YANG modules, and doesn't require a tremendous amount of explanation. It has a path. 🙂

#### DN Example
```
sys/bgp/inst/dom-default
```

#### Data Model Exploration
DME can be explored via `http://<nx-os_ip>/visore.html` on NX-OS devices. In a web browser, navigate to an accessible NX-OS device which supports DME.

#### Data Exploration
 There is a [Developer Sandbox](https://www.cisco.com/c/en/us/td/docs/switches/datacenter/nexus9000/sw/7-x/programmability/guide/b_Cisco_Nexus_9000_Series_NX-OS_Programmability_Guide_7x/b_Cisco_Nexus_9000_Series_NX-OS_Programmability_Guide_7x_chapter_010010.html) hosted on the device which assists in conversion of CLI to NX-API, etc.

## Development

### Docker
[Docker](https://www.docker.com/) is an incredibly useful utility in that it resolves a significant amount of packaging and deployment difficulty that may have been experienced in the past. It (effectively) "containerizes" an OS ecosystem so that you never have a shared library conflict or random configuration conflict ever again. It is (effectively) the de-facto container deployment technology now today. One of the benefits here is that when you download TDM, you only need Docker as a dependency and our associated Docker-related files will resolve all internal dependencies with zero human work involved. This is amazing for development, and for production we can look towards bare-metal if there are performance concerns. Docker has a nice [Get Started](https://docs.docker.com/get-started/) series, just read this section in its entirety.

### ArangoDB
[ArangoDB](https://arangodb.com/) is a fairly unique database. It accomodates several powerful concepts at once allowing for powerful query capabilities. With a combination of graph, key/value, and document storage - it is possible to execute graph queries which filter on key/values and return documents (as an example). This is not a common capability. For reference, please read the [ArangoDB manual](https://docs.arangodb.com/latest/Manual/).

### Elasticsearch
[Elasticsearch](https://www.elastic.co/) provides extremely fast search and analysis capabilities against almost any corpus of data able to be fed into it. Elasticsearch is used for the Search feature.

## Learning Resources

### Videos
* [Data Modeling Driven Management: Latest Industry and Tool Developments](https://www.youtube.com/watch?v=n_oKGJ_jgYQ)  
This talk covers YANG and more. Benoit Claise is a very knowledgeable guy when it comes to this stuff.
* [Introduction to SNMP - Simple Network Management Protocol](https://www.youtube.com/watch?v=ZX-XGQoISHQ)
* [Docker Tutorial - What is Docker & Docker Containers, Images, etc?](https://www.youtube.com/watch?v=pGYAg7TMmp0)
* [Graph Databases Will Change Your Freakin Life](https://www.youtube.com/watch?v=3vleFxDGoEs)  
This is a nice introduction to understanding graph databases, and why we might want to use them in this project!

### xrdocs.github.io
[xrdocs](https://xrdocs.github.io/) is perhaps one of the best resources to learn about Model-Driven Telemetry usage. It details how to gain access to IOS XRv, configure MDT, and use MDT via `pipeline`. This is IOS XR specific, but covers usage of YANG modules which is valuable.

### DevNet
DevNet has a wide range of resources. The Learning Labs are especially useful for hands on activity.
* [YANG](https://developer.cisco.com/search/yang#)
* [NETCONF](https://developer.cisco.com/search/netconf#)
* [gRPC](https://developer.cisco.com/search/grpc#)
* [Telemetry](https://developer.cisco.com/search/telemetry#)

### dCloud
The [Cisco Consuming XR Model Driven Streaming Telemetry Lab v1 dCloud lab](https://dcloud2-sjc.cisco.com/content/demo/49422) put together by Marco Umer is very useful in covering the entire range of what can be done with the data. It is also available publicly at [cisco-ie/telemetry-staging-ansible](https://github.com/cisco-ie/telemetry-staging-ansible).
