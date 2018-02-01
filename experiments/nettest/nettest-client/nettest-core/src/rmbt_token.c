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

#include "rmbt_token.h"

#include "rmbt_ssl.h"

static const char *base64(const char *input, int ilen, char *output, size_t *olen) {
	BIO *bmem, *b64;
	BUF_MEM *bptr;

	b64 = BIO_new(BIO_f_base64());
	bmem = BIO_new(BIO_s_mem());
	b64 = BIO_push(b64, bmem);
	BIO_write(b64, input, ilen);
	BIO_flush(b64);
	BIO_get_mem_ptr(b64, &bptr);

	if (bptr->length > *olen) {
		BIO_free_all(b64);
		return NULL;
	} else {
		memcpy((void *) output, bptr->data, bptr->length);
		output[bptr->length - 1] = '\0';
		*olen = bptr->length;
		BIO_free_all(b64);
		return output;
	}
}

const char *calc_token(const char *secret, const char *uuid, const char *start_time_str, char *hmac_out, size_t hmac_out_size) {
	unsigned char md_buf[EVP_MAX_MD_SIZE];
	unsigned int md_size = sizeof(md_buf);

	unsigned char msg[128];
	int r;
	r = snprintf((char *) msg, sizeof(msg), "%s_%s", uuid, start_time_str);
	if (r < 0)
		return 0;

	unsigned char *md = HMAC(EVP_sha1(), secret, (int) strlen(secret), msg, strnlen((char *) msg, sizeof(msg)), md_buf, &md_size);
	if (md == NULL)
		return NULL;
	return base64((char *) md, (int) md_size, hmac_out, &hmac_out_size);
}

