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

#include "rmbt_stats.h"

#include <time.h>
#include <sys/types.h>
#include <sys/utsname.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/tcp.h>

#include "rmbt_helper.h"

#define RMBT_STATS_INCREMENT	512

static pthread_mutex_t stats_mtx = PTHREAD_MUTEX_INITIALIZER;
static StatsThreadArg *stats_arg = NULL;

 void get_uname(rmbt_json obj) {
	struct utsname n;
	if (uname(&n) < 0)
		return;
	rmbt_json_add_string(obj, "res_uname_sysname", n.sysname);
	rmbt_json_add_string(obj, "res_uname_nodename", n.nodename);
	rmbt_json_add_string(obj, "res_uname_release", n.release);
	rmbt_json_add_string(obj, "res_uname_version", n.version);
	rmbt_json_add_string(obj, "res_uname_machine", n.machine);
}

static void tcp_info_set_json(rmbt_json obj, struct rmbt_tcp_info *i, socklen_t i_len) {
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_state);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_ca_state);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_retransmits);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_probes);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_backoff);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_options);
	JSON_ADD_OBJ_TCP_INFO_BITFIELD(i_len, obj, tcpi_snd_wscale, tcpi_rto);
	JSON_ADD_OBJ_TCP_INFO_BITFIELD(i_len, obj, tcpi_rcv_wscale, tcpi_rto);

	/* tcpi_busy_time because tcpi_delivery_rate_app_limited was introduced with tcpi_delivery_rate */
	JSON_ADD_OBJ_TCP_INFO_BITFIELD(i_len, obj, tcpi_delivery_rate_app_limited, tcpi_busy_time);

	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_rto);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_ato);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_snd_mss);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_rcv_mss);

	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_unacked);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_sacked);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_lost);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_retrans);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_fackets);


	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_last_data_sent);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_last_ack_sent);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_last_data_recv);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_last_ack_recv);

	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_pmtu);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_rcv_ssthresh);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_rtt);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_rttvar);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_snd_ssthresh);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_snd_cwnd);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_advmss);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_reordering);

	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_rcv_rtt);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_rcv_space);

	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_total_retrans);

	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_pacing_rate);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_max_pacing_rate);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_bytes_acked);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_bytes_received);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_segs_out);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_segs_in);

	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_notsent_bytes);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_min_rtt);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_data_segs_in);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_data_segs_out);

	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_delivery_rate);

	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_busy_time);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_rwnd_limited);
	JSON_ADD_OBJ_TCP_INFO(i_len, obj, tcpi_sndbuf_limited);
}

static rmbt_json get_tcp_info_entry_as_json(TcpInfoEntry* e) {
	rmbt_json obj = rmbt_json_new();
	tcp_info_set_json(obj, &e->tcp_info, e->tcp_info_length);
	rmbt_json_add_int64(obj, "timestamp_ns", e->ts);
	return obj;
}

rmbt_json_array get_stats_as_json_array(StatsThreadArg* e) {
	rmbt_json_array arr = rmbt_json_new_array();
	for (size_t i = 0; i < e->length; i++) {
		StatsThreadEntry *ste = &e->entries[i];
		for (size_t j = 0; j < ste->tcp_infos_length; j++) {
			rmbt_json obj = get_tcp_info_entry_as_json(&ste->tcp_infos[j]);
			rmbt_json_add_int64(obj, "flow_id", (int64_t)i);
			rmbt_json_add_to_array(arr, obj);
		}
	}
	return arr;
}

//static rmbt_json read_tcp_info_json(int sfd) {
//	struct rmbt_tcp_info info = { 0 };
//	socklen_t info_len = sizeof(info);
//	if (getsockopt(sfd, IPPROTO_TCP, TCP_INFO, &info, &info_len) != 0)
//		return NULL;
//	return tcp_info_to_json(&info, info_len);
//}

//static void json_add_tcp_info(int sfd, rmbt_json array) {
//	json_object_array_add(array, read_tcp_info_json(sfd));
//}
//
//static void print_tcp_info(int sfd, FILE *f) {
//	fprintf(f, "%s\n", json_object_to_json_string_ext(read_tcp_info_json(sfd), JSON_C_TO_STRING_PRETTY));
//}

static void rmbt_add_tcp_info(StatsThreadEntry *e) {
	/* make sure there is enough space */
	if (e->tcp_infos_length >= e->tcp_infos_size) {
		e->tcp_infos_size += RMBT_STATS_INCREMENT;
		e->tcp_infos = realloc(e->tcp_infos, e->tcp_infos_size * sizeof(TcpInfoEntry));
		memset(&e->tcp_infos[e->tcp_infos_length], 0, (e->tcp_infos_size - e->tcp_infos_length) * sizeof(TcpInfoEntry));
	}
	e->tcp_infos[e->tcp_infos_length].ts = ts_diff(stats_arg->ts_zero);
	struct rmbt_tcp_info *info = &e->tcp_infos[e->tcp_infos_length].tcp_info;
	e->tcp_infos[e->tcp_infos_length].tcp_info_length = sizeof(struct rmbt_tcp_info);
	if (getsockopt(e->sfd, IPPROTO_TCP, TCP_INFO, info, &e->tcp_infos[e->tcp_infos_length].tcp_info_length) == 0)
		e->tcp_infos_length++;
}

void stats_thread_set_sfd(int_fast16_t tid, int sfd) {
	pthread_mutex_lock(&stats_mtx);
	if (stats_arg != NULL && tid < (int_fast16_t)stats_arg->length)
		stats_arg->entries[tid].sfd = sfd;
	pthread_mutex_unlock(&stats_mtx);
}

void stats_set_arg(StatsThreadArg *arg) {
	pthread_mutex_lock(&stats_mtx);
	stats_arg = arg;
	for (size_t i = 0; i < stats_arg->length; i++)
		stats_arg->entries[i].sfd = -1;
	pthread_mutex_unlock(&stats_mtx);
}

void *stats_thread_start(__attribute__((unused)) void *arg) {
	struct timespec sleep_time;
	sleep_time.tv_sec = stats_arg->tcp_info_sample_rate_us / 1000000;
	sleep_time.tv_nsec = stats_arg->tcp_info_sample_rate_us % 1000000 * 1000;
	while(true) { // thread will be canceled; clock_nanosleep is a cancellation point
		pthread_mutex_lock(&stats_mtx);
		for (size_t i = 0; i < stats_arg->length; i++) {
			int sfd = stats_arg->entries[i].sfd;
			if (sfd >= 0)
				rmbt_add_tcp_info(&stats_arg->entries[i]);
		}
		pthread_mutex_unlock(&stats_mtx);
		int r = clock_nanosleep(CLOCK_REALTIME, 0, &sleep_time, NULL);
		if (r != 0)
			pthread_exit(NULL);
	}
}
