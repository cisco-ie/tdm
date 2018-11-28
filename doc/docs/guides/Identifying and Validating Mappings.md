# Identifying and Validating Mappings
Identifying and validating the mappings between Data Paths can be the most frustrating part of using and contributing to TDM. Unfortunately this process is not always easy nor are there tools to do it automatically. This document will walk through the usage of TDM and relevant tooling to identify relevant Data Paths, and how to validate whether Data Paths which appear similar may be considered enough of a match to map in TDM.

[[toc]]

## Identifying Relevant Data
"Identifying Relevant Data" may have different meaning to different people. Some will have existing data they would like to find equivalents for, like finding the NETCONF/YANG XPath equivalent of the SNMP OID `ifName`. Others will have domain knowledge that they would like to find more data about, such as information about a "BGP neighbor".

TDM can aid in finding this data via Search. TDM's Search is built with [ElasticSearch](https://www.elastic.co/products/elasticsearch), a powerful search and analytics engine. In Search, we compare the Human ID, Machine ID, and Description of each Data Path to the keywords in the query to determine the relevancy of each Data Path.

### Identifying Similar Data Paths
One of the reasons TDM exists is due to the desire to upgrade from SNMP to Model-Driven Telemetry. Most of the time, the data exposed by SNMP and Model-Driven Telemetry is not the same despite representing some of the same information. Most existing monitoring infrastructure already has the SNMP OIDs being monitored, and the requirement moving forward is to find the equivalent YANG XPaths for Model-Driven Telemetry. The following are some quick guidelines for how to use your existing data to find your new desired data with the help of TDM's Search.

#### Break it down
Your Data Paths might be very specific, long, and unintuitive to the human eye. For instance...

```
ifHCInUcastPkts
Cisco-NX-OS-device:System/nd-items/inst-items/dom-items/Dom-list/if-items/If-list/vaddrstat-items/VaddrStat-list/vip-items/VaddrStatVip-list/raSent
Cisco-IOS-XR-pbr-vservice-ea-oper:service-function-chaining/nodes/node/process/service-function-forwarder/local/error/data/sf/processed-pkts
```

These Data Paths contain a lot of information! The key to best searching TDM is to break down the Data Paths, whatever they might be, in to something easily searchable by keyword or idea.

```
# ifHCInUcastPkts
interface in unicast
if in ucast
...
# Cisco-NX-OS-device:System/nd-items/inst-items/dom-items/Dom-list/if-items/If-list/vaddrstat-items/VaddrStat-list/vip-items/VaddrStatVip-list/raSent
interface ra sent
...
# Cisco-IOS-XR-pbr-vservice-ea-oper:service-function-chaining/nodes/node/process/service-function-forwarder/local/error/data/sf/processed-pkts
service processed packets
...
```

For instance, breaking down the OID `ifHCInUcastPkts` to `interface in unicast` and using TDM's Search yields results like:
```
ietf-interfaces:interfaces-state/interface/statistics/in-unicast-pkts
openconfig-interfaces:interfaces/interface/state/counters/in-unicast-pkts
```
These YANG XPaths seem similar based on terminology, and are high potentials as Data Paths which might return equivalent information.

It is important to acknowledge that sometimes there will not be an equivalent Data Path available, but Search should be able to at least help get started seeking the same data. We also attempt to normalize synonyms like `intf`, `interface`, etc. to assist different terminologies. We don't know every synonym out there, so if you'd like a synonym added into Search, please email or [open an issue](https://github.com/cisco-ie/tdm/issues).

#### Look at the Description
If keyword search hasn't helped it is typically useful to get more information about the Data Path itself and what it represents. For instance, in the earlier example of `Cisco-NX-OS-device:System/nd-items/inst-items/dom-items/Dom-list/if-items/If-list/vaddrstat-items/VaddrStat-list/vip-items/VaddrStatVip-list/raSent`, what is `raSent` describing? Using DataPath Direct, we can quickly navigate to this Data Path in TDM and examine its description. Based on the description, this is "Router Advertisements sent"! This is much easier to search on, and we might have more success using the more qualified description. e.g. `interface router advertisement sent`.

This is also valuable for determining if two Data Paths which look similar by Human ID actually represent the same thing. It is easy to find this information by simply clicking on the interesting search result. It is always a good idea to evaluate the Description after identifying an interesting looking Data Path.

### Domain Specific Knowledge
TDM is well suited to helping identify domain-specific, knowledge-related Data Paths. Domain specific knowledge is easily represented by keyword-like searches which is what TDM's Search functionality is most useful for. The above "Break it down" section is effectively an attempt to decompose the structure of the Data Paths into more generic ideas. `bgp neighbor messages sent` is more easily communicated than `Cisco-IOS-XR-ipv4-bgp-oper:bgp/instances/instance/instance-active/default-vrf/neighbors/neighbor/messages-sent`. Attempt to use generic, yet specific, terms and you will likely have some success identifying information you are interested in.

## Retrieving Data
This section will go over how to retrieve data from Data Paths available in TDM in order to evaluate whether or not two Data Paths should be considered a match. The data returned from different Data Paths might be the same, and that is what we want to map in TDM. *However*, the data returned may not necessarily have the same structure or format. For example, JSON vs. XML or `HundredGigE0_0_0_0` vs. `HundredGigE0/0/0/0`.
While the structure or format may be different, the information being expressed must be the same. It requires looking at the data which is returned and determining if that data, despite potential presentation differences, expresses the same information.


### YANG XPath
YANG module data is represented as a TDM Data Path via its XPaths. To explore YANG XPaths, we will utilize the very useful [Advanced NETCONF Explorer](https://github.com/cisco-ie/anx) which presents an intuitive GUI interface via the web browser for exploring an online device's YANG modules.

#### Installation
ANX needs to be deployed on a server which is able to reach a NETCONF-enabled online device. Actual installation of ANX is out of the scope of this document, but a quick overview using Docker:

```bash
# If necessary...
ssh <host>
# Download ANX
git clone https://github.com/cisco-ie/anx.git
# If git is not available...
wget https://github.com/cisco-ie/anx/archive/master.tar.gz && tar -xzf master.tar.gz && rm master.tar.gz && mv anx-master anx
# Build & run ANX
cd anx
docker build -t cisco-ie/anx .
docker run --name anx -d -p 9269:8080 cisco-ie/anx
# Open browser to <host>:9269
```

#### Usage
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
SNMP MIB data is represented as a TDM Data Path via its OIDs. To explore OIDs, we will utilize the venerable [`net-snmp`](http://www.net-snmp.org/docs/man/) tools, specifically [`snmpwalk`](http://net-snmp.sourceforge.net/tutorial/tutorial-5/commands/snmpwalk.html). `snmpwalk` has its nuances, but we will try to get its basic usage down. OIDs are a little bit strange in the sense that the OIDs defined by MIBs are not necessarily the total definition of what is available. OIDs can be variable past what is visible purely from the MIB definition. `snmpwalk` traverses all of the values of the specified OID, and returns their values.

After an OID Data Path has been identified, a simple `snmpwalk -v 2c -c public <host> <oid>` will return all of the OID data.

#### Installation
SNMP tooling as an ecosystem is somewhat complicated to correctly install. This section will detail how to install the Cisco MIBs for usage with `net-snmp`.

Fortunately, `net-snmp` itself is very easy to install. It is effectively a standard package in the Unix-like ecosystem. For example, on Debian/Ubuntu, simply issue `apt install snmp`.

Unfortunately, `net-snmp` does not always come with the latest standard MIBs by default. On Debian/Ubuntu we can use `apt install snmp-mibs-downloader` to download several industry standard MIBs. For other distributions, you will have to do some searching and validation that your MIBs are the latest.

To use Cisco's MIBs, we first need to acquire them. Cisco has a mirror of SNMP-related information at [ftp://ftp.cisco.com/](ftp://ftp.cisco.com/). We will very specifically download the v2 MIBs located at [ftp://ftp.cisco.com/pub/mibs/v2/](ftp://ftp.cisco.com/pub/mibs/v2/) - if you don't know what this means then you will likely be okay with just this set. An example for Debian/Ubuntu, `wget --mirror --no-host-directories --cut-dirs=3 --directory-prefix=/usr/share/snmp/mibs/ --wait=1 ftp://ftp.cisco.com/pub/mibs/v2/`. This may take some time.


#### Example
An example setup for retrieving OID `ifName`:

`snmpwalk -Oaf -v 2c -c public <hostname> ifName 2>/dev/null`  
```
.iso.org.dod.internet.mgmt.mib-2.ifMIB.ifMIBObjects.ifXTable.ifXEntry.ifName.1 = STRING: Gi0/0
.iso.org.dod.internet.mgmt.mib-2.ifMIB.ifMIBObjects.ifXTable.ifXEntry.ifName.2 = STRING: Nu0
.iso.org.dod.internet.mgmt.mib-2.ifMIB.ifMIBObjects.ifXTable.ifXEntry.ifName.3 = STRING: VLAN-1
...
```

## Evaluating Similar Data
There is not a lot of concrete advice on this topic other than using common sense and looking hard at the data returned from the above sections. The data may come out in a different format, but if it is consistent in value then it is worth a match in TDM to assist all those that would look for an equivalent Data Path in the future. If you are able to determine a relevant Data Path, which returns the same data, then you have likely found a worthwhile match for TDM.

Let's correlate our data from the last two examples, XPath `openconfig-interfaces:interfaces/interface/state/name` and OID `ifName`.

### `openconfig-interfaces:interfaces/interface/state/name`
Retrieved via ANX.

```xml
<data xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces xmlns="http://openconfig.net/yang/interfaces">
   <interface>
    <name>Loopback0</name>
    <state>
     <name>Loopback0</name>
    </state>
   </interface>
   <interface>
    <name>HundredGigE0/0/0/0</name>
    <state>
     <name>HundredGigE0/0/0/0</name>
    </state>
   </interface>
   <interface>
    <name>HundredGigE0/0/0/1</name>
    <state>
     <name>HundredGigE0/0/0/1</name>
    </state>
   </interface>
   ...
  </interfaces>
 </data>
```

### `ifName`
`snmpwalk -Oa -v 2c -c public <hostname> ifName 2>/dev/null`

```
...
IF-MIB::ifName.41 = STRING: Loopback0
IF-MIB::ifName.42 = STRING: HundredGigE0/0/0/0
IF-MIB::ifName.43 = STRING: HundredGigE0/0/0/35
IF-MIB::ifName.44 = STRING: HundredGigE0/0/0/34
...
```

### Conclusion
We can see that, despite the structure of information being different, the values are indeed effectively the same. It's worth stating that `ifName` had more information including many optics, but we can safely say the information is so similar that we should consider these equivalent Data Paths and add that mapping within TDM. Another example of reasonably similar data would be if one returned the values in format `HundredGigE0_0_0_0` vs. `HundredGigE0/0/0/0` - this is effectively the same information despite its formatting being different. If it is expressing the same thing, it is worth mapping (with annotation) in TDM for other's usage.

## Final Note
Once we've identified similar Data Paths, we have a responsibility to verify that these Data Paths return equivalent data before mapping them in TDM. Leading others down a rabbit hole of incorrect information is irresponsible and rather infuriating. Ensuring that the data in TDM is high-quality and trustworthy is a requirement for its success as a platform for finding this kind of information. If incorrect data or mappings are identified, flag them for explanation or removal.
