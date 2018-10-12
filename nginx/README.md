# NGINX
This folder contains files which are related to the serving of different TDM components over public networks.

## NGINX
NGINX is a swiss army knife of functionality which we primarily use for reverse proxy capabilities in TDM. NGINX frontends all of our HTTP[S] requests into TDM services. Its primary role is to handle HTTPS into the system, enabling us to focus on raw development instead of internal component security. This, obviously, has various positive and negative qualities - but does exactly what is required right now. We also get centralization and logging of all access into the system.

* [nginx.conf](nginx.conf)  
Dev-oriented HTTP reverse-proxy configuration.
* [nginx.https.conf](nginx.https.conf)  
Production-oriented HTTPS reverse-proxy configuration.

For HTTPS to be enabled, `tdm.cisco.com.crt` and `tdm.cisco.com.key` must be generated and placed into this folder. A service like [LetsEncrypt](https://letsencrypt.org/) can be helpful in getting these certs, and then rename them appropriately (or change filenames in the NGINX configs).

## Goaccess
By using NGINX, we also solve another big question - usage details! [Goaccess](https://goaccess.io/) is a nifty tool which processes logs from components like NGINX and can produce nice HTML outputs and graphs. These are exposed via `/goaccess_<service>.html` from NGINX via some funky script usage and Docker volumes.

* [goaccess_dbms.conf](goaccess_dbms.conf)  
Goaccess configuration for processing ArangoDB access.
* [goaccess_web.conf](goaccess_web.conf)  
Goaccess configuration for processing TDM Web UI access.
* [goaccess_kibana.conf](goaccess_kibana.conf)  
Goaccess configuration for processing Kibana access for exploring Elasticsearch data.
