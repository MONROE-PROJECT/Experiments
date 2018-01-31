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

#include "rmbt_ssl.h"

#include "rmbt_helper.h"

static pthread_mutex_t *lockarray = NULL;
SSL_CTX *ssl_ctx = NULL;
pthread_mutex_t ssl_ctx_mutex = PTHREAD_MUTEX_INITIALIZER;

#pragma GCC diagnostic push  // require GCC 4.6
#pragma GCC diagnostic ignored "-Wunused-function"
static void lock_callback(int mode, int type, const char *file, int line) {
	(void) file;
	(void) line;
	if (mode & CRYPTO_LOCK) {
		pthread_mutex_lock(&(lockarray[type]));
	} else {
		pthread_mutex_unlock(&(lockarray[type]));
	}
}

static unsigned long thread_id(void) {
	unsigned long ret;

	ret = (unsigned long) pthread_self();
	return (ret);
}
#pragma GCC diagnostic pop  // require GCC 4.6

void init_ssl(bool ssl) {
	int i;

	lockarray = (pthread_mutex_t *) calloc((size_t) CRYPTO_num_locks(), sizeof(pthread_mutex_t));
	for (i = 0; i < CRYPTO_num_locks(); i++)
		pthread_mutex_init(&(lockarray[i]), NULL);

	SSL_library_init(); /* load encryption & hash algorithms for SSL */
	SSL_load_error_strings(); /* we also want some error msg without using ssl */

	CRYPTO_set_id_callback(thread_id);
	CRYPTO_set_locking_callback(lock_callback);

	if (ssl) {
		ssl_ctx = SSL_CTX_new(SSLv23_method());
		if (ssl_ctx == NULL)
			fail_ssl();
		SSL_CTX_set_options(ssl_ctx, SSL_OP_NO_SSLv2 | SSL_OP_NO_SSLv3);
		SSL_CTX_set_mode(ssl_ctx, SSL_MODE_AUTO_RETRY);
	}

	/*
	 if (SSL_CTX_use_certificate_chain_file(ssl_ctx, cert_path) <= 0)
	 {
	 ERR_print_errors_fp(stderr);
	 exit(EXIT_FAILURE);
	 }
	 */

	/* Load the server private-key into the SSL context */
	/*
	 if (SSL_CTX_use_PrivateKey_file(ssl_ctx, key_path, SSL_FILETYPE_PEM) <= 0)
	 {
	 ERR_print_errors_fp(stderr);
	 exit(EXIT_FAILURE);
	 }
	 */

	/* Load trusted CA. */
	/*
	 if (!SSL_CTX_load_verify_locations(ctx,CA_CERT,NULL))
	 {
	 ERR_print_errors_fp(stderr);
	 exit(1);
	 }
	 */

	/* Set to require peer (client) certificate verification */
	/*SSL_CTX_set_verify(ctx, SSL_VERIFY_PEER, verify_callback);*/
	/* Set the verification depth to 1 */
	/*SSL_CTX_set_verify_depth(ctx,1);*/

}

static ssize_t to_hex(unsigned char *dst, size_t dst_len, unsigned char *src, size_t src_len) {
	ssize_t wr = 0;
	for (size_t i = 0; i < src_len; i++) {
		int w = snprintf((char *) dst + wr, dst_len - (size_t) wr, "%02X", src[i]);
		if (w <= 0)
			return -1;
		wr += (ssize_t) w;
	}
	return wr;
}

char *get_ssl_debug(SSL *ssl) {
	//		SSL_SESSION_print_fp(stderr, SSL_get_session(ssl));

	ssize_t r;
	unsigned char buf_client_random[256];
	unsigned char buf_master_key[256];
	SSL_SESSION *ssl_session = SSL_get_session(ssl);

#ifdef HAVE_SSL_SESSION_GET_MASTER_KEY
	unsigned char buf_raw[256];
	size_t ssl_r = SSL_get_client_random(ssl, buf_raw, sizeof(buf_raw));
	if (ssl_r <= 0)
		return NULL;
	r = to_hex(buf_client_random, sizeof(buf_client_random), buf_raw, ssl_r);
	if (r <= 0)
		return NULL;

	ssl_r = SSL_SESSION_get_master_key(ssl_session, buf_raw, sizeof(buf_raw));
	if (ssl_r <= 0)
		return NULL;
	r = to_hex(buf_master_key, sizeof(buf_master_key), buf_raw, ssl_r);
	if (r <= 0)
		return NULL;
#else
	r = to_hex(buf_client_random, sizeof(buf_client_random), ssl->s3->client_random, sizeof(ssl->s3->client_random));
	if (r <= 0)
		return NULL;
	r = to_hex(buf_master_key, sizeof(buf_master_key), ssl_session->master_key, sizeof(ssl_session->master_key));
	if (r <= 0)
		return NULL;
#endif
	char *result;
	r = asprintf(&result, "CLIENT_RANDOM %s %s", buf_client_random, buf_master_key);
	if (r > 0)
		return result;
	return NULL;
}

/* mainly to make valgrind usable */
void shutdown_ssl(void) {
	if (ssl_ctx != NULL)
		SSL_CTX_free(ssl_ctx);
	ssl_ctx = NULL;
#if !defined(HAVE_ERR_REMOVE_THREAD_STATE_DEPRECATED) && \
  defined(HAVE_ERR_REMOVE_THREAD_STATE)
	ERR_remove_thread_state(NULL);
#endif
	CRYPTO_cleanup_all_ex_data();
	ERR_free_strings();
#if !defined(HAVE_ERR_REMOVE_THREAD_STATE) && !defined(HAVE_ERR_REMOVE_THREAD_STATE)
	ERR_remove_state(0);
#endif
	EVP_cleanup();
#ifdef HAVE_SSL_COMP_FREE_COMPRESSION_METHODS
	SSL_COMP_free_compression_methods();
#endif
	CRYPTO_set_locking_callback(NULL);
	for (int i = 0; i < CRYPTO_num_locks(); i++)
		pthread_mutex_destroy(&(lockarray[i]));
	free(lockarray);
	lockarray = NULL;
}
