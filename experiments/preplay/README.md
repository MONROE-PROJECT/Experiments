# pReplay

pReplay replays the dependency graph.
It starts from the first activity which is loading the root html.
Then according to the graph, it it encounters a network activity, it makes a request for the corresponding url, or if it encounters a computation activity, it waits for a specific amount of time (mentioned in the graph).
Once a particular activity is finshed it checks  whether it should trigger dependent activities based on whether all activities that a dependent activity depends on are finished.
pReplay keeps walking through the dependency graph this way until all activities in the dependency graph have been visited.

## usage
```
./pReplay interface_name server testfile [http|https|http2|phttpget] [max-connections] [cookie-size]
```
* `interface_name`: source interface for outgoing traffic 
* `server` : DNS name or IP address
* `testfile` : relative path to test file in json format
* `protocol` :
    * `http` : http 1.1
    * `https` : http 1.1 with SSL
    * `http2` : http 2
* `max-connections` : maximum amount of concurrent connections
* `cookie-size` : size of cookie - works with http1 only


## info
tested with  Linux
