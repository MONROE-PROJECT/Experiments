# Experiment rmbt
Runs rmbt client (throughput measurement).

The experiment will run the rmbt client.

For the rmbt client source code see https://github.com/lwimmer/rmbt-client.

The minimum required configuration is (via /monroe/config):
```
{
  "cnf_server_host": "<hostname or ip of the RMBT server to use>",
  "cnf_server_port": <port of the RMBT server to use>
}
```

The default values are (can be overridden by a /monroe/config):
```
{
  # The following value are specific to the monroe platform
  "guid": "no.guid.in.config.file",               # Should be overridden by scheduler
  "zmqport": "tcp://172.17.0.1:5556",
  "modem_metadata_topic": "MONROE.META.DEVICE.MODEM",
  "dataversion": 2,
  "dataid": "MONROE.EXP.RMBT",
  "nodeid": "fake.nodeid",
  "meta_grace": 120,                              # Grace period to wait for interface metadata
  "exp_grace": 300,                               # Grace period before killing experiment
  "ifup_interval_check": 3,                       # Interval to check if interface is up
  "time_between_experiments": 0,
  "verbosity": 2,                                 # 0 = "Mute", 1=error, 2=Information, 3=verbose
  "resultdir": "/monroe/results/",
  "modeminterfacename": "InternalInterface",
  "save_metadata_topic": "MONROE.META",
  "save_metadata_resultdir": None,                # set to a dir to enable saving of metadata
  "add_modem_metadata_to_result": False,          # set to True to add one captured modem metadata to rmbt result
  "traceroute_resultdir": "/monroe/results/",     # set to a dir to enable traceroute before rmbt
  "disabled_interfaces": ["lo",
                          "metadata",
                          "eth0",
                          "wlan0"
  ],                      # Interfaces to NOT run the experiment on
  "interfaces_without_metadata": ["eth0",
                                  "wlan0"],       # Manual metadata on these IF

  # These values are specic for this experiment; defaults:
  #"cnf_server_host": "",               # REQUIRED PARAMETER; Host/IP to connect to
  #"cnf_server_port": ,                 # REQUIRED PARAMETER; Port to connect to
  "cnf_secret": "",                     # RMBT server secret (can be empty if server does not check tokens)
  "cnf_encrypt": False,                 # use TLS if True
  "cnf_dl_num_flows": 5,                # number of TCP flows to use for downlink
  "cnf_ul_num_flows": 5,                # number of TCP flows to use for uplink
  "cnf_dl_duration_s": 10,              # nominal duration for downlink measurement
  "cnf_ul_duration_s": 10,              # nominal duration for uplink measurement
  "cnf_dl_pretest_duration_s": 1,       # minimum/nominal duration for downlink pretest
  "cnf_ul_pretest_duration_s": 1,       # minimum/nominal duration for uplink pretest
  "cnf_rtt_tcp_payload_num": 11,        # number of tcp rtt measurements
  "cnf_dl_wait_time_s": 20,             # time to wait for downlink measurement to finish after nominal time
  "cnf_ul_wait_time_s": 20,             # time to wait for uplink measurement to finish after nominal time
  "cnf_timeout_s": 30,                  # TCP timeout
  "cnf_tcp_info_sample_rate_us": 10000, # = 10ms; how often to collect tcp_info
  "multi_config_randomize": False,      # Randomize the muliple runs by "multi_config", has no effect without "multi_config" (see below)
  "tar_additional_results": True        # tar the flows, stats and traceroute output
}
```

Other supported settings are:
```
{
  # Set "multi_config" to do multiple runs with varying configuration
  # on every interface.
  # All elements of each sublist are combined with the elements of every other
  # sublist. The resulting configurations are then combined with the main
  # configuration and add or override the entries of the main config.
  # The traceroute is only done once per server/interface combination.
  # The following example does 12 runs on every interface.
  # It does 1,3,4,5,7,9 number of flows against server A and B:
  "multi_config": [
    [
      { "cnf_dl_num_flows": 1, "cnf_ul_num_flows": 1 },
      { "cnf_dl_num_flows": 3, "cnf_ul_num_flows": 3 },
      { "cnf_dl_num_flows": 4, "cnf_ul_num_flows": 4 },
      { "cnf_dl_num_flows": 5, "cnf_ul_num_flows": 5 },
      { "cnf_dl_num_flows": 7, "cnf_ul_num_flows": 7 },
      { "cnf_dl_num_flows": 9, "cnf_ul_num_flows": 9 },
    ],
    [ {"cnf_server_host": "A"}, {"cnf_server_host": "B"}]
  ],
  "enabled_interfaces": ["op0"],  # Interfaces to run the experiment on
  "require_modem_metadata": {"DeviceMode": 4}, # only run if in LTE (5) or UMTS (4)
  "cnf_encrypt_debug": false,     # Add TLS debug info to flows file
  "cnf_cipherlist": null,         # OpenSSL Cipherlist
  "cnf_token": null,              # RMBT token (mutually exclusive with cnf_secret)
  "cnf_file_summary": "{time}_{id_test}_summary.json",
  "cnf_file_flows": "{time}_{id_test}_flows.json",
  "cnf_file_stats": "{time}_{id_test}_stats.json"
}
```

## Requirements

These directories and files must exist and be read/writable by the user/process
running the container.
/opt/monroe/config
"resultdir" (from /opt/monroe/config see defaults above)

## Sample output
The experiment will produce a single line JSON object similar to this (pretty printed and added comments here for readability)
```
{
  "Guid": "313.123213.123123.123123", # exp_config["guid"]
  "Timestamp": 23123.1212,            # time.time()
  "Iccid": 2332323,                   # meta_info["ICCID"]
  "Operator": "Operator",             # meta_info["Operator"]
  "NodeId" : "9",                     # exp_config["nodeid"]
  "DataVersion": 2,
  "ErrorCode": 0                      # rmbt command error code.
  "DataId": "MONROE.EXP.RMBT",
  "SequenceNumber": 1,
  "res_id_test": "e6147214-86f4-47cb-8e7c-623c9b3305c4",
  "res_time_start_s": 1496394081,
  "res_time_end_s": 1496394110,
  "res_status": "success",
  "res_status_msg": null,
  "res_version_client": "v1.0-10-geb3d4eacf",
  "res_version_server": "RMBTv0.3",
  "res_server_ip": "10.10.10.10",
  "res_server_port": 10080,
  "res_encrypt": false,
  "res_chunksize": 4096,
  "res_tcp_congestion": "cubic",
  "res_total_bytes_dl": 14578965,
  "res_total_bytes_ul": 24409282,
  "res_uname_sysname": "Linux",
  "res_uname_nodename": "a37d1bc45001",
  "res_uname_release": "4.9.0-0.bpo.3-amd64",
  "res_uname_version": "#1 SMP Debian 4.9.25-1~bpo8+1 (2017-05-19)",
  "res_uname_machine": "x86_64",
  "res_rtt_tcp_payload_num": 11,
  "res_rtt_tcp_payload_client_ns": 61124894,
  "res_rtt_tcp_payload_server_ns": 79970608,
  "res_dl_num_flows": 5,
  "res_dl_time_ns": 10527728474,
  "res_dl_bytes": 13820479,
  "res_dl_throughput_kbps": 10502.154598,
  "res_ul_num_flows": 5,
  "res_ul_time_ns": 10451588171,
  "res_ul_bytes": 23589484,
  "res_ul_throughput_kbps": 18056.190974
}
```
