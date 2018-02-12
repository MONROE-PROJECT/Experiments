/*******************************************************************************
 * Copyright 2017 Leonhard Wimmer
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *  http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *******************************************************************************/

#ifndef SRC_RMBT_RESULT_H_
#define SRC_RMBT_RESULT_H_

#include <arpa/inet.h>
#include <stdbool.h>
#include <time.h>

#include "rmbt_json.h"

#define FOREACH_PHASE(PHASE) \
        PHASE(init)   \
        PHASE(pretest_dl)  \
        PHASE(rtt_tcp_payload)   \
        PHASE(dl)  \
		PHASE(pretest_ul)  \
		PHASE(ul)  \
		PHASE(end)

#define GENERATE_ENUM(ENUM) 	PH_##ENUM,
#define GENERATE_STRING(STRING) #STRING,

typedef enum {
	FOREACH_PHASE(GENERATE_ENUM)
} Phase;

typedef struct {
	const char *cipher;
	char *tcp_congestion;
	char *tls_debug;
	int_fast32_t chunksize;
	int_fast16_t port_local, port_server;
	char ip_local[INET6_ADDRSTRLEN];
	char ip_server[INET6_ADDRSTRLEN];
	char server_version[64];
	bool encrypt;
} ConnectionInfo;

typedef struct {
	int_fast64_t time_start_rel_ns, time_end_rel_ns;
	int_fast64_t rtt_server_ns, rtt_client_ns;
} RttTcpPayload;

typedef struct {
	int_fast16_t rtt_tcp_payload_num;
	RttTcpPayload *rtt_tcp_payloads;
} RttTcpPayloadResult;

typedef struct {
	char *id_test;
	char *error;
	RttTcpPayloadResult *rtt_tcp_payload_result;
	ConnectionInfo *connection_info;
	int_fast64_t dl_time_ns, dl_bytes;
	int_fast64_t ul_time_ns, ul_bytes;
	int_fast64_t rtt_tcp_payload_client_ns;
	int_fast64_t rtt_tcp_payload_server_ns;
	int_fast64_t total_bytes_dl, total_bytes_ul;
	time_t time_start_s;
	time_t time_end_s;
	double dl_throughput_kbps;
	double ul_throughput_kbps;
	int_fast16_t dl_num_flows, ul_num_flows;
	Phase last_phase;
} Result;

typedef struct {
	int_fast64_t bytes;
	int_fast64_t time_ns;
	int_fast64_t time_ns_end;
	int_fast64_t duration_server;
} DataPoint;

typedef struct {
	int_fast64_t time_start_rel_ns, time_end_rel_ns, duration_server_ns;
	int_fast32_t num_time_series;
	DataPoint *time_series;
} DirectionResult;

typedef struct {
	int_fast64_t flow_bytes_dl;
	int_fast64_t flow_bytes_ul;
	RttTcpPayloadResult rtt_tcp_payload;
	DirectionResult pretest_dl, dl, pretest_ul, ul;
	ConnectionInfo connection_info;
	Phase last_phase;
	char error[512];
} FlowResult;

rmbt_json_array rtt_tcp_payloads_to_json_array(RttTcpPayload *rtt_tcp_payloads, int_fast16_t rtt_tcp_payload_num);
void add_datapoint_to_array(rmbt_json array, DataPoint data_point);
rmbt_json directionresult_to_json_obj(DirectionResult *direction_result);

void calc_results(Result *result, FlowResult *flow_results, int_fast16_t num_flow_results);

rmbt_json collect_summary_results(Result *result);
rmbt_json collect_raw_results(Result *result, FlowResult *flow_results, int_fast16_t num_flow_results);
void do_free_flow_results(FlowResult *flow_results, int_fast16_t num_flow_results);

#endif /* SRC_RMBT_RESULT_H_ */
