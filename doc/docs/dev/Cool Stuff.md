# Cool Stuff
This document is simply to try and express cool stuff which we could possibly do.

## Automatic Data Normalization
This is the holy grail, and likely unfortunately out of scope at the moment ([although Google might have a working implementation based on this presentation](https://www.youtube.com/watch?v=McNm_WfQTHw)). If we can determine how to go from one data modeling language to another data modeling language generically, we can provide an API to normalize different data in to one clean presentation. For instance, let us assume we have data points `1`, `2`, and `3` and they are all considered "equivalent" and mapped as `1 <-> 2 <-> 3`. Given this knowledge, and some implementation, we could specify any of these data points to be our desired data form and any time we provide any of the other data points they can be normalized to our specified schema. i.e. `2` is the desired data point to generically perform analysis against. Submitting data points from `1` and `3` will be automatically translated in to the schema of `2` and thus we no longer need to join our analysis against 3 separate data points and instead against 1 as the data is already being normalized by TDM via knowing the mappings.

## ML/Stats-based Data Mappings
Using different stats methods we can easily attempt to map between data points based on the data identifiers themselves as well as the data values. For instance, applying Levenshtein distance to all the different DataPaths is a quick and easy one (but likely ineffective) to ascertain some level of similarity. We will have to consider some ensemble methods to make the DataPath comparison reasonable. Another compelling option is to query live devices for the data exposed in TDM and compare actual values or trends in values to attempt to correlate individual data points.

## Data Validation/QA
With an offline view of data availability, we can attempt to verify the truthiness of what is advertised and determine gaps in implementation. We can also verify mapping integrity based on returned values from a live device.
