# Identifying and Validating Mappings
Identifying and validating the mappings between Data Paths can be the most frustrating part of using and contributing to TDM. Unfortunately this process is not always easy nor are there tools to do it automatically. This document will walk through the usage of TDM and relevant tooling to identify relevant Data Paths, and how to validate whether Data Paths which appear similar may be considered enough of a match to map in TDM.

[[toc]]

## Identifying Relevant Data
"Identifying Relevant Data" might mean different things to different people. Some will have existing data they'd like to find equivalents for, and may or may not understand what that data means. For instance, finding the NETCONF/YANG XPath equivalent of the `ifName` SNMP OID. Others will have domain knowledge that they'd like to find more data about, such as information about a "BGP neighbor". TDM can help with finding this data via Search.

TDM's Search is built with [ElasticSearch](https://www.elastic.co/products/elasticsearch), a powerful search and analytics engine. In Search, we compare the Human ID, Machine ID, and Description of each Data Path to the keywords in the query to determine the relevancy of each Data Path. Here are some guidelines to best use TDM's Search.

### Identifying Similar Data Paths
One of the reasons TDM exists is due to the desire to upgrade from SNMP to Model-Driven Telemetry. Most of the time, the data exposed by SNMP and Model-Driven Telemetry is not the same, despite representing some of the same information. There is commonly a list of OIDs already in use and a task to identify the same YANG XPaths for Model-Driven Telemetry as the SNMP OIDs. Here are some quick guidelines for this sort of task and how TDM can be used to help.

#### Break it down
Your Data Paths might be very specific, long, and unintuitive to the human eye. For instance...

```
ifHCInUcastPkts
Cisco-NX-OS-device:System/nd-items/inst-items/dom-items/Dom-list/if-items/If-list/vaddrstat-items/VaddrStat-list/vip-items/VaddrStatVip-list/raSent
Cisco-IOS-XR-pbr-vservice-ea-oper:service-function-chaining/nodes/node/process/service-function-forwarder/local/error/data/sf/processed-pkts
```

These Data Paths contain a lot of information! The key to best searching TDM is to break down the Data Paths in to something easily searchable by keyword.

```
# ifHCInUcastPkts
interface sent
interface ucast sent
...
# Cisco-NX-OS-device:System/nd-items/inst-items/dom-items/Dom-list/if-items/If-list/vaddrstat-items/VaddrStat-list/vip-items/VaddrStatVip-list/raSent
interface ra sent
...
# Cisco-IOS-XR-pbr-vservice-ea-oper:service-function-chaining/nodes/node/process/service-function-forwarder/local/error/data/sf/processed-pkts
service processed packets
...
```

It is important to acknowledge that sometimes there will not be an equivalent Data Path available, but Search should be able to at least help get started seeking the same data. We also attempt to normalize synonyms like `intf`, `interface`, etc. to assist different terminologies, but we don't know every synonym out there. If you'd like a synonym added into Search, please email or [open an issue](https://github.com/cisco-ie/tdm/issues).

#### Look at the Description
If keyword search hasn't helped, it is typically useful to get more information about the Data Path itself and what it represents. For instance, the earlier example of `Cisco-NX-OS-device:System/nd-items/inst-items/dom-items/Dom-list/if-items/If-list/vaddrstat-items/VaddrStat-list/vip-items/VaddrStatVip-list/raSent`, what is `raSent` describing? Using DataPath Direct, we can quickly navigate to this Data Path in TDM and examine its description. Based on the Description, this is "Router Advertisements sent"! This is much easier to search on, and we might have more success using the more qualified description. e.g. `interface router advertisement sent`.

This is also valuable for determining if two Data Paths which look similar by Human ID actually represent the same thing. It is easy to find this information by simply clicking on the interesting search result. It is always a good idea to evaluate the Description after identifying an interesting looking Data Path.

### Domain Specific Knowledge
TDM is well suited to helping to identify domain-specific knowledge related Data Paths. Domain specific knowledge is easily represented by keyword-like searches which is what TDM's Search functionality is most suited for. The above section is effectively an attempt to decompose the structure of the Data Paths into more generic ideas. `bgp neighbor messages sent` is more easily communicated than `Cisco-IOS-XR-ipv4-bgp-oper:bgp/instances/instance/instance-active/default-vrf/neighbors/neighbor/messages-sent`. Attempt to use generic, yet specific, terms and you'll likely have some success identifying information you're interested in.

## Retrieving Data
This section will go over how to retrieve data from Data Paths available in TDM in order to evaluate whether or not two Data Paths should be considered a match. The data returned from different Data Paths might be the same, and that is what we want to map in TDM. However, the data will not necessarily have the same structure of data returned. 
The data returned from different Data Paths, which we map as equivalent, do not necessarily require having the same structure of data returned, but they do require having the same data (as in values) returned. For instance, an OID does not return as XML, however YANG XPaths via NETCONF will, or even as JSON via gRPC. It requires looking at the data which is returned, and determining if that data, despite potential structural differences, is as close to a parity match as possible.


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

An example flow for retrieving XPath `openconfig-interfaces:interfaces/interface/state/name`:

1. Open your browser to the running instance of ANX.
2. Login to your NETCONF-enabled device via the ANX interface.
3. Await the YANG module parsing to finish.
4. Using "Search models" and "Search nodes", filter the data akin to how you would with TDM's search interface based on the structure of the XPath.
5. Select the corresponding node in the filtered tree.
6. Click "NETCONF console"
7. Click `<get>`
8. Click "Send Request"
9. Evaluate the returned data.

![ANX 4, 5, and 6](/doc/img/anx_1.png)

![ANX 7, 8, and 9](/doc/img/anx_2.png)

### MIB OID (SNMP)
SNMP MIB data is represented as a TDM Data Path via its OIDs. To explore OIDs, we will utilize the venerable [`snmpwalk`](http://net-snmp.sourceforge.net/tutorial/tutorial-5/commands/snmpwalk.html). `snmpwalk` has its nuances, but we will try to get its basic usage down. OIDs are a little bit strange in the sense that the OIDs defined by MIBs are not necessarily the total definition of what is available. OIDs can be variable past what's visibile purely from the MIB definition. `snmpwalk` traverses all of the values of the specified OID, and returns their values.

After an OID Data Path has been identified, a simple `snmpwalk -v 2c -c public <host> <oid>` will return all of the OID data.

## Evaluating Similar Data
There is not a lot of concrete advice on this topic other than using common sense and looking hard at the data returned from the above section. The data may come out in a different format, but if it is consistent in value then it is worth a match in TDM to assist all those that would look for an equivalent Data Path in the future. If you are able to determine a relevant Data Path, which returns the same data, then you have likely found a worthwhile match for TDM.

## Final Note
Once we've identified similar Data Paths, we have a responsibility to verify that these Data Paths return equivalent data before mapping them in TDM. Leading others down a rabbit hole of incorrect information is irresponsible and rather infuriating. Ensuring that the data in TDM is high-quality and trustworthy is a requirement for its success as a platform for finding this kind of information. If incorrect data or mappings are identified, flag them for explanation or removal.
