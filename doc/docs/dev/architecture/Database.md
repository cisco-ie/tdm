# Database
TDM's parsed source-of-truth resides in ArangoDB. ArangoDB is a powerful graph database which enables NoSQL-like storage models and relational queries.

[[toc]]

## Schema
TDM has a relatively simple schema. ArangoDB helps express it simply as well.

![Database Schema Image](/doc/img/tdm_schema.png)

### Entities (Collections)

#### DataPath
The most basic representation of a "path" to data which can be transformed and formatted for control protocols to retrieve the data.

* **machine_id**  
The path/identifier which is qualified, unique, and most used by definition in the machine. The machine_id must be unique in the system.
* human_id  
The path/identifier which is colloquially used by humans to communicate the data path.
* description  
The description provided for the data to be returned.
* is_leaf  
Whether the data path returns a leaf-like value such as an integer. Indicates a pointer to data which is unable to be further traversed.
* is_variable  
Whether the data path is unable to be directly indexed.
* is_configurable  
Whether the data path represents something which is able to be configured. Effectively, a "write" property.
* verified  
Whether the data path has been verified and should absolutely be trusted. If it is not verified, there is a potential for it to be in error.

#### DataModel
The data model which provides the definition/schema of available data which we may derive DataPaths to.

* content  
The unparsed content of the data model.
* **name**  
The name or filename of the data model.
* **parsed_checksum**  
The checksum of the data paths parsed from the data model. This is not currently implemented.
* **revision**  
The revision of the data model.

#### DataModelLanguage
The known and defined language of data modeling which a DataModel is written in.

* **name**
* description

#### OS
The operating system which DataModels may apply to.

* **name**  
e.g. IOS XR
* description

#### Release
The OS Release which DataModels may apply to.

* **name**  
e.g. 6.5.1
* description

#### ControlProtocol
The known and defined protocol which is capable of transforming or utilizing DataModels or DataPaths to retrieve data.

* **name**  
e.g. NETCONF
* description

#### TransportProtocol
The known and defined protocol which a ControlProtocol may operate over.

* **name**  
e.g. HTTP
* description

#### Encoding
The encoding of the data which a DataPath is communicated via a ControlProtocol and over the TransportProtocol.

* **name**  
e.g. JSON
* description
  
#### DataType
The defined data type that a data point in a DataPath is defined to return.

* **name**
* description
* is_primitive

#### Device
A physical device which may have data models and should have corresponding data paths.

* **name**
* description

#### Calculation
A defined calculation which may be used to indicate that a DataPath is calculated via other DataPaths. This does not attempt to maintain order of operations. Order of operations must be maintained in the equation/description and will not automatically apply.

* name  
An apt naming for the calculation, for human consumption.
* description
* equation
* author

### Relationships (Edges)

#### DeviceHasDataPath
Indicates that it has been validated that a Device does have a specified DataPath available.

* os
* release

#### DeviceHasDataModel
Indicates that it has been validated that a Device does have a specified DataModel.

* os
* release

#### OSHasRelease
OS ownership of a specific Release name.

#### ReleaseHasDataModel
Indication that, theoretically, a specific Release should have a DataModel.

#### ReleaseRevision
Indicates that a Release is a revision of another Release.

#### DataPathFromDataModel
Indicates that a specific DataPath is derivative of a certain DataModel.

* parse_timestamp

#### OfDataModelLanguage
Indicates that a DataModel is written in the linked DataModelLanguage.

#### HasControlProtocol
Indicates that a DataModelLanguage may be manipulated by the linked ControlProtocol.

#### HasEncoding
Indicates that a ControlProtocol supports the linked Encoding.

#### HasTransportProtocol
Indicates that a ControlProtocol supports the linked TransportProtocol.

#### DataPathMatch
Indicates that the linked DataPaths are equivalent.

* timestamp  
Time of match indication.
* author  
Submitter of match.
* validated  
Whether a match is trustworthy.
* weight  
-1..+inf. -1 indicates incongruent.
* annotation  
Human consumable annotation of match.
* needs_human  
Indicates incompatible for machine consumption.

#### DataPathParent
Indicates that a DataPath is a parent of another DataPath.

#### DataPathChild
Indicates that a DataPath is a child of another DataPath.

#### OfDataType
Indicates that a DataPath is of data type DataType.

* parse_timestamp

#### DataModelChild
Demonstrates revision child relationships in DataModels.

#### DataModelParent
Demonstrates revision parent relationships in DataModels.

#### DataModelDerivedFrom
Indicates that this DataModel is not a standalone DataModel and is actually converted or generated from the existing, linked DataModel.

#### InCalculation
Indicates that a DataPath is within the specified Calculation.

#### CalculationResult
Indicates that a DataPath is a result of the specified Calculation.

#### DataModelLanguageHasDataType
Indicates that a DataType is defined within a DataModelLanguage.

## Example AQL
Queries that are usable in the ArangoDB UI. Outputs are all examples. HIGHLY recommend usage of `LIMIT` statements at reasonable points of the query. None of these queries are guaranteed to be "the best." :)

## Retrievals

### Filtered DataPath Leaves

#### Query
AQL Fulltext searches utilize characters like `-`, `+`, and `.` in the mini-language to indicate "logical not", etc. Commas indicate terminology to filter on. This query will first return all results with all elements of the filter string, and then ensure that the filter string itself is within the results. This ensures that our exact filter string is present and prevents arbitrary ordering issues.

```
LET filter_string = "Cisco-IOS-XE"
FOR dp IN FULLTEXT(DataPath, "human_id", SUBSTITUTE(filter_string, "-", ","))
  FILTER CONTAINS(dp.human_id, filter_string)
  LIMIT 10
  RETURN dp.human_id
```

If you want to search for general terminology, which isn't DataPath specific, then this too will work.

```
LET filter_string = "bgp"
FOR dp IN FULLTEXT(DataPath, "human_id", filter_string)
  LIMIT 10
  RETURN dp.human_id
```

#### Output
```json
[
  "Cisco-IOS-XE-bgp-oper:bgp-state/neighbors/neighbor/afi-safi",
  "Cisco-IOS-XE-bgp-oper:bgp-state/neighbors/neighbor/vrf-name",
  "Cisco-IOS-XE-bgp-oper:bgp-state/neighbors/neighbor/neighbor-id",
  "Cisco-IOS-XE-bgp-oper:bgp-state/neighbors/neighbor/description",
  "Cisco-IOS-XE-bgp-oper:bgp-state/neighbors/neighbor/bgp-version",
  "Cisco-IOS-XE-bgp-oper:bgp-state/neighbors/neighbor/link",
  "Cisco-IOS-XE-bgp-oper:bgp-state/neighbors/neighbor/up-time",
  "Cisco-IOS-XE-bgp-oper:bgp-state/neighbors/neighbor/last-write",
  "Cisco-IOS-XE-bgp-oper:bgp-state/neighbors/neighbor/last-read",
  "Cisco-IOS-XE-bgp-oper:bgp-state/neighbors/neighbor/installed-prefixes"
]
```

### OS and Releases

#### Query
```
RETURN MERGE(
  FOR os IN OS
    RETURN {
      [ os.name ]: FLATTEN(
        FOR os_release IN OSHasRelease
          FILTER os_release._from == os._id
          RETURN (
            FOR release in Release
              FILTER os_release._to == release._id
              RETURN release.name
          )
      )
    }
)
```

#### Output
```json
[
  {
    "IOS XE": [
      "16.3.1",
      "16.7.1",
      "16.6.2",
      "16.6.1",
      "16.5.1",
      "16.4.1",
      "16.3.2"
    ]
  }
]
```

### OS/Release Owned DataModels

#### Query
```
FOR os IN OS
  LIMIT 1
  RETURN {
    [ os.name ]: MERGE(
      FOR os_release IN OSHasRelease
        FILTER os_release._from == os._id
        LIMIT 2
        RETURN MERGE(
          FOR release IN Release
            FILTER os_release._to == release._id
            RETURN {
              [ release.name ]: FLATTEN(
                FOR release_model IN ReleaseHasDataModel
                  FILTER release_model._from == release._id
                  LIMIT 5
                  RETURN (
                    FOR dm IN DataModel
                      FILTER release_model._to == dm._id
                      RETURN CONCAT_SEPARATOR("@", dm.name, dm.revision)
                  )
              )
            }
        )
    )
  }
```

#### Output
```json
[
  {
    "IOS XE": {
      "16.3.1": [],
      "16.7.1": [
        "openconfig-network-instance-types@2016-12-15",
        "tailf-confd-monitoring@2013-06-14",
        "Cisco-IOS-XE-diffserv-target-oper@2017-02-09",
        "cisco-xe-ietf-event-notifications-deviation@2017-08-22",
        "cisco-xe-ietf-yang-push-deviation@2017-08-22"
      ]
    }
  }
]
```

### OS/Release Owned DataModels and DataPaths

#### Query
```
RETURN MERGE(
  FOR os IN OS
    LIMIT 1
    RETURN {
      [ os.name ]: MERGE(FLATTEN(
        FOR os_release IN OSHasRelease
          FILTER os_release._from == os._id
          LIMIT 2
          RETURN MERGE(
            FOR release IN Release
              FILTER os_release._to == release._id
              RETURN {
                [ release.name ]: MERGE(FLATTEN(
                  FOR release_model IN ReleaseHasDataModel
                    FILTER release_model._from == release._id
                    LIMIT 5
                    RETURN MERGE(
                      FOR dm IN DataModel
                        FILTER release_model._to == dm._id
                        RETURN {
                          [ CONCAT_SEPARATOR("@", dm.name, dm.revision) ]: FLATTEN(
                            FOR model_dp IN DataPathFromDataModel
                              FILTER model_dp._from == dm._id
                              LIMIT 2
                              RETURN FLATTEN(
                                FOR dp IN DataPath
                                  FILTER model_dp._to == dp._id
                                  RETURN dp.human_id
                              )
                          )
                        }
                    )
                ))
              }
          )
      ))
    }
)
```

#### Output
```json
[
  {
    "IOS XE": {
      "16.3.1": {},
      "16.7.1": {
        "Cisco-IOS-XE-diffserv-target-oper@2017-02-09": [
          "Cisco-IOS-XE-diffserv-target-oper:diffserv-interfaces-state",
          "Cisco-IOS-XE-diffserv-target-oper:diffserv-interfaces-state/diffserv-interface/diffserv-target-entry/diffserv-target-classifier-statistics/queuing-statistics/wred-stats/early-drop-bytes"
        ],
        "cisco-xe-ietf-event-notifications-deviation@2017-08-22": [],
        "cisco-xe-ietf-yang-push-deviation@2017-08-22": [],
        "openconfig-network-instance-types@2016-12-15": [],
        "tailf-confd-monitoring@2013-06-14": [
          "tailf-confd-monitoring:confd-state",
          "tailf-confd-monitoring:confd-state/internal/cdb/client/subscription/error"
        ]
      }
    }
  }
]
```

### OS/Release DataPaths

#### Query
```
RETURN MERGE(
  FOR os IN OS
    LIMIT 2
    RETURN {
      [ os.name ]: MERGE(FLATTEN(
        FOR os_release IN OSHasRelease
        FILTER os_release._from == os._id
        LIMIT 2
        RETURN (
          FOR release IN Release
          FILTER os_release._to == release._id
          RETURN {
            [ release.name ]: FLATTEN(
              FOR release_model IN ReleaseHasDataModel
              FILTER release_model._from == release._id
              LIMIT 2
              RETURN FLATTEN(
                FOR dm IN DataModel
                FILTER release_model._to == dm._id
                RETURN FLATTEN(
                  FOR model_dp IN DataPathFromDataModel
                  FILTER model_dp._from == dm._id
                  LIMIT 2
                  RETURN FLATTEN(
                    FOR dp IN DataPath
                    FILTER model_dp._to == dp._id
                    RETURN dp.human_id
                  )
                )
              )
            )
          }
        )
      ))
    }
)
```

#### Output
```json
[
  {
    "IOS XE": {
      "16.3.1": [],
      "16.7.1": [
        "tailf-confd-monitoring:confd-state",
        "tailf-confd-monitoring:confd-state/internal/cdb/client/subscription/error"
      ]
    },
    "IOS XR": {
      "5.3.0": [],
      "6.3.1": [
        "Cisco-IOS-XR-config-mda-cfg:apply-group",
        "Cisco-IOS-XR-config-mda-cfg:preconfigured-nodes/preconfigured-node/clock-interface/clocks/clock/port"
      ]
    }
  }
]
```

### Common OS/Release DataPaths
Intersects IOS XR 6.3.1 and IOS XE 16.7.1 data paths.

#### Query
```
LET xe_dps = FLATTEN(
  FOR os IN OS
  FILTER os.name == "IOS XE"
    RETURN FLATTEN(
      FOR os_release IN OSHasRelease
        FILTER os_release._from == os._id
        RETURN FLATTEN(
          FOR release IN Release
            FILTER os_release._to == release._id && release.name == "16.7.1"
            RETURN FLATTEN(
              FOR release_model IN ReleaseHasDataModel
                FILTER release_model._from == release._id
                RETURN FLATTEN(
                  FOR dm IN DataModel
                    FILTER release_model._to == dm._id
                    FOR model_dp IN DataPathFromDataModel
                      FILTER model_dp._from == dm._id
                      RETURN FLATTEN(
                        FOR dp IN DataPath
                          FILTER model_dp._to == dp._id
                          RETURN dp.human_id
                      )
                  )
              )
        )
    )
)
LET xr_dps = FLATTEN(
  FOR os IN OS
  FILTER os.name == "IOS XR"
    RETURN FLATTEN(
      FOR os_release IN OSHasRelease
        FILTER os_release._from == os._id
        RETURN FLATTEN(
          FOR release IN Release
            FILTER os_release._to == release._id && release.name == "6.3.1"
            RETURN FLATTEN(
              FOR release_model IN ReleaseHasDataModel
                FILTER release_model._from == release._id
                RETURN FLATTEN(
                  FOR dm IN DataModel
                    FILTER release_model._to == dm._id
                    FOR model_dp IN DataPathFromDataModel
                      FILTER model_dp._from == dm._id
                      RETURN FLATTEN(
                        FOR dp IN DataPath
                          FILTER model_dp._to == dp._id
                          RETURN dp.human_id
                      )
                  )
              )
        )
    )
)
RETURN INTERSECTION(xe_dps, xr_dps)
```

#### Output
```json
[
  [
    "ietf-interfaces:interfaces-state/interface/statistics/in-pkts",
    "ietf-interfaces:interfaces-state/interface/statistics/out-pkts",
    "ietf-interfaces:interfaces-state/interface/routing-instance",
    "ietf-interfaces:interfaces-state/interface/pseudowire/neighbor-ip-address",
    "ietf-interfaces:interfaces-state/interface/pseudowire/vc-id",
    "ietf-interfaces:interfaces-state/interface/ethernet/duplex",
    ...
  ]
]
```

### Retrieve Matching DataPaths

#### Query
```
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
```

#### Output
```json
[
  {
    "_key": "8759",
    "human_id": "ifHCOutMulticastPkts",
    "machine_id": "1.3.6.1.2.1.31.1.1.1.12",
    "matches": [
      {
        "_key": "4931200",
        "human_id": "Cisco-IOS-XR-infra-statsd-oper:infra-statistics/interfaces/interface/latest/generic-counters",
        "machine_id": "Cisco-IOS-XR-infra-statsd-oper/infra-statsd-oper:infra-statistics/infra-statsd-oper:interfaces/infra-statsd-oper:interface/infra-statsd-oper:latest/infra-statsd-oper:generic-counters"
      },
      {
        "_key": "4931336",
        "human_id": "Cisco-IOS-XR-infra-statsd-oper:infra-statistics/interfaces/interface/latest/generic-counters/multicast-packets-sent",
        "machine_id": "Cisco-IOS-XR-infra-statsd-oper/infra-statsd-oper:infra-statistics/infra-statsd-oper:interfaces/infra-statsd-oper:interface/infra-statsd-oper:latest/infra-statsd-oper:generic-counters/infra-statsd-oper:multicast-packets-sent"
      },
      {
        "_key": "4931336",
        "human_id": "Cisco-IOS-XR-infra-statsd-oper:infra-statistics/interfaces/interface/latest/generic-counters/multicast-packets-sent",
        "machine_id": "Cisco-IOS-XR-infra-statsd-oper/infra-statsd-oper:infra-statistics/infra-statsd-oper:interfaces/infra-statsd-oper:interface/infra-statsd-oper:latest/infra-statsd-oper:generic-counters/infra-statsd-oper:multicast-packets-sent"
      }
    ]
  }
]
```

### Retrieve DataPath Calculations

#### Query
```
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
```

#### Output
```json
[
  {
    "_key": "8719",
    "human_id": "ifHCInUcastPkts",
    "machine_id": "1.3.6.1.2.1.31.1.1.1.7",
    "calculations": {
      "as_result": [
        {
          "_key": "13113704",
          "name": "Inbound Unicast Packets YANG <-> SNMP",
          "result": {
            "_key": "8719",
            "human_id": "ifHCInUcastPkts",
            "machine_id": "1.3.6.1.2.1.31.1.1.1.7"
          },
          "factors": [
            {
              "_key": "4931216",
              "human_id": "Cisco-IOS-XR-infra-statsd-oper:infra-statistics/interfaces/interface/latest/generic-counters/packets-received",
              "machine_id": "Cisco-IOS-XR-infra-statsd-oper/infra-statsd-oper:infra-statistics/infra-statsd-oper:interfaces/infra-statsd-oper:interface/infra-statsd-oper:latest/infra-statsd-oper:generic-counters/infra-statsd-oper:packets-received"
            },
            {
              "_key": "4931296",
              "human_id": "Cisco-IOS-XR-infra-statsd-oper:infra-statistics/interfaces/interface/latest/generic-counters/multicast-packets-received",
              "machine_id": "Cisco-IOS-XR-infra-statsd-oper/infra-statsd-oper:infra-statistics/infra-statsd-oper:interfaces/infra-statsd-oper:interface/infra-statsd-oper:latest/infra-statsd-oper:generic-counters/infra-statsd-oper:multicast-packets-received"
            },
            {
              "_key": "4931316",
              "human_id": "Cisco-IOS-XR-infra-statsd-oper:infra-statistics/interfaces/interface/latest/generic-counters/broadcast-packets-received",
              "machine_id": "Cisco-IOS-XR-infra-statsd-oper/infra-statsd-oper:infra-statistics/infra-statsd-oper:interfaces/infra-statsd-oper:interface/infra-statsd-oper:latest/infra-statsd-oper:generic-counters/infra-statsd-oper:broadcast-packets-received"
            }
          ]
        }
      ],
      "as_factor": []
    }
  }
]
```

### Retrieve Unmatched DataPaths

#### Query
```
LET given_dps = @given_dps
LET matched_dps = FLATTEN(
  FOR given_dp IN given_dps
    RETURN FLATTEN(
      FOR dp IN DataPath
        FILTER dp.human_id == given_dp
        RETURN (
          FOR dp_eq IN DataPathMatch
            FILTER dp_eq._from == dp._id || dp_eq._to == dp._id
            RETURN dp.human_id
        )
    )
)
LET calculated_dps = FLATTEN(
  FOR given_dp IN given_dps
    RETURN FLATTEN(
      FOR dp IN DataPath
        FILTER dp.human_id == given_dp
        RETURN FLATTEN(
         FOR calc_result IN CalculationResult
          FILTER calc_result._to == dp._id
          RETURN dp.human_id
        )
    )
)
RETURN MINUS(given_dps, linked_dps, calculated_dps)
```

#### Output
```json
[
  "asdf"
]
```

### Retrieve Collection Counts

#### Query
```
LET given_collections = @given_collections
RETURN MERGE(
  FOR collection IN given_collections
    RETURN {
      [ collection ]: COLLECTION_COUNT(collection)
    }
)
```

#### Output
```json
[
  {
    "DataModel": 1760,
    "Release": 31,
    "DataPath": 554322
  }
]
```

### Retrieve OS/Releases linked to a DataPath

#### Query
```
WITH OS, Release, DataModel, DataPath
FOR os IN OS
  FOR v, e, p
    IN 3..3
    OUTBOUND os._id
    OSHasRelease, ReleaseHasDataModel, DataPathFromDataModel
    FILTER p.vertices[3]._key == @dp_key
    RETURN {
        'os': p.vertices[0].name,
        'release': p.vertices[1].name
    }
```

#### Output
```json
[
  {
    "os": "IOS XE",
    "release": "16.7.1"
  },
  {
    "os": "IOS XE",
    "release": "16.6.2"
  },
  {
    "os": "IOS XE",
    "release": "16.6.1"
  },
  {
    "os": "IOS XR",
    "release": "6.3.1"
  },
  {
    "os": "IOS XR",
    "release": "6.2.2"
  },
  {
    "os": "NX-OS",
    "release": "7.0(3)I7(3)"
  },
  {
    "os": "NX-OS",
    "release": "7.0(3)I7(2)"
  },
  {
    "os": "NX-OS",
    "release": "7.0(3)I7(1)"
  },
  {
    "os": "NX-OS",
    "release": "7.0(3)I6(2)"
  },
  {
    "os": "NX-OS",
    "release": "7.0(3)I6(1)"
  },
  {
    "os": "NX-OS",
    "release": "7.0(3)I5(2)"
  },
  {
    "os": "NX-OS",
    "release": "7.0(3)I5(1)"
  }
]
```

### Retrieve per-DataModelLanguage DataPaths with Matches

#### Query
```
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
```

#### Output
```json
[
  {
    "CLI": [],
    "DME": [],
    "SMI": [
      {
        "_key": "334439",
        "human_id": "bgpLocalAs"
      },
      {
        "_key": "334495",
        "human_id": "bgpPeerLocalAddr"
      }
    ],
    "YANG": [
      {
        "_key": "7586776",
        "human_id": "Cisco-IOS-XR-bundlemgr-oper:bundle-information/bundle/bundle-members/bundle-member/bundle-member-item/counters/lacpd-us-received"
      }
    ]
  }
]
```

### Search DataPaths per OS/Release/DataModelLanguage/DataModel
This is a pretty hefty query if not used appropriately. Do not recommend searching just "bgp". This can use up to 32 GB of RAM, but has a relatively constant time-to-return window of 1-45 seconds compared to previous iterations of the query whose upper limits were indeterminate (never finished).

#### Query
```
filter_os_releases = {"IOS XR": ["6.3.1"]}
filter_dmls = ["YANG"]
filter_str = "openconfig interface"
start_index = 0
max_return_count = 3
```

```
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
                                                        FILTER dp.is_configurable == False
                                                        FILTER dp.is_leaf == True
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
```

#### Output
```json
[
  {
    "IOS XR": {
      "6.3.1": {
        "YANG": {
          "openconfig-interfaces": [
            {
              "_key": "937777",
              "human_id": "openconfig-interfaces:interfaces/interface/aggregation/state/lag-speed"
            },
            {
              "_key": "937737",
              "human_id": "openconfig-interfaces:interfaces/interface/aggregation/state/lag-type"
            },
            {
              "_key": "937797",
              "human_id": "openconfig-interfaces:interfaces/interface/aggregation/state/member"
            }
          ],
          "openconfig-lacp": [
            {
              "_key": "3971823",
              "human_id": "openconfig-lacp:lacp/interfaces/interface/members/member/interface"
            },
            ...
          ]
        }
      }
    }
  }
]
```
