
# Experiment
Perform various types of traceroutes. The available traceroute implementations are:

* The default traceroute that is distributed by the debian repositories

  ```
  root@Monroe000db94007b0:~# traceroute --version
  Modern traceroute for Linux, version 2.0.20, Nov  8 2014
  Copyright (c) 2008  Dmitry Butskoy,   License: GPL v2 or any later
  ```

* A modified version of paris-traceroute (included as a binary in the container). The modifications ensure compatibility with the MONROE infrastructure. [The original unmodified code can be found here.](https://code.google.com/p/paris-traceroute/source/checkout) [The modified code used at the MONROE project can be found here.](https://github.com/FoivosMichelinakis/paris-traceroute-monroe-project)

## How to use
* In the case of simple traceroute just call the command making sure that the interface flag is set to one of the mobile interfaces. 
  ```
  traceroute -i op0 <TARGET> &> <txtFile> 
  ```
* In the case of paris-traceroute some preliminary steps are necessary before we can begin the traceroute.
  * Create, at the root directory of the container, a file called `sourceInterface.txt` that contains the target interface. 

    ```
    echo op0 > sourceInterface.txt
    ```
  * Run the python script `getInterfaceIP.py`, providing as a parameter the interface we want to use. This will create the file `sourceIP.txt` at the root directory of the container, with the internal IP of the interface.
  
    ```
    python getInterfaceIP.py op0
    ```
  * Run the `paris-traceroute` command, by calling the binary file included in the container. It can either run without parameters to perform a "simple" traceroute (similar to the output of the ordinary traceroute command), or with the flags `-n -a exh`, in order to perform an exhaustive traceroute. Exhaustive traceroutes provide a more detailed and accurate paths between the host (MONROE node) and the target server. It is able to detect among others, the presence of load balancers, which create multiple paths between the host and the target.
    ```
    <pathToBinary>/paris-traceroute -n -a exh <TARGET> &> <txtFile>
    ```
   * Parse the txt files and provide JSON files that will be added to the database. In this container, the python script `trace.py` does so. An example invocation of this script would be:
      ```
      python trace.py --targetDomainName <TARGET> \
      --fileToParse <txtFile> \
      --productionTestingSwitch production \
      --JsonTracetouteSwitch traceroute \
      --tracerouteMode paris_traceroute_exhaustive \
      --InterfaceName op0
      ```
    * Copy the JSON files to the `/monroe/results/` directory so that they can be added to the database. In order to avoid conflicts with the exporter script that we do not control, we have to make the copy in 2 steps
      ```
      cp <JSONFile> /monroe/results/<JSONFile>.tmp
      mv /monroe/results/<JSONFile>.tmp /monroe/results/<JSONFile>
      ```
  ## Notes
  It is possible to run multiple instances of `traceroute` in parallel, without any problem. `paris-traceroute` though should be run sequentially and preferably when the node is generating little traffic in general. This is because it uses packet capture to detect the replies from the intermediate nodes and background traffic might interfere with this process.
