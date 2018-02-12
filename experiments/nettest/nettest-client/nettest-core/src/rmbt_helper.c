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

#include "rmbt_helper.h"

#include <stdarg.h>
#include "rmbt_ssl.h"

#define I_1E9 (int_fast64_t)1000000000

void fail(const char *fmt, ...) {
	va_list ap;
	va_start(ap, fmt);
	vfprintf(stderr, fmt, ap);
	va_end(ap);
	fprintf(stderr, "\n");
	exit(EXIT_FAILURE);
}

void fail_errno(int err, const char *fmt, ...) {
	va_list ap;
	va_start(ap, fmt);
	vfprintf(stderr, fmt, ap);
	va_end(ap);
	errno = err;
	perror("error: ");
	fprintf(stderr, "\n");
	exit(EXIT_FAILURE);
}

void fail_ssl() {
	fprintf(stderr, "ssl error:\n");
	ERR_print_errors_fp(stderr);
	exit(EXIT_FAILURE);
}

void ts_fill(struct timespec *now) {
	int rc = clock_gettime(CLOCK_MONOTONIC, now);
	if (rc == -1)
		fail("error during clock_gettime");
}

int_fast64_t ts_diff(struct timespec *start) {
	struct timespec end;
	ts_fill(&end);

	if ((end.tv_nsec - start->tv_nsec) < 0) {
		end.tv_sec = end.tv_sec - start->tv_sec - 1;
		end.tv_nsec = I_1E9 + end.tv_nsec - start->tv_nsec;
	} else {
		end.tv_sec = end.tv_sec - start->tv_sec;
		end.tv_nsec = end.tv_nsec - start->tv_nsec;
	}
	return end.tv_nsec + (int_fast64_t) end.tv_sec * I_1E9 ;
}

void ts_copy(struct timespec *dest, struct timespec *src) {
	memcpy(dest, src, sizeof(struct timespec));
}

bool variable_subst(char *dst, size_t dst_size, const char *src, const char **replacements, size_t num_replacements) {
	size_t len = 0;
	const char *start = src;
	for (;;) {
		const char *delim_start = index(start, '{');

		if (delim_start == NULL) {
			size_t size = strlen(start);
			if (size + 1 > dst_size - len)
				return false;
			memcpy(dst + len, start, size + 1);
			return true;
		}

		size_t size = (size_t) (delim_start - start);
		if (size > dst_size - len)
			return false;
		memcpy(dst + len, start, size);
		len += size;
		const char *delim_end = index(delim_start, '}');
		if (delim_end != NULL) {
			bool found = false;
			for (size_t i = 0; i < num_replacements * 2; i += 2) {
				if (strncmp(delim_start + 1, replacements[i], (size_t) (delim_end - delim_start - 1)) == 0) {
					size = strlen(replacements[i + 1]);
					if (size > dst_size - len)
						return false;
					memcpy(dst + len, replacements[i + 1], size);
					len += size;
					found = true;
					break;
				}
			}
			if (!found) {
				size = (size_t) (delim_end - delim_start + 1);
				if (size > dst_size - len)
					return false;
				memcpy(dst + len, delim_start, size);
				len += size;
			}
			start = delim_end + 1;
		}
	}
	return true;
}
