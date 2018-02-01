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

#ifndef SRC_RMBT_FLOW_H_
#define SRC_RMBT_FLOW_H_

#include "rmbt_common.h"
#include "rmbt_result.h"

#include <stdatomic.h>

typedef struct {
	char *bind_ip, *server_host, *server_port, *cipherlist, *secret, *token, *test_id, *file_summary, *file_flows, *file_stats;
	int_fast16_t dl_num_flows, ul_num_flows, dl_duration_s, ul_duration_s, rtt_tcp_payload_num, dl_pretest_duration_s, ul_pretest_duration_s, dl_wait_time_s,
			ul_wait_time_s;
	int_fast32_t tcp_info_sample_rate_us;
	int timeout_ms;
	bool encrypt, encrypt_debug;
} TestConfig;

typedef struct {
	atomic_bool global_abort;
	pthread_mutex_t mutex;
	pthread_cond_t cond;
	int_fast16_t total;
	int_fast16_t entered;
	int_fast16_t left;
} RmbtBarrier;

#define RMBT_BARRIER_INITIALIZER { false, PTHREAD_MUTEX_INITIALIZER, PTHREAD_COND_INITIALIZER, 0, 0, 0 }

typedef struct {
	TestConfig *cfg;
	pthread_t thread;
	int_fast16_t thread_num;
	int_fast16_t thread_count;
	struct timespec *ts_zero;
	RmbtBarrier *barrier;
	FlowResult *flow_result;
	bool do_log;
	bool do_rtt_tcp_payload;
	bool do_uplink;
	bool do_downlink;
} ThreadArg;

#define RETURN_IF_NOK(x) if (!(x)) return false;

void *run_test_thread_start(void *arg);

#endif /* SRC_RMBT_FLOW_H_ */
