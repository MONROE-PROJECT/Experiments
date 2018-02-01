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

#include "rmbt_flow.h"

#include <stdbool.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <fcntl.h>
#include <netdb.h>
#include <arpa/inet.h>
#include <poll.h>

#include "rmbt_helper.h"
#include "rmbt_ssl.h"
#include "rmbt_stats.h"

#define MAX_CHUNKSIZE	65536
#define DATAPOINT_INCREMENT_PRETEST 32
#define DATAPOINT_INCREMENT_MAIN 51200

#define NL_C			'\n'
#define NL				"\n"
#define WHITESPACE		" \t"
#define EMPTY			""
#define GETCHUNKS		"GETCHUNKS"
#define GETTIME			"GETTIME"
#define PUT				"PUT"
#define PUTNORESULT		"PUTNORESULT"
#define PING			"PING"
#define PONG			"PONG"
#define QUIT			"QUIT"
#define OK				"OK"
#define ERR				"ERR"
#define BYE				"BYE"
#define ACCEPT			"ACCEPT"
#define CHUNKSIZE		"CHUNKSIZE"
#define TOKEN			"TOKEN"
#define RMBTv			"RMBTv"

#define BYTE_CONTINUE	0x00
#define BYTE_END		0xff

#define M_TOKEN			0x0001
#define M_QUIT			0x0002
#define M_GETCHUNKS		0x0004
#define M_GETTIME		0x0008
#define M_PUT			0x0010
#define M_PUTNORESULT	0x0020
#define M_PING			0x0040
#define M_OK			0x0100
#define M_ERR			0x0200
#define M_BYE			0x0400

#define MASK_IS_SET(mask,bit)	((mask & bit) == bit)
#define IS_OK(mask)		MASK_IS_SET(mask,M_OK)
#define IS_ERR(mask)	MASK_IS_SET(mask,M_ERR)

#define BUF_SIZE		512

#define NUM_ERRORS		16

#define I_1E9 (int_fast64_t) 1000000000

#define BARRIER RETURN_IF_NOK(barrier_wait(s))

#define IS_SSL_WANT_READ_OR_WRITE(x)	((x == SSL_ERROR_WANT_READ) || (x == SSL_ERROR_WANT_WRITE))

#define NEED_POLL_READ	-2
#define NEED_POLL_WRITE	-3
#define IS_NEED_POLL(x) (x == NEED_POLL_READ || x == NEED_POLL_WRITE)

#if !defined(TCP_CORK) && defined(TCP_NOPUSH) /* hack for now to make it work on *BSD */
#define TCP_CORK TCP_NOPUSH
#endif

typedef uint_fast16_t Mask;

typedef struct {
	const TestConfig *config;
	ThreadArg *targ;
	unsigned char *buf_chunk;
	SSL *ssl;
	int socket_fd;
	long unread_buf_s;
	long unread_buf_e;
	Mask mask;
	char unread_buf[BUF_SIZE];
	char *error[NUM_ERRORS];
	bool have_err;
	bool need_reconnect;
} State;

__attribute__ ((hot)) inline static int_fast64_t get_relative_time_ns(State *s) {
	return ts_diff(s->targ->ts_zero);
}

__attribute__ ((format (printf, 2, 3))) static bool add_error(State *s, const char *fmt, ...) {
	s->targ->barrier->global_abort = true;
	pthread_cond_broadcast(&s->targ->barrier->cond);

	s->have_err = true;
	for (uint_fast16_t i = 0; i < NUM_ERRORS; i++) {
		if (s->error[i] == NULL) {
			va_list ap;
			va_start(ap, fmt);
			int r = vasprintf(&(s->error[i]), fmt, ap);
			va_end(ap);
			if (r == -1)
				perror("could not add_error");
			break;
		}
	}
	return false;
}

static void collect_ssl_errors(State *s) {
	const char *file = NULL;
	const char *data = NULL;
	int line;
	int flags = ERR_TXT_STRING;

	unsigned long err;
	while ((err = ERR_get_error_line_data(&file, &line, &data, &flags)) != 0) {
		char buf[256];
		ERR_error_string_n(err, buf, sizeof(buf)); // ERR_error_string is NOT thread safe (as it seems)
		add_error(s, "%s:%s:%d:%s", ERR_error_string(err, NULL), file, line, data);
	}
}

__attribute__ ((format (printf, 2, 3))) static void my_log_force(__attribute__ ((unused)) State *s, const char *fmt, ...) {
	va_list ap;
	va_start(ap, fmt);
	vfprintf(stderr, fmt, ap);
	va_end(ap);
	fprintf(stderr, "\n");
}

__attribute__ ((format (printf, 2, 3))) static void my_log(State *s, const char *fmt, ...) {
	if (s->targ->do_log) {
		va_list ap;
		va_start(ap, fmt);
		vfprintf(stderr, fmt, ap);
		va_end(ap);
		fprintf(stderr, "\n");
	}
}

static void get_errors(State *s, char *dst, size_t dst_size) {
	collect_ssl_errors(s);
	size_t len = 0;
	for (uint_fast16_t i = 0; i < NUM_ERRORS; i++) {
		if (s->error[i] != NULL) {
			int res = snprintf(dst + len, dst_size - len, len == 0 ? "%s" : "; %s", s->error[i]);
			if (res > 0)
				len += (size_t) res;
			if (res < 0 || dst_size - len <= 1)
				return;
		}
	}
}

static void print_errors(State *s, FILE *stream, bool clear) {
	collect_ssl_errors(s);
	for (uint_fast16_t i = 0; i < NUM_ERRORS; i++) {
		if (s->error[i] != NULL) {
			fprintf(stream, "%s\n", s->error[i]);
			if (clear) {
				free(s->error[i]);
				s->error[i] = NULL;
			}
		}
	}
	if (clear)
		s->have_err = false;
}

/*
 * We don't use pthread_barrier, as it is not available on Android.
 * Also this way we can abort all threads more easily if one fails.
 */
static bool barrier_wait(State *s) {
	RmbtBarrier *b = s->targ->barrier;
	pthread_mutex_lock(&b->mutex);
	if (b->global_abort) {
		pthread_cond_broadcast(&b->cond);
		pthread_mutex_unlock(&b->mutex);
		return false;
	}

	while (! b->global_abort && b->entered == b->total) /* not all threads have left the last barrier */
		pthread_cond_wait(&b->cond, &b->mutex);

	if (++b->entered == b->total)
		pthread_cond_broadcast(&b->cond); /* if I was the last one, tell the others */

	while (! b->global_abort && b->entered < b->total) /* the barrier. waiting for the others */
		pthread_cond_wait(&b->cond, &b->mutex);

	if (++b->left == b->total) { /* I was the last one to leave, cleanup */
		b->entered = b->left = 0;
		pthread_cond_broadcast(&b->cond); /* tell threads potentially waiting for the next barrier */
	}

	bool result = ! b->global_abort;
	pthread_mutex_unlock(&b->mutex);
	return result;
}

static inline void set_nodelay(State *s, int value) {
	setsockopt(s->socket_fd, IPPROTO_TCP, TCP_NODELAY, &value, sizeof(value));
}

static inline void set_cork(State *s, int value) {
	setsockopt(s->socket_fd, IPPROTO_TCP, TCP_CORK, &value, sizeof(value));
}

static inline void set_throughput(State *s) {
	set_nodelay(s, 0);
	set_cork(s, 1);
}

static inline void set_low_delay(State *s) {
	set_cork(s, 0);
	set_nodelay(s, 1);
}

static inline int my_poll(State *s, bool read, bool write, int ssl_err) {
	if (ssl_err != 0) {
		switch (ssl_err) {
		case SSL_ERROR_WANT_READ:
			read = true;
			break;
		case SSL_ERROR_WANT_WRITE:
			write = true;
			break;
		default:
			break;
		}
	}
	short int events = 0;
	if (read)
		events |= POLLIN;
	if (write)
		events |= POLLOUT;
	if (events == 0) {
		add_error(s, "no events to monior in poll");
		return -1;
	}
	struct pollfd pfd = { .fd = s->socket_fd, .events = events };
	int ret = poll(&pfd, 1, s->config->timeout_ms);
	if (ret == 0)
		add_error(s, "timeout");
	else if (ret < 0)
		add_error(s, "error in poll: %s", strerror(errno));
	return ret;
}

static inline ssize_t my_write(State *s, unsigned char *buf, ssize_t size) {
	ssize_t num_written, total_written = 0;
	bool again;
	do {
		again = false;
		if (s->ssl != NULL) {
			num_written = SSL_write(s->ssl, buf + total_written, (int) (size - total_written));
			if (num_written <= 0) {
				int ssl_err = SSL_get_error(s->ssl, (int) num_written);
				if (IS_SSL_WANT_READ_OR_WRITE(ssl_err)) {
					int poll_res = my_poll(s, false, false, ssl_err);
					if (poll_res > 0)
						again = true;
					else
						return -1;
				} else {
					add_error(s, "error during SSL_write");
					return -1;
				}
			}
		} else {
			num_written = write(s->socket_fd, buf + total_written, (size_t) (size - total_written));
			if (num_written < 0) {
				if (errno == EAGAIN) {
					int poll_res = my_poll(s, false, true, 0);
					if (poll_res > 0)
						again = true;
					else
						return -1;
				} else {
					add_error(s, "error during write: %s", strerror(errno));
					return -1;
				}
			}
		}
		if (num_written >= 0) {
			total_written += num_written;
			if (total_written == size)
				return total_written;
		}
	} while (total_written < size || again);
	add_error(s, "unknown error in write");
	return -1;
}

static inline bool unread_empty(State *s) {
	return s->unread_buf_s == s->unread_buf_e;
}

/*
 * returns NEED_POLL_READ on EAGAIN or SSL_ERROR_WANT_READ if nonblocking
 * returns NEED_POLL_WRITE on SSL_read if SSL_ERROR_WANT_WRITE
 */
static inline long my_read(State *s, unsigned char *buf, ssize_t size, bool nonblocking) {
	if (unread_empty(s)) {
		bool again;
		do {
			again = false;
			ssize_t num_read;
			if (s->ssl != NULL) {
				num_read = SSL_read(s->ssl, buf, (int) size);
				if (num_read <= 0) {
					int ssl_err = SSL_get_error(s->ssl, (int) num_read);
					if (IS_SSL_WANT_READ_OR_WRITE(ssl_err)) {
						if (nonblocking)
							return ssl_err == SSL_ERROR_WANT_WRITE ? NEED_POLL_WRITE : NEED_POLL_READ;
						int poll_res = my_poll(s, false, false, ssl_err);
						if (poll_res > 0)
							again = true;
						else
							return -1;
					} else {
						add_error(s, "error during SSL_read");
						return -1;
					}
				}
			} else {
				num_read = read(s->socket_fd, buf, (size_t) size);
				if (num_read < 0) {
					if (errno == EAGAIN) {
						if (nonblocking)
							return NEED_POLL_READ;
						int poll_res = my_poll(s, true, false, 0);
						if (poll_res > 0)
							again = true;
						else
							return -1;
					} else {
						add_error(s, "error during read: %s", strerror(errno));
						return -1;
					}
				}
			}
			if (num_read >= 0) {
				s->targ->flow_result->flow_bytes_dl += num_read;
				return num_read;
			}
		} while (again);
		add_error(s, "unknown error in read");
		return -1;
	} else {
		long bs = sizeof(s->unread_buf);
		long unread_size = s->unread_buf_e - s->unread_buf_s;
		if (unread_size < 0)
			unread_size += bs;
		if (unread_size < size)
			size = unread_size;
		long first_copy = size, second_copy = 0;
		long max_first = bs - s->unread_buf_s;
		if (first_copy > max_first) {
			second_copy = first_copy - max_first;
			first_copy = max_first;
		}
		memcpy(buf, s->unread_buf + s->unread_buf_s, (size_t) first_copy);
		if (second_copy != 0)
			memcpy(buf + first_copy, s->unread_buf, (size_t) second_copy);
		s->unread_buf_s += size;
		if (s->unread_buf_s >= bs)
			s->unread_buf_s -= bs;
		if (s->unread_buf_s == s->unread_buf_e)
			s->unread_buf_s = s->unread_buf_e = 0;
		return size;
	}
}

static void my_unread(State *s, unsigned char *buf, long size) {
	long bs = sizeof(s->unread_buf);
	long max = s->unread_buf_s - s->unread_buf_e;
	if (max <= 0)
		max += bs;
	if (max < size)
		size = max;
	long first_copy = size, second_copy = 0;
	long max_first = bs - s->unread_buf_e;
	if (first_copy > max_first) {
		second_copy = first_copy - max_first;
		first_copy = max_first;
	}
	memcpy(s->unread_buf + s->unread_buf_e, buf, (size_t) first_copy);
	if (second_copy != 0)
		memcpy(s->unread_buf, buf + first_copy, (size_t) second_copy);
	s->unread_buf_e += size;
	if (s->unread_buf_e >= bs)
		s->unread_buf_e -= bs;
}

/*
 * may return NEED_POLL_READ / NEED_POLL_WRITE
 */
static inline long my_readline(State *s, unsigned char *buf, int size, bool nonblocking) {
	unsigned char *buf_ptr = buf;
	ssize_t size_remain = size;
	long r;
	unsigned char *nl_ptr = NULL;

	do {
		r = my_read(s, (void*) buf_ptr, size_remain, nonblocking);
		if (nonblocking && IS_NEED_POLL(r)) {
			if (buf_ptr > buf) {
//				printf("unread nb: %ld:%s\n", buf_ptr - buf, buf);
				my_unread(s, buf, buf_ptr - buf);
			}
			return r;
		}
		if (r > 0) {
			nl_ptr = memchr(buf_ptr, NL_C, (size_t) r);
			buf_ptr += r;
			size_remain -= r;
		}
	} while (r > 0 && nl_ptr == NULL && size_remain > 0);
	if (nl_ptr == NULL && size_remain <= 0)
		return -1;
	if (nl_ptr != NULL) {
		*nl_ptr = '\0';
		if (nl_ptr + 1 < buf_ptr) {
			//printf("unread: %ld:%s\n", buf_ptr - nl_ptr - 1, nl_ptr + 1);
			my_unread(s, nl_ptr + 1, buf_ptr - nl_ptr - 1);
		}
		return nl_ptr - buf + 1;
	} else
		return buf_ptr - buf;
}

/*
 * may return NEED_POLL_READ / NEED_POLL_WRITE
 */
static long read_time_bytes(State *s, int_fast64_t *time, bool *got_bytes, int_fast64_t *bytes, bool nonblocking) {
	unsigned char buf[BUF_SIZE];
	long r = my_readline(s, buf, sizeof(buf), nonblocking);
	if (nonblocking && IS_NEED_POLL(r))
		return r;
	if (r <= 0)
		return add_error(s, "could not read TIME from server");
	if (bytes != NULL)
		r = sscanf((char*) buf, "TIME %" SCNdFAST64 " BYTES %"SCNdFAST64, time, bytes);
	else
		r = sscanf((char*) buf, "TIME %" SCNdFAST64, time);
	if (r <= 0)
		return add_error(s, "could not parse TIME from server: %s", buf);
	if (got_bytes != NULL)
		(*got_bytes) = (r == 2);
	return true;
}

static inline bool read_time(State *s, int_fast64_t *time) {
	return read_time_bytes(s, time, NULL, NULL, false);
}

static bool read_ok(State *s) {
	unsigned char buf[BUF_SIZE];
	long r = my_readline(s, buf, sizeof(buf), false);
	if (r <= 0)
		return add_error(s, "could not read OK from server");
	if (strcmp(OK, (char*) buf) != 0)
		return add_error(s, "expected server to send OK");
	return true;
}

static bool read_ok_accept(State *s) {
	unsigned char buf[BUF_SIZE];
	s->mask = 0;
	while (true) {
		long r = my_readline(s, buf, sizeof(buf), false);
		if (r <= 0)
			return add_error(s, "could not read from server");

		char *saveptr, *first, *rest;
		first = strtok_r((char*) buf, WHITESPACE, &saveptr);
		rest = strtok_r(NULL, EMPTY, &saveptr);

		if (strcmp(OK, first) == 0) {
			s->mask |= M_OK;
		} else if (strcmp(ACCEPT, first) == 0) {
			char *str, *part;
			for (str = rest;; str = NULL) {
				part = strtok_r(str, WHITESPACE, &saveptr);
				if (part == NULL)
					break;
				if (strcmp(TOKEN, part) == 0)
					s->mask |= M_TOKEN;
				else if (strcmp(QUIT, part) == 0)
					s->mask |= M_QUIT;
				else if (strcmp(GETCHUNKS, part) == 0)
					s->mask |= M_GETCHUNKS;
				else if (strcmp(GETTIME, part) == 0)
					s->mask |= M_GETTIME;
				else if (strcmp(PUT, part) == 0)
					s->mask |= M_PUT;
				else if (strcmp(PUTNORESULT, part) == 0)
					s->mask |= M_PUTNORESULT;
				else if (strcmp(PING, part) == 0)
					s->mask |= M_PING;
			}
			return true;
		} else if (strcmp(CHUNKSIZE, first) == 0) {
			int_fast32_t chunksize;
			sscanf(rest, "%" SCNdFAST32, &chunksize);
			if (chunksize <= 0 || chunksize > MAX_CHUNKSIZE)
				return add_error(s, "server sent illegal CHUNKSIZE: %"PRIdFAST32" (max: %"PRIdFAST32")", chunksize, (int_fast32_t) MAX_CHUNKSIZE);

			s->targ->flow_result->connection_info.chunksize = chunksize;
			free(s->buf_chunk);
			s->buf_chunk = calloc((size_t) (s->targ->flow_result->connection_info.chunksize), 1);
		} else if (strcmp(ERR, first) == 0) {
			s->mask |= M_ERR;
			return add_error(s, "server responded with: %s", buf);
		} else if (strcmp(BYE, first) == 0) {
			s->mask |= M_BYE;
			return true;
		} else if (strncmp(RMBTv, first, strlen(RMBTv)) == 0) {
			if (strlen(first) < sizeof(s->targ->flow_result->connection_info.server_version))
				strncpy(s->targ->flow_result->connection_info.server_version, first, sizeof(s->targ->flow_result->connection_info.server_version));
		} else
			return add_error(s, "could not parse line from server: %s", buf);
	}
}

__attribute__ ((format (printf, 2, 3))) static bool write_to_server(State *s, const char *fmt, ...) {
	unsigned char buf[BUF_SIZE];
	va_list ap;
	va_start(ap, fmt);
	ssize_t num = vsnprintf((char*) buf, sizeof(buf), fmt, ap);
	if (num <= 0)
		return add_error(s, "error while writing to server (vsnprintf)");
	va_end(ap);
	num = my_write(s, buf, num);
	if (num <= 0)
		return add_error(s, "error while writing to server");
	s->targ->flow_result->flow_bytes_ul += num;
	return true;
}

static void extract_ip_port_from_sockaddr(struct sockaddr_storage *addr, in_port_t *port, const void **ip_addr) {
	if (addr->ss_family == AF_INET) { // IPv4
		struct sockaddr_in *si = (struct sockaddr_in *) addr;
		*port = si->sin_port;
		*ip_addr = &si->sin_addr;
	} else if (addr->ss_family == AF_INET6) { // IPv6
		struct sockaddr_in6 *si = (struct sockaddr_in6 *) addr;
		*port = si->sin6_port;
		*ip_addr = &si->sin6_addr;
	}
}

static bool connect_to_server(State *s) {

	struct addrinfo *res, *rp, hints = { .ai_family = AF_UNSPEC, .ai_socktype = SOCK_STREAM, .ai_protocol = IPPROTO_TCP };
	int gai_err = getaddrinfo(s->config->server_host, s->config->server_port, &hints, &res);
	if (gai_err != 0)
		return add_error(s, "error in getaddrinfo (for connect): %s", gai_strerror(gai_err));

	int sfd = -1;
	for (rp = res; rp != NULL; rp = rp->ai_next) {
		sfd = socket(rp->ai_family, rp->ai_socktype, rp->ai_protocol);
		if (sfd == -1)
			continue;

		if (s->config->bind_ip != NULL) {
			struct addrinfo *res_bind, *rp_bind, hints_bind = { .ai_family = rp->ai_family, .ai_socktype = rp->ai_socktype, .ai_protocol = rp->ai_protocol };
			gai_err = getaddrinfo(s->config->bind_ip, NULL, &hints_bind, &res_bind);
			if (gai_err != 0)
				return add_error(s, "error in getaddrinfo (for bind) (ip: %s): %s", s->config->bind_ip, gai_strerror(gai_err));
			for (rp_bind = res_bind; rp_bind != NULL; rp_bind = rp_bind->ai_next) {
				if (bind(sfd, rp_bind->ai_addr, rp_bind->ai_addrlen) == 0)
					break; /* Success */
			}
			if (rp_bind == NULL)
				return add_error(s, "could not bind to specified ip: %s", s->config->bind_ip);
			freeaddrinfo(res_bind);
		}

		fcntl(sfd, F_SETFL, O_NONBLOCK);
		if (connect(sfd, rp->ai_addr, rp->ai_addrlen) == 0)
			break; /* Success */
		if (errno == EINPROGRESS) { // is nonblocking
			int poll_res = my_poll(s, true, true, 0);
			if (poll_res > 0) { // socket ready
				int err;
				socklen_t err_len = sizeof(err);
				int r = getsockopt(sfd, SOL_SOCKET, SO_ERROR, &err, &err_len);
				if (r == -1)
					return add_error(s, "error in getsockopt: %s", strerror(errno));
				if (err != 0)
					return add_error(s, "error while connecting: %s", strerror(err));
				break;
			}
		}
		my_log_force(s, "could not connect: %s", strerror(errno));
		close(sfd);
	}
	if (rp == NULL || sfd == -1)
		return add_error(s, "could not connect to server");
	freeaddrinfo(res);

	s->socket_fd = sfd;

	stats_thread_set_sfd(s->targ->thread_num, sfd);

	char buf[64];
	socklen_t buf_len = sizeof(buf);
	if (getsockopt(sfd, 6, TCP_CONGESTION, &buf, &buf_len) == 0)
		if (asprintf(&s->targ->flow_result->connection_info.tcp_congestion, "%s", buf) <= 0)
			s->targ->flow_result->connection_info.tcp_congestion = NULL;

	set_low_delay(s);

	if (s->config->encrypt) {

		pthread_mutex_lock(&ssl_ctx_mutex);
		SSL *ssl = SSL_new(ssl_ctx);
		if (ssl == NULL) {
			pthread_mutex_unlock(&ssl_ctx_mutex);
			return add_error(s, "error in SSL_new");
		}

		if (s->config->cipherlist != NULL && strlen(s->config->cipherlist) > 0) {
			int r = SSL_set_cipher_list(ssl, s->config->cipherlist);
			if (r <= 0) {
				pthread_mutex_unlock(&ssl_ctx_mutex);
				return add_error(s, "error while setting cipherlist: %s", s->config->cipherlist);
			}
		}

		SSL_set_fd(ssl, sfd);

		BIO_set_nbio(SSL_get_rbio(ssl), 1);
		BIO_set_nbio(SSL_get_wbio(ssl), 1);

		SSL_set_connect_state(ssl);

		int ssl_ret, ssl_err, poll_ret;
		do {
			poll_ret = 0;
			ERR_clear_error();
			ssl_ret = SSL_connect(ssl);
			if (ssl_ret == 1)
				break;
			ssl_err = SSL_get_error(ssl, ssl_ret);
			if (IS_SSL_WANT_READ_OR_WRITE(ssl_err))
				poll_ret = my_poll(s, false, false, ssl_err);
			else {
				pthread_mutex_unlock(&ssl_ctx_mutex);
				return add_error(s, "error during SSL_connect");
			}
		} while (poll_ret > 0);
		pthread_mutex_unlock(&ssl_ctx_mutex);

		s->ssl = ssl;
		s->targ->flow_result->connection_info.encrypt = true;
		s->targ->flow_result->connection_info.cipher = SSL_get_cipher(ssl);
		if (s->config->encrypt_debug)
			s->targ->flow_result->connection_info.tls_debug = get_ssl_debug(ssl);
	}
	RETURN_IF_NOK(read_ok_accept(s));

	struct sockaddr_storage addr;
	socklen_t addr_len = sizeof(addr);
	const void *ip_addr = NULL;
	in_port_t port = 0;

	if (getsockname(sfd, (struct sockaddr*) &addr, &addr_len) == 0) {
		extract_ip_port_from_sockaddr(&addr, &port, &ip_addr);
		inet_ntop(addr.ss_family, ip_addr, s->targ->flow_result->connection_info.ip_local, sizeof(s->targ->flow_result->connection_info.ip_local));
		s->targ->flow_result->connection_info.port_local = ntohs(port);
	}

	if (getpeername(sfd, (struct sockaddr*) &addr, &addr_len) == 0) {
		extract_ip_port_from_sockaddr(&addr, &port, &ip_addr);
		inet_ntop(addr.ss_family, ip_addr, s->targ->flow_result->connection_info.ip_server, sizeof(s->targ->flow_result->connection_info.ip_server));
		s->targ->flow_result->connection_info.port_server = ntohs(port);
	}

	return true;
}

static bool send_token(State *s) {
	if (!MASK_IS_SET(s->mask, M_TOKEN))
		return add_error(s, "expected server to accept TOKEN");

	RETURN_IF_NOK(write_to_server(s, TOKEN " %s\n", s->config->token));
	return read_ok_accept(s);
}

static bool connect_and_send_token(State *s) {
	RETURN_IF_NOK(connect_to_server(s));
	return send_token(s);
}

static bool disconnect(State *s) {
	if (s->ssl != NULL) {
		int err = SSL_shutdown(s->ssl);
		if (err < 0)
			add_error(s, "error in SSL_shutdown");
		SSL_free(s->ssl);
		s->ssl = NULL;
	}
	close(s->socket_fd);
	stats_thread_set_sfd(s->targ->thread_num, -1);
	return true;
}

static bool do_getchunks(State *s, int_fast32_t chunks, struct timespec *ts_zero, DataPoint *data_point) {
	if (!MASK_IS_SET(s->mask, M_GETCHUNKS))
		return add_error(s, "expected server to accept PING");

	data_point->time_ns = ts_diff(ts_zero); // t_begin

	RETURN_IF_NOK(write_to_server(s, GETCHUNKS " %" PRIuFAST32 NL, chunks));

	int_fast64_t totalRead = 0;
	long read;
	unsigned char lastByte = 0;
	const int_fast32_t chunksize = s->targ->flow_result->connection_info.chunksize;
	do {
		read = my_read(s, s->buf_chunk, chunksize, false);
		if (read > 0) {
			int_fast64_t posLast = chunksize - 1 - (totalRead % chunksize);
			if (read > posLast)
				lastByte = s->buf_chunk[posLast];
			totalRead += read;
		}
	} while (read > 0 && lastByte != BYTE_END);

	data_point->time_ns_end = ts_diff(ts_zero); // t_end

	RETURN_IF_NOK(write_to_server(s, OK NL));

	RETURN_IF_NOK(read_time(s, &data_point->duration_server));

	return read_ok_accept(s);
}

static bool do_rtt_tcp_payload(State *s) {
	unsigned char buf[BUF_SIZE];
	RttTcpPayloadResult *rtt_tcp_payload_result = &s->targ->flow_result->rtt_tcp_payload;

	int_fast16_t rtt_tcp_payload_num = s->config->rtt_tcp_payload_num;
	RttTcpPayload *rtt_tcp_payloads = calloc((size_t) rtt_tcp_payload_num, sizeof(RttTcpPayload));

	for (int_fast16_t i = 0; i < rtt_tcp_payload_num; i++) {
		if (!MASK_IS_SET(s->mask, M_PING))
			return add_error(s, "expected server to accept PING");

		rtt_tcp_payloads[i].time_start_rel_ns = get_relative_time_ns(s);

		struct timespec ts_start;
		ts_fill(&ts_start);
		RETURN_IF_NOK(write_to_server(s, PING NL));

		long r = my_readline(s, buf, sizeof(buf), false);
		rtt_tcp_payloads[i].rtt_client_ns = ts_diff(&ts_start);

		if (r <= 0)
			return add_error(s, "could not read PONG from server");
		if (strcmp(PONG, (char *) buf) != 0)
			return add_error(s, "expected PING, server sent: %s", buf);

		RETURN_IF_NOK(write_to_server(s, OK NL));

		RETURN_IF_NOK(read_time(s, &rtt_tcp_payloads[i].rtt_server_ns));

		rtt_tcp_payloads[i].time_end_rel_ns = get_relative_time_ns(s);

		RETURN_IF_NOK(read_ok_accept(s));
	}

	rtt_tcp_payload_result->rtt_tcp_payloads = rtt_tcp_payloads;
	rtt_tcp_payload_result->rtt_tcp_payload_num = rtt_tcp_payload_num;

	return true;
}

static bool do_pretest(State *s, int_fast16_t duration, DirectionResult *res, bool (*do_chunks)(State *, int_fast32_t, struct timespec *, DataPoint *)) {
	int_fast32_t max_datapoints = DATAPOINT_INCREMENT_PRETEST;
	DataPoint *time_series = malloc((size_t) max_datapoints * sizeof(DataPoint));
	int_fast32_t ts_idx = 0;

	int_fast32_t chunks = 1;
	struct timespec ts_end, ts_zero;
	res->time_start_rel_ns = get_relative_time_ns(s);
	ts_fill(&ts_zero);
	ts_copy(&ts_end, &ts_zero);
	ts_end.tv_sec += duration;
	int_fast64_t timediff;
	do {
		RETURN_IF_NOK(do_chunks(s, chunks, &ts_zero, &time_series[ts_idx]));
		chunks *= 2;

		if (ts_idx >= max_datapoints) {
			max_datapoints += DATAPOINT_INCREMENT_PRETEST;
			time_series = realloc(time_series, (size_t) max_datapoints * sizeof(DataPoint));
		}
		time_series[ts_idx++].bytes = chunks * s->targ->flow_result->connection_info.chunksize;

		timediff = ts_diff(&ts_end);
	} while (timediff < 0);

	res->time_series = time_series;
	res->num_time_series = ts_idx;

	res->time_end_rel_ns = get_relative_time_ns(s);
	return true;
}

static inline bool do_pretest_downlink(State *s) {
	return do_pretest(s, s->config->dl_pretest_duration_s, &s->targ->flow_result->pretest_dl, do_getchunks);
}

__attribute__ ((flatten,hot)) static bool do_downlink(State *s) {
	if (!MASK_IS_SET(s->mask, M_GETTIME))
		return add_error(s, "expected server to accept GETTIME");

	DirectionResult *res = &s->targ->flow_result->dl;

	res->time_start_rel_ns = get_relative_time_ns(s);

	struct timespec ts_start;
	ts_fill(&ts_start);
	RETURN_IF_NOK(write_to_server(s, GETTIME " %" PRIdFAST16 "\n", s->config->dl_duration_s));

	int_fast64_t totalRead = 0;
	int_fast64_t read;
	unsigned char lastByte = 0;
	int_fast64_t timediff_ns = 0;
	int_fast64_t max_timediff_ns = (s->config->dl_duration_s + s->config->dl_wait_time_s) * I_1E9;

	int_fast32_t max_datapoints = DATAPOINT_INCREMENT_MAIN;
	DataPoint *time_series = malloc((size_t) max_datapoints * sizeof(DataPoint));
	int_fast32_t ts_idx = 0;

	const int_fast32_t chunksize = s->targ->flow_result->connection_info.chunksize;

	do {
		read = my_read(s, s->buf_chunk, chunksize, false);
		if (read > 0) {
			int_fast64_t posLast = chunksize - 1 - (totalRead % chunksize);
			if (read > posLast)
				lastByte = (unsigned char) s->buf_chunk[posLast];
			totalRead += read;

			timediff_ns = ts_diff(&ts_start);

			if (ts_idx >= max_datapoints) {
				max_datapoints += DATAPOINT_INCREMENT_MAIN;
				time_series = realloc(time_series, (size_t) max_datapoints * sizeof(DataPoint));
			}
			time_series[ts_idx].bytes = totalRead;
			time_series[ts_idx].time_ns = timediff_ns;
			time_series[ts_idx].duration_server = 0;
			time_series[ts_idx++].time_ns_end = 0;
		}
	} while (read > 0 && lastByte != BYTE_END && timediff_ns < max_timediff_ns);

	if (read <= 0)
		return add_error(s, "error during do_downlink");

	res->time_series = time_series;
	res->num_time_series = ts_idx;

	res->time_end_rel_ns = get_relative_time_ns(s);

	/* need to reconnect */
	if (lastByte != BYTE_END) {
		my_log_force(s, "need reconnect");
		s->need_reconnect = true;
		res->duration_server_ns = 0;
		return true;
	}

	RETURN_IF_NOK(write_to_server(s, OK NL));

	RETURN_IF_NOK(read_time(s, &res->duration_server_ns));

	return read_ok_accept(s);
}

static bool do_putchunks(State *s, int_fast32_t chunks, struct timespec *ts_zero, DataPoint *data_point) {
	if (!MASK_IS_SET(s->mask, M_PUTNORESULT))
		return add_error(s, "expected server to accept PUTNORESULT");

	RETURN_IF_NOK(write_to_server(s, PUTNORESULT NL));

	RETURN_IF_NOK(read_ok(s));

	data_point->time_ns = ts_diff(ts_zero); // t_begin

	const int_fast32_t chunksize = s->targ->flow_result->connection_info.chunksize;

	s->buf_chunk[chunksize - 1] = BYTE_CONTINUE;

	set_throughput(s);

	int_fast64_t total_written = 0;
	for (int_fast32_t i = 0; i < chunks; i++) {
		if (i == chunks - 1) // for last chunk
			s->buf_chunk[chunksize - 1] = BYTE_END;
		ssize_t num = my_write(s, s->buf_chunk, chunksize);
		if (num < 0)
			return add_error(s, "error while writing to server in do_putchunks");
		total_written += num;
	}
	s->targ->flow_result->flow_bytes_ul += total_written;

	set_low_delay(s);

	RETURN_IF_NOK(read_time(s, &data_point->duration_server));

	data_point->time_ns_end = ts_diff(ts_zero); // t_end

	return read_ok_accept(s);
}

static inline bool do_prestest_uplink(State *s) {
	return do_pretest(s, s->config->ul_pretest_duration_s, &s->targ->flow_result->pretest_ul, do_putchunks);
}

__attribute__ ((flatten,hot)) static bool do_uplink(State *s) {
	if (!MASK_IS_SET(s->mask, M_PUT))
		return add_error(s, "expected server to accept PUT");

	DirectionResult *res = &s->targ->flow_result->ul;

	res->time_start_rel_ns = get_relative_time_ns(s);

	RETURN_IF_NOK(write_to_server(s, PUT NL));

	RETURN_IF_NOK(read_ok(s));

	BARRIER; // barrier with other flow do_uplink()s

	const int_fast32_t chunksize = s->targ->flow_result->connection_info.chunksize;

	s->buf_chunk[chunksize - 1] = BYTE_CONTINUE; // set last byte to continue value

	int_fast32_t max_datapoints = DATAPOINT_INCREMENT_MAIN;
	DataPoint *time_series = malloc((size_t) max_datapoints * sizeof(DataPoint));
	int_fast32_t ts_idx = 0;

	struct timespec ts_start;
	ts_fill(&ts_start);

	int_fast64_t total_bytes_written = 0;
	int_fast64_t timediff_ns, max_timediff_ns = s->config->ul_duration_s * I_1E9;
	int_fast64_t cutoff_timediff_ns = (s->config->ul_duration_s + s->config->ul_wait_time_s) * I_1E9;

	struct pollfd pfd = { .fd = s->socket_fd };

	set_throughput(s);

	bool last_chunk = false, stop_writing = false;
	bool ssl_need_read = false, ssl_need_write = false;
	bool poll_read = false, poll_write = false;
	do {
		// we always want to read
		timediff_ns = ts_diff(&ts_start);
		if (poll_read && (poll_write || (!ssl_need_write && stop_writing))) {
			if (s->ssl != NULL && SSL_pending(s->ssl) > 0)
				poll_read = false;
			else {
				pfd.events = POLLIN | (poll_write ? POLLOUT : 0);
				int poll_ret = poll(&pfd, 1, s->config->timeout_ms);
				if (poll_ret != 1) // timeout or error
					return add_error(s, "error in poll of do_uplink: %s", poll_ret == 0 ? "timeout" : strerror(errno));
				if (pfd.revents & POLLIN)
					poll_read = false;
				if (pfd.revents & POLLOUT)
					poll_write = false;
			}
		}

		if (!stop_writing && (!poll_write || (ssl_need_read && !poll_read))) { // can write
			ssize_t offset = total_bytes_written % chunksize;
			ssize_t written;
			bool poll_needed = false;
			if (s->ssl != NULL) {
				written = SSL_write(s->ssl, s->buf_chunk + offset, (int) (chunksize - offset));
				int ssl_err = SSL_get_error(s->ssl, (int) written);
				if (written <= 0 && IS_SSL_WANT_READ_OR_WRITE(ssl_err)) {
					if (ssl_err == SSL_ERROR_WANT_READ) {
						poll_read = true;
						ssl_need_read = true;
					} else if (ssl_err == SSL_ERROR_WANT_WRITE) {
						poll_write = true;
					}
					poll_needed = true;
				}
			} else {
				written = write(s->socket_fd, s->buf_chunk + offset, (size_t) (chunksize - offset));
				if (written == -1 && errno == EAGAIN) {
					poll_write = true;
					poll_needed = true;
				}
			}
			if (!poll_needed) {
				ssl_need_read = false;
				if (written <= 0)
					return add_error(s, "error while writing to server in do_uplink");
				total_bytes_written += written;

				if (last_chunk && total_bytes_written % chunksize == 0) {
					set_low_delay(s);
					stop_writing = true;
				}

				if (timediff_ns >= max_timediff_ns && !last_chunk) {
					s->buf_chunk[chunksize - 1] = BYTE_END; // set last byte to termination value
					last_chunk = true;
				}
			}
		}

		if (!poll_read || (ssl_need_write && !poll_write)) { // can read
			bool got_bytes = false;
			if (ts_idx >= max_datapoints) {
				max_datapoints += DATAPOINT_INCREMENT_MAIN;
				time_series = realloc(time_series, (size_t) max_datapoints * sizeof(DataPoint));
			}

			long ret = read_time_bytes(s, &time_series[ts_idx].time_ns, &got_bytes, &time_series[ts_idx].bytes, true);
			// ret == NEED_POLL_READ on EAGAIN/SSL_ERROR_WANT_READ
			// ret == NEED_POLL_WRITE on SSL_ERROR_WANT_WRITE
			if (IS_NEED_POLL(ret)) {
				if (ret == NEED_POLL_READ) {
					poll_read = true;
				} else if (ret == NEED_POLL_WRITE) {
					poll_write = true;
					ssl_need_write = true;
				}
				continue;
			}
			if (ret != true)
				return false;

			ssl_need_write = false;

			time_series[ts_idx].time_ns_end = 0;
			time_series[ts_idx++].duration_server = 0;

			if (!got_bytes) { // got end result; end result has no bytes set
				time_series[ts_idx - 1].bytes = total_bytes_written;
				s->targ->flow_result->ul.time_series = time_series;
				s->targ->flow_result->ul.num_time_series = ts_idx;
				break;
			}
		}
	} while (timediff_ns < cutoff_timediff_ns);

	set_low_delay(s);

	s->targ->flow_result->flow_bytes_ul += total_bytes_written;

	res->time_end_rel_ns = get_relative_time_ns(s);

	/* need to reconnect */
	if (timediff_ns >= cutoff_timediff_ns) {
		my_log_force(s, "cutoff time reached");
		s->need_reconnect = true;
		return true;
	}

	return read_ok_accept(s);
}

static bool check_for_reconnect(State *s) {
	if (s->need_reconnect) {
		RETURN_IF_NOK(disconnect(s));
		RETURN_IF_NOK(connect_and_send_token(s));
		s->need_reconnect = false;
	}
	return true;
}

static inline bool quit(State *s) {
	if (!MASK_IS_SET(s->mask, M_QUIT))
		return add_error(s, "expected server to accept QUIT");
	return write_to_server(s, QUIT NL);
}

static inline void set_phase(State *s, Phase phase) {
	s->targ->flow_result->last_phase = phase;
}

static bool run_test(State *s) {
	set_phase(s, PH_init);

	my_log(s, "connecting...");

	RETURN_IF_NOK(connect_and_send_token(s));

	BARRIER;
	my_log(s, "connected with %" PRIuFAST16 " flow(s) for dl; %" PRIuFAST16 " flow(s) for ul", s->config->dl_num_flows, s->config->ul_num_flows);

	/* pretest downlink */
	set_phase(s, PH_pretest_dl);
	my_log(s, "pretest downlink start... (min %" PRIuFAST16 "s)", s->config->dl_pretest_duration_s);
	if (s->targ->do_downlink)
		RETURN_IF_NOK(do_pretest_downlink(s));
	BARRIER;
	my_log(s, "pretest downlink end.");

	/* rtt_tcp_payload */
	set_phase(s, PH_rtt_tcp_payload);
	my_log(s, "rtt_tcp_payload start... (%" PRIuFAST16 " times)", s->config->rtt_tcp_payload_num);
	if (s->targ->do_rtt_tcp_payload) /* only one thread does rtt_tcp_payload */
		RETURN_IF_NOK(do_rtt_tcp_payload(s));
	BARRIER;
	my_log(s, "rtt_tcp_payload end.");

	/* downlink */
	set_phase(s, PH_dl);
	my_log(s, "downlink test start... (%" PRIuFAST16 "s)", s->config->dl_duration_s);
	if (s->targ->do_downlink) {
		RETURN_IF_NOK(do_downlink(s));
		RETURN_IF_NOK(check_for_reconnect(s));
	}
	BARRIER;
	my_log(s, "downlink test end.");

	/* pretest uplink */
	set_phase(s, PH_pretest_ul);
	my_log(s, "pretest uplink start... (min %" PRIuFAST16 "s)", s->config->ul_pretest_duration_s);
	if (s->targ->do_uplink)
		RETURN_IF_NOK(do_prestest_uplink(s));
	BARRIER;
	my_log(s, "pretest uplink end.");

	/* uplink */
	set_phase(s, PH_ul);
	my_log(s, "uplink test start... (%" PRIuFAST16 "s)", s->config->ul_duration_s);
	if (s->targ->do_uplink) {
		RETURN_IF_NOK(do_uplink(s));
	} else
		BARRIER; // there is a BARRIER in do_uplink
	BARRIER;
	my_log(s, "uplink test end.");

	/* end */
	set_phase(s, PH_end);
	my_log(s, "disconnecting.");
	RETURN_IF_NOK(quit(s));
	return true;
}

void *run_test_thread_start(void *arg) {
	State state = { .targ = arg, .config = ((ThreadArg *) arg)->cfg };

	bool ok = run_test(&state);
	if (!ok || state.have_err)
		get_errors(&state, state.targ->flow_result->error, sizeof(state.targ->flow_result->error));

	disconnect(&state);

	print_errors(&state, stderr, true);

	free(state.buf_chunk);
	state.buf_chunk = NULL;

#if !defined(HAVE_ERR_REMOVE_THREAD_STATE_DEPRECATED) && \
  defined(HAVE_ERR_REMOVE_THREAD_STATE)
	ERR_remove_thread_state(NULL);
#endif

	return NULL;
}
