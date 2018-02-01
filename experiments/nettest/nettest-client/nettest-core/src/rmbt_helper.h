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

#ifndef SRC_RMBT_HELPER_H_
#define SRC_RMBT_HELPER_H_

#include "rmbt_common.h"

void fail(const char *format, ...) __attribute__ ((noreturn,format (printf, 1, 2)));
void fail_errno(int err, const char *fmt, ...) __attribute__ ((noreturn,format (printf, 2, 3)));
void fail_ssl(void) __attribute__ ((noreturn));
void ts_fill(struct timespec *now) __attribute__ ((hot));
int_fast64_t ts_diff(struct timespec *start) __attribute__ ((hot));
void ts_copy(struct timespec *dest, struct timespec *src);
bool variable_subst(char *dst, size_t dst_size, const char *src, const char **replacements, size_t num_replacements);

#endif /* SRC_RMBT_HELPER_H_ */
