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

#include "rmbt_compress.h"

#include <string.h>
#include <errno.h>

#ifdef HAVE_LZMA

#define RMBT_COMPRESS_EXT ".xz"

#include <lzma.h>

#define LZMA_PRESET 4

static bool rmbt_compress(const char *input_data, size_t input_data_length,
		FILE *f) {

	lzma_stream strm = LZMA_STREAM_INIT;
	lzma_ret ret = lzma_easy_encoder(&strm, LZMA_PRESET, LZMA_CHECK_CRC32);
	if (ret != LZMA_OK) {
		fprintf(stderr, "error in lzma_easy_encoder");
		return false;
	}

	uint8_t outbuf[BUFSIZ];
	strm.next_in = (const uint8_t *) input_data;
	strm.avail_in = input_data_length;
	strm.next_out = outbuf;
	strm.avail_out = sizeof(outbuf);

	for (;;) {
		ret = lzma_code(&strm, LZMA_FINISH);
		if (strm.avail_out == 0 || ret == LZMA_STREAM_END) {
			size_t write_size = sizeof(outbuf) - strm.avail_out;
			if (fwrite(outbuf, 1, write_size, f) != write_size) {
				fprintf(stderr, "error while writing to file: %s",
						strerror(errno));
				return false;
			}
			if (ret == LZMA_STREAM_END)
				break;
			strm.next_out = outbuf;
			strm.avail_out = sizeof(outbuf);

		}
		if (ret != LZMA_OK) {
			fprintf(stderr, "error in lzma_code");
			return false;
		}
	}

	lzma_end(&strm);

	return true;
}

#endif /* HAVE_LZMA */

bool rmbt_write_to_file(const char *filename, const char *data) {

	FILE *f = fopen(filename, "w");
	if (f == NULL) {
		fprintf(stderr, "error while opening %s: %s", filename,
				strerror(errno));
		return false;
	}

	size_t data_len = strlen(data);

	bool done = false;
#ifdef RMBT_COMPRESS_EXT
	char *dot = strrchr(filename, '.');
	if (dot && !strcmp(dot, RMBT_COMPRESS_EXT)) {
		if (!rmbt_compress(data, data_len, f)) {
			fprintf(stderr, "error while compressing %s", filename);
			return false;
		}
		done = true;
	}
#endif
	if (!done) {
		if (fwrite(data, 1, data_len, f) != data_len) {
			fprintf(stderr, "error while writing to %s: %s", filename,
					strerror(errno));
			return false;
		}
	}

	fclose(f);

	return true;
}
