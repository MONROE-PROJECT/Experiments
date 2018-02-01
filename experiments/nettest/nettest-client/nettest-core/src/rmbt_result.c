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

#include "rmbt_result.h"

#include <stdio.h>
#include <string.h>

#include "rmbt_config.h"
#include "rmbt_stats.h"

#define SUCCESS		"success"
#define FAIL		"fail_"

#define FREE_AND_SET_NULL(ptr) if (ptr != NULL) { free(ptr); ptr = NULL; }

static const char *PHASE_STRING[] = { FOREACH_PHASE(GENERATE_STRING) };

rmbt_json_array rtt_tcp_payloads_to_json_array(RttTcpPayload rtt_tcp_payloads[], int_fast16_t rtt_tcp_payload_num) {
	rmbt_json_array result = rmbt_json_new_array();
	for (int_fast16_t i = 0; i < rtt_tcp_payload_num; i++) {
		rmbt_json point = rmbt_json_new();
		rmbt_json_add_int64(point, "time_start_rel_ns", (*(rtt_tcp_payloads + i)).time_start_rel_ns);
		rmbt_json_add_int64(point, "rtt_server_ns", (int64_t) (*(rtt_tcp_payloads + i)).rtt_server_ns);
		rmbt_json_add_int64(point, "rtt_client_ns", (*(rtt_tcp_payloads + i)).rtt_client_ns);
		rmbt_json_add_int64(point, "time_end_rel_ns", (*(rtt_tcp_payloads + i)).time_end_rel_ns);
		rmbt_json_add_to_array(result, point);
	}
	return result;
}

static rmbt_json_array time_series_to_json_array(DataPoint data_points[], int_fast32_t num_data_points) {
	rmbt_json_array result = rmbt_json_new_array();
	for (int_fast32_t i = 0; i < num_data_points; i++) {
		DataPoint data_point = *(data_points + i);
		rmbt_json point = rmbt_json_new();
		if (data_point.time_ns_end == 0) {
			rmbt_json_add_int64(point, "t", data_point.time_ns);
			rmbt_json_add_int64(point, "b", data_point.bytes);
		} else {
			rmbt_json_add_int64(point, "t_begin", data_point.time_ns);
			rmbt_json_add_int64(point, "b", data_point.bytes);
			rmbt_json_add_int64(point, "t_end", data_point.time_ns_end);
		}
		if (data_point.duration_server != 0)
			rmbt_json_add_int64(point, "d_server", data_point.duration_server);
		rmbt_json_add_to_array(result, point);
	}
	return result;
}

rmbt_json directionresult_to_json_obj(DirectionResult *direction_result) {
	rmbt_json result_json = rmbt_json_new();
	rmbt_json_add_int64(result_json, "time_start_rel_ns", direction_result->time_start_rel_ns);
	rmbt_json_add_int64(result_json, "time_end_rel_ns", direction_result->time_end_rel_ns);
	if (direction_result->duration_server_ns != 0)
		rmbt_json_add_int64(result_json, "duration_server_ns", direction_result->duration_server_ns);
	rmbt_json_add_array(result_json, "time_series", time_series_to_json_array(direction_result->time_series, direction_result->num_time_series));
	return result_json;
}

static void calc_direction_results(double *result, int_fast64_t *result_time, int_fast64_t *result_bytes, int_fast16_t *num_flows,
		DirectionResult *direction_results[], int_fast16_t num_direction_results) {

	int_fast64_t target_time = INT_FAST64_MAX;
	int_fast16_t target_time_idx = -1;

	*num_flows = 0;

	for (int_fast16_t i = 0; i < num_direction_results; i++) {
		DirectionResult *direction_result = direction_results[i];
		if (direction_result->time_series != NULL) {
			(*num_flows)++;
			int_fast64_t last_time = direction_result->time_series[direction_result->num_time_series - 1].time_ns;
			if (target_time_idx == -1 || last_time < target_time) {
				target_time_idx = i;
				target_time = last_time;
			}
		}
	}

	int_fast64_t total_bytes = 0;
	/* could be optimized by using binary search */
	for (int_fast16_t i = 0; i < num_direction_results; i++) {
		DirectionResult *direction_result = direction_results[i];
		int_fast32_t target_idx_a = -1, target_idx_b = -1;
		for (int_fast32_t j = direction_result->num_time_series - 1; j >= 0; j--) {
			if (direction_result->time_series[j].time_ns <= target_time) {
				target_idx_a = target_idx_b = j;
				if (direction_result->time_series[j].time_ns != target_time && j != direction_result->num_time_series - 1)
					target_idx_b++;
				break;
			}
		}
		if (target_idx_a == target_idx_b && target_idx_a != -1)
			total_bytes += direction_result->time_series[target_idx_a].bytes;
		else {
			int_fast64_t bytes_a = target_idx_a == -1 ? 0 : direction_result->time_series[target_idx_a].bytes;
			int_fast64_t bytes_b = target_idx_b == -1 ? 0 : direction_result->time_series[target_idx_b].bytes;
			int_fast64_t time_a = target_idx_a == -1 ? 0 : direction_result->time_series[target_idx_a].time_ns;
			int_fast64_t time_b = target_idx_b == -1 ? 0 : direction_result->time_series[target_idx_b].time_ns;

			total_bytes += bytes_a;
			if (time_b - time_a != 0)
				total_bytes += (bytes_b - bytes_a) * (target_time - time_a) / (time_b - time_a);
		}
	}
	*result = (double) total_bytes / (double) target_time * 8e6;
	*result_time = target_time;
	*result_bytes = total_bytes;
}

static int cmp_int_fast64_p(const void *p1, const void *p2) {
	int_fast64_t diff = *(const int_fast64_t *) p2 - *(const int_fast64_t *) p1;
	if (diff > 0)
		return 1;
	if (diff < 0)
		return -1;
	return 0;
}

void calc_results(Result *result, FlowResult *flow_results, int_fast16_t num_flow_results) {

	/* rtt_tcp_payload */
	if (result->rtt_tcp_payload_result == NULL) {
		for (int_fast16_t i = 0; i < num_flow_results; i++) {
			FlowResult *flow_result = flow_results + i;
			if (flow_result->rtt_tcp_payload.rtt_tcp_payloads != NULL) {
				result->rtt_tcp_payload_result = &flow_result->rtt_tcp_payload;
				break;
			}
		}
	}
	if (result->rtt_tcp_payload_result != NULL) {
		int_fast16_t rtt_tcp_payload_num = result->rtt_tcp_payload_result->rtt_tcp_payload_num;
		int_fast64_t rtt_tcp_payloads_client[rtt_tcp_payload_num];
		int_fast64_t rtt_tcp_payloads_server[rtt_tcp_payload_num];
		for (int_fast16_t i = 0; i < rtt_tcp_payload_num; i++) {
			rtt_tcp_payloads_client[i] = result->rtt_tcp_payload_result->rtt_tcp_payloads->rtt_client_ns;
			rtt_tcp_payloads_server[i] = result->rtt_tcp_payload_result->rtt_tcp_payloads->rtt_server_ns;
		}

		qsort(rtt_tcp_payloads_client, (size_t) rtt_tcp_payload_num, sizeof(int_fast64_t), cmp_int_fast64_p);
		qsort(rtt_tcp_payloads_server, (size_t) rtt_tcp_payload_num, sizeof(int_fast64_t), cmp_int_fast64_p);

		/*
		 rtt_tcp_payload_result->rtt_client_shortest_ns = rtt_tcp_payloads_client[0];
		 rtt_tcp_payload_result->rtt_server_shortest_ns = rtt_tcp_payload_server[0];
		 */

		if (rtt_tcp_payload_num == 1) {
			result->rtt_tcp_payload_client_ns = rtt_tcp_payloads_client[0];
			result->rtt_tcp_payload_server_ns = rtt_tcp_payloads_server[0];
		} else if (rtt_tcp_payload_num > 1) {
			int_fast16_t idx_median = rtt_tcp_payload_num / 2;
			if (rtt_tcp_payload_num % 2 == 0) {
				result->rtt_tcp_payload_client_ns = (rtt_tcp_payloads_client[idx_median] + rtt_tcp_payloads_client[idx_median + 1]) / 2;
				result->rtt_tcp_payload_server_ns = (rtt_tcp_payloads_server[idx_median] + rtt_tcp_payloads_server[idx_median + 1]) / 2;
			} else {
				result->rtt_tcp_payload_client_ns = rtt_tcp_payloads_client[idx_median];
				result->rtt_tcp_payload_server_ns = rtt_tcp_payloads_server[idx_median];
			}
		}
	}

	/* dl / ul */
	DirectionResult *direction_result_dl[num_flow_results];
	DirectionResult *direction_result_ul[num_flow_results];
	result->total_bytes_dl = result->total_bytes_ul = 0;
	for (int_fast16_t i = 0; i < num_flow_results; i++) {
		FlowResult *flow_result = flow_results + i;

		if (result->connection_info == NULL)
			result->connection_info = &flow_result->connection_info;

		direction_result_dl[i] = &flow_result->dl;
		direction_result_ul[i] = &flow_result->ul;

		result->total_bytes_dl += flow_result->flow_bytes_dl;
		result->total_bytes_ul += flow_result->flow_bytes_ul;
	}
	calc_direction_results(&result->dl_throughput_kbps, &result->dl_time_ns, &result->dl_bytes, &result->dl_num_flows, direction_result_dl, num_flow_results);
	calc_direction_results(&result->ul_throughput_kbps, &result->ul_time_ns, &result->ul_bytes, &result->ul_num_flows, direction_result_ul, num_flow_results);

	/* status */
	for (int_fast16_t i = 0; i < num_flow_results; i++) {
		FlowResult *flow_result = flow_results + i;
		if (flow_result->error[0] != '\0') {
			result->error = flow_result->error;
			result->last_phase = flow_result->last_phase;
			break;
		}
	}
}

static void add_common_results(Result *result, rmbt_json result_json) {

	if (result->id_test != NULL)
		rmbt_json_add_string(result_json, "res_id_test", result->id_test);
	rmbt_json_add_int64(result_json, "res_time_start_s", result->time_start_s);
	rmbt_json_add_int64(result_json, "res_time_end_s", result->time_end_s);
	if (result->error == NULL) {
		rmbt_json_add_string(result_json, "res_status", SUCCESS);
		rmbt_json_add_null(result_json, "res_status_msg");
	} else {
		char status[sizeof(result->error) + strlen(FAIL)];
		snprintf(status, sizeof(status), "%s%s", FAIL, PHASE_STRING[result->last_phase]);
		rmbt_json_add_string(result_json, "res_status", status);
		rmbt_json_add_string(result_json, "res_status_msg", result->error);
	}
	rmbt_json_add_string(result_json, "res_version_client", RMBT_VERSION);

	if (result->connection_info != NULL) {
		if (strlen(result->connection_info->server_version) > 0)
			rmbt_json_add_string(result_json, "res_version_server", result->connection_info->server_version);
		if (strlen(result->connection_info->ip_server) > 0)
			rmbt_json_add_string(result_json, "res_server_ip", result->connection_info->ip_server);
		if (result->connection_info->port_server != 0)
			rmbt_json_add_int64(result_json, "res_server_port", result->connection_info->port_server);
		rmbt_json_add_bool(result_json, "res_encrypt", result->connection_info->encrypt);
		if (result->connection_info->cipher != NULL)
			rmbt_json_add_string(result_json, "res_cipher", result->connection_info->cipher);
		if (result->connection_info->chunksize > 0)
			rmbt_json_add_int64(result_json, "res_chunksize", result->connection_info->chunksize);
		if (result->connection_info->tcp_congestion != NULL)
			rmbt_json_add_string(result_json, "res_tcp_congestion", result->connection_info->tcp_congestion);
	}

	if (result->total_bytes_dl > 0)
		rmbt_json_add_int64(result_json, "res_total_bytes_dl", result->total_bytes_dl);
	if (result->total_bytes_ul > 0)
		rmbt_json_add_int64(result_json, "res_total_bytes_ul", result->total_bytes_ul);

	get_uname(result_json);
}

rmbt_json collect_summary_results(Result *result) {
	rmbt_json result_json = rmbt_json_new();

	add_common_results(result, result_json);

	if (result->rtt_tcp_payload_result != NULL && result->rtt_tcp_payload_result->rtt_tcp_payload_num > 0)
		rmbt_json_add_int64(result_json, "res_rtt_tcp_payload_num", result->rtt_tcp_payload_result->rtt_tcp_payload_num);
	if (result->rtt_tcp_payload_client_ns > 0)
		rmbt_json_add_int64(result_json, "res_rtt_tcp_payload_client_ns", result->rtt_tcp_payload_client_ns);
	if (result->rtt_tcp_payload_server_ns > 0)
		rmbt_json_add_int64(result_json, "res_rtt_tcp_payload_server_ns", result->rtt_tcp_payload_server_ns);

	if (result->dl_bytes > 0) {
		rmbt_json_add_int64(result_json, "res_dl_num_flows", result->dl_num_flows);
		rmbt_json_add_int64(result_json, "res_dl_time_ns", result->dl_time_ns);
		rmbt_json_add_int64(result_json, "res_dl_bytes", result->dl_bytes);
		rmbt_json_add_double(result_json, "res_dl_throughput_kbps", result->dl_throughput_kbps);
	}
	if (result->ul_bytes > 0) {
		rmbt_json_add_int64(result_json, "res_ul_num_flows", result->ul_num_flows);
		rmbt_json_add_int64(result_json, "res_ul_time_ns", result->ul_time_ns);
		rmbt_json_add_int64(result_json, "res_ul_bytes", result->ul_bytes);
		rmbt_json_add_double(result_json, "res_ul_throughput_kbps", result->ul_throughput_kbps);
	}

	return result_json;
}

static void add_json_array_if_nonempty(rmbt_json object, const char *key, rmbt_json_array json_array) {
	if (rmbt_json_array_length(json_array) > 0)
		rmbt_json_add_array(object, key, json_array);
	else
		rmbt_json_free_array(json_array);
}

rmbt_json collect_raw_results(Result *result, FlowResult *flow_results, int_fast16_t num_flow_results) {
	rmbt_json result_json = rmbt_json_new();

	add_common_results(result, result_json);

	rmbt_json json_details = rmbt_json_new();

	if (result->rtt_tcp_payload_result != NULL) {
		rmbt_json json_rtt_tcp_payload = rmbt_json_new();
		rmbt_json_add_array(json_rtt_tcp_payload, "values",
				rtt_tcp_payloads_to_json_array(result->rtt_tcp_payload_result->rtt_tcp_payloads, result->rtt_tcp_payload_result->rtt_tcp_payload_num));
		rmbt_json_add_object(json_details, "rtt_tcp_payload", json_rtt_tcp_payload);
	}

	rmbt_json_array json_init = rmbt_json_new_array();
	rmbt_json_array json_pretest_dl = rmbt_json_new_array();
	rmbt_json_array json_dl = rmbt_json_new_array();
	rmbt_json_array json_pretest_ul = rmbt_json_new_array();
	rmbt_json_array json_ul = rmbt_json_new_array();

	for (int_fast16_t i = 0; i < num_flow_results; i++) {
		FlowResult *flow_result = flow_results + i;

		rmbt_json init_obj = rmbt_json_new();

		if (flow_result->connection_info.port_local != 0)
			rmbt_json_add_int64(init_obj, "client_port", flow_result->connection_info.port_local);
		if (flow_result->connection_info.cipher != NULL)
			rmbt_json_add_string(init_obj, "cipher", flow_result->connection_info.cipher);
		if (flow_result->connection_info.tls_debug != NULL)
			rmbt_json_add_string(init_obj, "tls_debug", flow_result->connection_info.tls_debug);
		rmbt_json_add_to_array(json_init, init_obj);

		if (flow_result->pretest_dl.time_series != NULL)
			rmbt_json_add_to_array(json_pretest_dl, directionresult_to_json_obj(&flow_result->pretest_dl));
		if (flow_result->dl.time_series != NULL)
			rmbt_json_add_to_array(json_dl, directionresult_to_json_obj(&flow_result->dl));
		if (flow_result->pretest_ul.time_series != NULL)
			rmbt_json_add_to_array(json_pretest_ul, directionresult_to_json_obj(&flow_result->pretest_ul));
		if (flow_result->ul.time_series != NULL)
			rmbt_json_add_to_array(json_ul, directionresult_to_json_obj(&flow_result->ul));
	}

	add_json_array_if_nonempty(json_details, "init", json_init);
	add_json_array_if_nonempty(json_details, "pretest_dl", json_pretest_dl);
	add_json_array_if_nonempty(json_details, "dl", json_dl);
	add_json_array_if_nonempty(json_details, "pretest_ul", json_pretest_ul);
	add_json_array_if_nonempty(json_details, "ul", json_ul);

	rmbt_json_add_object(result_json, "res_details", json_details);

	return result_json;
}

void do_free_flow_results(FlowResult *flow_results, int_fast16_t num_flow_results) {
	for (int_fast16_t i = 0; i < num_flow_results; i++) {
		FlowResult *flow_result = flow_results + i;

		FREE_AND_SET_NULL(flow_result->connection_info.tcp_congestion);
		FREE_AND_SET_NULL(flow_result->connection_info.tls_debug);
		FREE_AND_SET_NULL(flow_result->pretest_dl.time_series);
		FREE_AND_SET_NULL(flow_result->dl.time_series);
		FREE_AND_SET_NULL(flow_result->pretest_ul.time_series);
		FREE_AND_SET_NULL(flow_result->ul.time_series);
		FREE_AND_SET_NULL(flow_result->rtt_tcp_payload.rtt_tcp_payloads);
	}
}

