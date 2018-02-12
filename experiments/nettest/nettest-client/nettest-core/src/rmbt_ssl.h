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

#ifndef SRC_RMBT_SSL_H_
#define SRC_RMBT_SSL_H_

#include "rmbt_common.h"

#define OPENSSL_THREAD_DEFINES
#include <openssl/opensslconf.h>
#if !defined(OPENSSL_THREADS)
#error no thread support in openssl
#endif

#include <openssl/bio.h> /* BIO objects for I/O */
#include <openssl/crypto.h>
#include <openssl/ssl.h> /* SSL and SSL_CTX for SSL connections */
#include <openssl/err.h> /* Error reporting */
#include <openssl/hmac.h>

#include "rmbt_config.h"

extern SSL_CTX *ssl_ctx;
extern pthread_mutex_t ssl_ctx_mutex;

#if OPENSSL_VERSION_NUMBER >= 0x10002003L && \
  OPENSSL_VERSION_NUMBER <= 0x10002FFFL && \
  !defined(OPENSSL_NO_COMP)
#define HAVE_SSL_COMP_FREE_COMPRESSION_METHODS 1
#endif

#if (OPENSSL_VERSION_NUMBER >= 0x10000000L)
#define HAVE_ERR_REMOVE_THREAD_STATE 1
#endif

#if (OPENSSL_VERSION_NUMBER >= 0x10100000L) && /* OpenSSL 1.1.0+ */ \
  !defined(LIBRESSL_VERSION_NUMBER)
#define HAVE_ERR_REMOVE_THREAD_STATE_DEPRECATED 1
#define HAVE_SSL_SESSION_GET_MASTER_KEY 1
#endif

void init_ssl(bool ssl);

char *get_ssl_debug(SSL *ssl);

void shutdown_ssl(void);

#endif /* SRC_RMBT_SSL_H_ */
