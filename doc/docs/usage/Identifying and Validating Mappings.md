# Identifying and Validating Mappings
Identifying and validating the mappings between Data Paths can be the most frustrating part of using and contributing to TDM. Unfortunately this process is not always easy nor are there tools to do it automatically. TDM attempts to assist with this process via Search, This document will walk through the usage of TDM and relevant tooling to identify relevant Data Paths, and how to validate whether Data Paths which appear similar may be considered enough of a match to map in TDM.

## Identifying Relevant Data
The statement of "Identifying Relevant Data" can be processed in several different contexts. Sometimes you have domain knowledge that you'd like to find data about, other times you have existing data that you'd like to find equivalents for. For instance, finding Data Paths representing the BGP neighbor count versus finding an equivalent YANG XPath for the OID `ifName`. Ultimately TDM seeks to aid in finding information for both of these use cases, but is more suited to domain-specific knowledge-like searches.

TDM's Search is built with ElasticSearch, an amazing database for full-text search. In Search, we compare the Human ID, Machine ID, and Description of each Data Path to the keywords in the query string and attempt to weight out the relevancy of each Data Path. We also try to normalize synonyms like `intf`, `interface`, etc. to assist different terminologies. Here are some guidelines to best use TDM's Search.

### Identifying Similar Data Paths
If you already have Data Paths (like SNMP OIDs) that you'd like to find equivalent data for, which is represented differently (like YANG XPaths), here are some easy guidelines to help TDM help you.

1. Break it down.

Your Data Paths might be very specific, long, and unintuitive to the human eye. For instance...

```
ifHCInUcastPkts
/Cisco-NX-OS-device:System/nd-items/inst-items/dom-items/Dom-list/if-items/If-list/vaddrstat-items/VaddrStat-list/vip-items/VaddrStatVip-list/raSent
Cisco-IOS-XR-pbr-vservice-ea-oper:service-function-chaining/nodes/node/process/service-function-forwarder/local/error/data/sf/processed-pkts
```

These Data Paths contain a lot of information! The key to best searching TDM is to break down the Data Paths in to something easily searchable by keyword.

```
# ifHCInUcastPkts
interface sent
interface ucast sent
...
# /Cisco-NX-OS-device:System/nd-items/inst-items/dom-items/Dom-list/if-items/If-list/vaddrstat-items/VaddrStat-list/vip-items/VaddrStatVip-list/raSent
interface ra sent
...
# /Cisco-IOS-XR-pbr-vservice-ea-oper:service-function-chaining/nodes/node/process/service-function-forwarder/local/error/data/sf/processed-pkts
service processed packets
...
```

It's important to acknowledge that sometimes there will not be an equivalent Data Path available, but Search should be able to at least help you get started seeking the same data.

2. Look at the Description in TDM.

If keyword search hasn't helped, it's typically useful to get more information about the Data Path itself and what it represents. For instance, the earlier example of `/Cisco-NX-OS-device:System/nd-items/inst-items/dom-items/Dom-list/if-items/If-list/vaddrstat-items/VaddrStat-list/vip-items/VaddrStatVip-list/raSent`, what is `raSent` describing? Using DataPath Direct, we can quickly navigate to this Data Path in TDM and examine its description. It appears, based on the Description, that this is "Router Advertisements sent"! This is much easier to search on, and we might have more success using the more qualified description. e.g. `interface router advertisement sent`.

This is also valuable for determining if two Data Paths which look similar by Human ID actually represent the same thing. It is easy to find this information by simply clicking on the interesting search result. It is always a good idea to evaluate the Description after identifying an interesting looking Data Path.

### Domain Specific Knowledge
TDM is well suited to helping to identify domain-specific knowledge related Data Paths. Domain specific knowledge is easily represented by keyword-like searches which is what TDM's Search functionality is most suited for. The above section is effectively an attempt to decompose the structure of the Data Paths into more generic ideas. `bgp neighbor messages sent` is more easily communicated than `/Cisco-IOS-XR-ipv4-bgp-oper:bgp/instances/instance/instance-active/default-vrf/neighbors/neighbor/messages-sent`. Attempt to use generic, yet specific, terms and you'll likely have some success identifying information you're interested in.

## Evaluating Similar Data Paths
Once we've identified similar Data Paths, we have a responsibility to verify that these Data Paths return equivalent data before mapping them in TDM. Leading others down a rabbit hole of incorrect information is irresponsible and rather infuriating. Ensuring that the data in TDM is high-quality and trustworthy is a requirement for its success as a platform for finding this kind of information. If incorrect data or mappings are identified, flag them for explanation or removal.

This section will go over how to retrieve Data Paths currently available in TDM, and begin evaluating the data returned.

### YANG XPath
YANG module data is represented as a TDM Data Path via its XPaths. To explore YANG XPaths, we will utilize the very useful [Advanced NETCONF Explorer](https://github.com/cisco-ie/anx) which presents an intuitive GUI interface via the web browser for exploring an online device's YANG modules.

ANX needs to be deployed on a server which is able to reach a NETCONF-enabled online device. Actual installation of ANX is out of the scope of this document, but a quick overview using Docker:

```bash
# If necessary...
ssh <host>
# Download ANX
git clone https://github.com/cisco-ie/anx.git
# If git is not available...
wget https://github.com/cisco-ie/anx/archive/master.tar.gz && tar -xzf master.tar.gz && rm master.tar.gz && mv anx-master anx
cd anx
docker build -t cisco-ie/anx .
docker run --name anx -d -p 9269:8080 cisco-ie/anx
# Open browser to <host>:9269
```

### MIB OID (SNMP)
SNMP MIB data is represented as a TDM Data Path via its OIDs. To explore OIDs, we will utilize the venerable `snmpwalk` which has been around for years and is always reliable. `snmpwalk` can sometimes be a little bit nuanced, but we will try to get its basic usage down.
