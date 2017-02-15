
# Experiment
Perform periodically traceroutes to various targets. This experiment is meant to be run in the background and it is possible to run in parallel with experiments of other users. It uses the default traceroute binary distributed by the debian repositories.

Each traceroute produces a `txt` file which is then parsed by the `outputParser.py`, to provide a `JSON` file for this experiment. The `JSON` file is then imported to the MONROE database. 

## Flags

In order to reduce its duration there is the option to run the traceroutes in parallel. The number of parallel tracroute instances is dictated by the `maxNumberOfTotalTracerouteInstances` parameter.
It is possible to parallelize on a per interface basis (ie. `maxNumberOfTotalTracerouteInstances` per interface) or per the whole experiment (ie. `maxNumberOfTotalTracerouteInstances` total in the experiment instance spread among all the interfaces). This behavior is controlled by the `executionMode` parameter. The available options are: `serially`, `serialPerInterface` and `parallel`.

It is possible to also provide a flag for the protocol of the probes. (flag `protocol` with parameters `default`, `udp`, `tcp` and `icmp`)

## Additional options
The parameters of this experiment will be provided as "Additional options".
"Additional options" are passed to the experiment when it is scheduled at the [experiment
scheduling web interface.](https://www.monroe-system.eu/NewExperiment.html)

An example "Additional options" JSON string that can be used with this container is:
```
"interfaces": ["op0", "op1", "op2"], "targets": ["www.ntua.gr", "www.uc3m.es", "Google.com", "Facebook.com", "Youtube.com", "Baidu.com", "Yahoo.com", "Amazon.com", "Wikipedia.org", "audio-ec.spotify.com", "mme.whatsapp.net", "sync.liverail.com", "ds.serving-sys.com", "instagramstatic-a.akamaihd.net"], "maxNumberOfTotalTracerouteInstances": 5, "executionMode": "parallel"
```