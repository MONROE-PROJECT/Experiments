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

#ifndef SRC_RMBT_CONFIG_H_
#define SRC_RMBT_CONFIG_H_

#ifndef RMBT_VERSION
# if defined(GIT_VERSION)
#  define RMBT_VERSION GIT_VERSION
# elif defined(VERSION)
#  define RMBT_VERSION VERSION
# else
#  define RMBT_VERSION "unknown"
# endif
#endif

#define DEFAULT_CONFIG "{ \n\
  \"cnf_encrypt\": false, \n\
  \"cnf_encrypt_debug\": false, \n\
  \"cnf_timeout_s\": 30, \n\
  \"cnf_rtt_tcp_payload_num\": 11, \n\
  \"cnf_dl_num_flows\": 5, \n\
  \"cnf_ul_num_flows\": 5, \n\
  \"cnf_dl_duration_s\": 10, \n\
  \"cnf_ul_duration_s\": 10, \n\
  \"cnf_dl_pretest_duration_s\": 1, \n\
  \"cnf_ul_pretest_duration_s\": 1, \n\
  \"cnf_dl_wait_time_s\": 20, \n\
  \"cnf_ul_wait_time_s\": 20, \n\
  \"cnf_tcp_info_sample_rate_ns\": 0 \n\
}"

#endif /* SRC_RMBT_CONFIG_H_ */
