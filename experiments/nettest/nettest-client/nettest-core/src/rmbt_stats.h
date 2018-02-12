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

#ifndef SRC_RMBT_STATS_H_
#define SRC_RMBT_STATS_H_

#include "rmbt_common.h"

#include <sys/socket.h>

#include "rmbt_json.h"

/*
 * We use our own version of tcp_info, as we might run on a kernel that is more recent
 * than the headers we are compiling against.
 * The "introduced in" comments refer to git commit ids of the linux kernel sources.
 * */
struct rmbt_tcp_info {
	uint8_t	tcpi_state;
	uint8_t	tcpi_ca_state;
	uint8_t	tcpi_retransmits;
	uint8_t	tcpi_probes;
	uint8_t	tcpi_backoff;
	uint8_t	tcpi_options;
	uint8_t	tcpi_snd_wscale : 4, tcpi_rcv_wscale : 4;
	/* next one introduced in eb8329e0a04db0061f714f033b4454326ba147f4 (4.9) */
	uint8_t	tcpi_delivery_rate_app_limited:1;

	uint32_t	tcpi_rto;
	uint32_t	tcpi_ato;
	uint32_t	tcpi_snd_mss;
	uint32_t	tcpi_rcv_mss;

	uint32_t	tcpi_unacked;
	uint32_t	tcpi_sacked;
	uint32_t	tcpi_lost;
	uint32_t	tcpi_retrans;
	uint32_t	tcpi_fackets;

	/* Times. */
	uint32_t	tcpi_last_data_sent;
	uint32_t	tcpi_last_ack_sent;
	uint32_t	tcpi_last_data_recv;
	uint32_t	tcpi_last_ack_recv;

	/* Metrics. */
	uint32_t	tcpi_pmtu;
	uint32_t	tcpi_rcv_ssthresh;
	uint32_t	tcpi_rtt;
	uint32_t	tcpi_rttvar;
	uint32_t	tcpi_snd_ssthresh;
	uint32_t	tcpi_snd_cwnd;
	uint32_t	tcpi_advmss;
	uint32_t	tcpi_reordering;

	uint32_t	tcpi_rcv_rtt;
	uint32_t	tcpi_rcv_space;

	uint32_t	tcpi_total_retrans;

	uint64_t	tcpi_pacing_rate;
	uint64_t	tcpi_max_pacing_rate;
	/* introduced in 0df48c26d8418c5c9fba63fac15b660d70ca2f1c (4.1) */
	uint64_t	tcpi_bytes_acked;
	/* introduced in bdd1f9edacb5f5835d1e6276571bbbe5b88ded48 (4.1) */
	uint64_t	tcpi_bytes_received;
	/* introduced in 2efd055c53c06b7e89c167c98069bab9afce7e59 (4.2) */
	uint32_t	tcpi_segs_out;
	uint32_t	tcpi_segs_in;

	/* introduced in cd9b266095f422267bddbec88f9098b48ea548fc (4.6) */
	uint32_t	tcpi_notsent_bytes;
	uint32_t	tcpi_min_rtt;
	/* introduced in a44d6eacdaf56f74fad699af7f4925a5f5ac0e7f (4.6) */
	uint32_t	tcpi_data_segs_in;
	uint32_t	tcpi_data_segs_out;

	/* introduced in eb8329e0a04db0061f714f033b4454326ba147f4 (4.9) */
	uint64_t	tcpi_delivery_rate;

	/* introduced in efd90174167530c67a54273fd5d8369c87f9bd32 (4.10) */
	uint64_t	tcpi_busy_time;
	uint64_t	tcpi_rwnd_limited;
	uint64_t	tcpi_sndbuf_limited;
};

/* macro to check if specified member was actually returned by getsockopt
 * (i.e. kernel supports it) */
#define	IS_IN_RMBT_TCP_INFO(len, m)	(offsetof(struct rmbt_tcp_info, m) + sizeof(((struct rmbt_tcp_info *)0)->m) <= len)
#define JSON_ADD_OBJ_TCP_INFO(len, obj, m)	if (IS_IN_RMBT_TCP_INFO(len, m)) { \
		rmbt_json_add_int64(obj, #m, (int64_t)i->m); }
#define JSON_ADD_OBJ_TCP_INFO_BITFIELD(len, obj, m, next_memb)	\
		if (offsetof(struct rmbt_tcp_info, next_memb) <= len) { \
			rmbt_json_add_int64(obj, #m, (int64_t)i->m); }

typedef struct {
	int_fast64_t ts;
	socklen_t tcp_info_length;
	struct rmbt_tcp_info tcp_info;
} TcpInfoEntry;

typedef struct {
	int sfd;
	TcpInfoEntry *tcp_infos;
	size_t tcp_infos_size;
	size_t tcp_infos_length;
} StatsThreadEntry;

typedef struct {
	struct timespec *ts_zero;
	StatsThreadEntry *entries;
	size_t length;
	int_fast32_t tcp_info_sample_rate_us;
} StatsThreadArg;

void get_uname(rmbt_json obj);

void stats_set_arg(StatsThreadArg *arg);
rmbt_json_array get_stats_as_json_array(StatsThreadArg* e);
void stats_thread_set_sfd(int_fast16_t tid, int sfd);
void *stats_thread_start(void *arg) __attribute__ ((noreturn));

#endif /* SRC_RMBT_STATS_H_ */
