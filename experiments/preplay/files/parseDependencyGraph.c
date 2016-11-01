/* The following program is
used to replay dependency
trees based page load process
in todays browser

written by-- Mohd Rajiullah*/
#define _XOPEN_SOURCE 700

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>
#include <ctype.h>
#include <pthread.h>
#include <unistd.h>
#include <curl/curl.h>
#include <sys/time.h>
#include "cJSON.h"
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/queue.h>

pthread_mutex_t thread_count_mutex  = PTHREAD_MUTEX_INITIALIZER;
pthread_cond_t thread_count_cv      = PTHREAD_COND_INITIALIZER;
int thread_count                    = 0;

#define HTTP1 1
#define HTTP2 2
#define HTTPS 3
#define PHTTPGET 4
#define COOKIE_SIZE 512
#define NUM_HANDLES 1000
#define EASY_HANDLES 100
#define FIFO_BUFFER_SIZE 1024
#define STRING_BUFFER 1024
#define NANOSLEEP_MS_MULTIPLIER  1000000  // 1 millisecond = 1,000,000 Nanoseconds

#ifndef CURLPIPE_MULTIPLEX
/* This little trick will just make sure that we don't enable pipelining for
 * libcurls old enough to not have this symbol. It is _not_ defined to zero in
 * a recent libcurl header.
 */
#define CURLPIPE_MULTIPLEX 0
#endif

struct memory_chunk {
    char *memory;
    size_t size;
    int enabled;
};

struct sctp_pipe_data {
    uint32_t    id;
    uint32_t    path_len;
    uint32_t    cookie_len;
    uint32_t    header_len;
    uint32_t    payload_len;
    char        path[FIFO_BUFFER_SIZE];
} __attribute__ ((packed));

struct phttpget_request {
    pthread_mutex_t recv_mutex;
    pthread_cond_t recv_cv;
    uint8_t got_response;
    struct sctp_pipe_data pipe_data;
    TAILQ_ENTRY(phttpget_request) entries;
};

void createActivity(char *job_id);
int cJSON_HasArrayItem(cJSON *array, const char *string);
void onComplete(cJSON *obj_name);

int debug = 0;
int total_download_request_from_input=0;
double page_load_time = 0.0;
unsigned long page_size = 0;
int json_output = 1;
int object_count = 0;
int first_object = 0;
char *cookie_string;
int cookie_size = COOKIE_SIZE;
char *source_interface= NULL;
char *server = NULL;
char *testfile = NULL;
cJSON *json = NULL;
cJSON *this_objs_array = NULL;
cJSON *this_acts_array = NULL;
cJSON *map_start = NULL;
cJSON *map_complete = NULL;
cJSON *json_for_output=NULL;
cJSON *download_size=NULL;
cJSON *temp_download_size=NULL;
struct timeval start;
pthread_mutex_t lock;
void *curl_hnd[NUM_HANDLES];
CURL *easy[NUM_HANDLES];
CURLM *multi_handle = NULL;
int num_transfers = 0;
int protocol = HTTP1;
int transport_protocol = IPPROTO_TCP;
int request_count = 0;
int max_con = 0;
CURL *easyh1[EASY_HANDLES];
//CURL *easyh1;
int *worker_status;
//int worker_status[max_con] = {0, 0, 0, 0, 0, 0};

/* PHTTPGET STUFF BEGIN */
int fifo_in_fd = -1;
int fifo_out_fd = -1;
char *fifo_in_name = "/tmp/phttpget-out";
char *fifo_out_name = "/tmp/phttpget-in";
pthread_t phttpget_recv_thread;
pthread_t phttpget_program_thread;
uint32_t phttpget_request_counter = 0;
uint32_t phttpget_response_counter = 0;
pthread_mutex_t phttpget_write_mutex = PTHREAD_MUTEX_INITIALIZER;
TAILQ_HEAD(phttpget_request_queue, phttpget_request);
struct phttpget_request_queue phttpget_requests_pending;
/* PHTTPGET STUFF END */

static size_t
memory_callback(void *contents, size_t size, size_t nmemb, void *userp)
{
    size_t realsize = size * nmemb;
    struct memory_chunk *chunk = userp;

    if (!chunk->enabled) {
        return realsize;
    }

    chunk->memory = realloc(chunk->memory, chunk->size + realsize + 1);
    if (chunk->memory == NULL) {
        perror("realloc");
        return 0;
    }

    memcpy(&(chunk->memory[chunk->size]), contents, realsize);
    chunk->size += realsize;
    chunk->memory[chunk->size] = 0;
    return realsize;
}

int
init_worker()
{
    int i;
    int res;

    for (i = 0; i < max_con; i++) {
        easyh1[i] = curl_easy_init();
        if (!easyh1[i]) {
            return -1;
        }

        if ((res = curl_easy_setopt(easyh1[i], CURLOPT_TCP_NODELAY, 1L)) != CURLE_OK ||
	    (res= curl_easy_setopt(easyh1[i], CURLOPT_INTERFACE, source_interface)) != CURLE_OK) {
            fprintf(stderr, "cURL option error: %s\n", curl_easy_strerror(res));
            exit(EXIT_FAILURE);
        }

        /* some servers don't like requests that are made without a user-agent
         * field, so we provide one
         */
        if ((res = curl_easy_setopt(easyh1[i], CURLOPT_USERAGENT, "pReplay/0.1")) != CURLE_OK) {
            fprintf(stderr, "cURL option error: %s\n", curl_easy_strerror(res));
            exit(EXIT_FAILURE);
        }
    }
    return 0;
}

int
init_tls_worker()
{
    int i;
    int res;

    for (i = 0; i < max_con; i++) {
        easyh1[i] = curl_easy_init();
        if (!easyh1[i]) {
            return -1;
        }

        if ((res = curl_easy_setopt(easyh1[i], CURLOPT_TCP_NODELAY, 1L)) != CURLE_OK ||
            (res = curl_easy_setopt(easyh1[i], CURLOPT_HEADER, 0L)) != CURLE_OK ||
            (res = curl_easy_setopt(easyh1[i], CURLOPT_SSL_VERIFYPEER, 0L)) != CURLE_OK ||
	    (res= curl_easy_setopt(easyh1[i], CURLOPT_INTERFACE, source_interface)) != CURLE_OK ||
            (res = curl_easy_setopt(easyh1[i], CURLOPT_SSL_VERIFYHOST, 0L)) != CURLE_OK) {
            fprintf(stderr, "cURL option error: %s\n", curl_easy_strerror(res));
            exit(EXIT_FAILURE);
            }

            /* some servers don't like requests that are made without a user-agent
             * field, so we provide one */
        if ((res = curl_easy_setopt(easyh1[i], CURLOPT_USERAGENT, "pReplay/0.1")) != CURLE_OK) {
            fprintf(stderr, "cURL option error: %s\n", curl_easy_strerror(res));
            exit(EXIT_FAILURE);
        }
    }
    return 0;
}


void *
run_worker(void *arg)
{
    cJSON *obj_name = arg;
    char url[400];
    int j = cJSON_HasArrayItem(this_objs_array, cJSON_GetObjectItem(obj_name, "obj_id")->valuestring);
    int i = 0;
    int idle_worker_found = 0;
    cJSON *obj = NULL;
    cJSON *this_obj = NULL;
    struct memory_chunk chunk;
    int res = 0;
    double bytes = 0;
    long total_bytes = 0;
    long header_bytes = 0;
    double transfer_time = 0;
    double end_time = 0;
    struct timeval te;

    if (j != -1){
        obj = cJSON_GetArrayItem(this_objs_array, j);
        this_obj= cJSON_GetObjectItem(obj, cJSON_GetObjectItem(obj_name, "obj_id")->valuestring);

        if (protocol==HTTP1) {
            snprintf(url, sizeof(url), "%s%s%s", "http://", server, cJSON_GetObjectItem(this_obj, "path")->valuestring);
        } else if (protocol==HTTPS) {
            snprintf(url, sizeof(url), "%s%s%s", "https://", server, cJSON_GetObjectItem(this_obj, "path")->valuestring);
        }


        while (1) {
            pthread_mutex_lock(&lock);
            for (i = 0; i < max_con; i++) {
                if (worker_status[i] == 0){
                    idle_worker_found = 1;
                    worker_status[i] = 1;
                    break;
                }
            }
            pthread_mutex_unlock(&lock);
            if (idle_worker_found == 1) {
                break;
            }
        }


        if ((res = curl_easy_setopt(easyh1[i], CURLOPT_WRITEFUNCTION, memory_callback)) != CURLE_OK) {
            fprintf(stderr, "cURL option error: %s\n", curl_easy_strerror(res));
            exit(EXIT_FAILURE);
        }

        if ((res = curl_easy_setopt(easyh1[i], CURLOPT_WRITEDATA, (void *)&chunk)) != CURLE_OK) {
            fprintf(stderr, "cURL option error: %s\n", curl_easy_strerror(res));
            exit(EXIT_FAILURE);
        }


        chunk.memory = NULL;
        chunk.size = 0;
        chunk.enabled = 0;

        //char *url1="http://example.com";

        curl_easy_setopt(easyh1[i], CURLOPT_URL, url);
        //curl_easy_setopt(easyh1[i], CURLOPT_COOKIEFILE, "cookie.tmp");
        curl_easy_setopt(easyh1[i], CURLOPT_COOKIE, cookie_string);
        curl_easy_setopt(easyh1[i], CURLOPT_PRIVATE, url);
        chunk.size = 0;

        if ((res=curl_easy_perform(easyh1[i])) != CURLE_OK){
            //fprintf(stderr, "i= %d\n", i);
            perror("Curl error");
            exit(EXIT_FAILURE);
        }



        if ((res = curl_easy_getinfo(easyh1[i], CURLINFO_SIZE_DOWNLOAD, &bytes)) != CURLE_OK ||
            (res = curl_easy_getinfo(easyh1[i], CURLINFO_HEADER_SIZE, &header_bytes)) != CURLE_OK ||
            (res = curl_easy_getinfo(easyh1[i], CURLINFO_TOTAL_TIME, &transfer_time)) != CURLE_OK )
            {
            fprintf(stderr, "cURL error: %s\n", curl_easy_strerror(res));
            exit(EXIT_FAILURE);
        }

        worker_status[i] = 0;


        gettimeofday(&te,NULL);
        pthread_mutex_lock(&lock);
        page_load_time=end_time=((te.tv_sec-start.tv_sec)*1000+(double)(te.tv_usec-start.tv_usec)/1000);

        total_bytes=(long)bytes+header_bytes;
        page_size+=(long)bytes;

        object_count++;
        if (json_output == 1) {
            if (first_object == 0) {
                //printf("{\"S\":%ld,\"T\":%f}",total_bytes, transfer_time);
                cJSON_AddItemToArray(download_size,temp_download_size=cJSON_CreateObject());
                cJSON_AddNumberToObject(temp_download_size,"S",total_bytes);
                cJSON_AddNumberToObject(temp_download_size,"T",transfer_time);
                first_object = 1;
            } else {
                cJSON_AddItemToArray(download_size,temp_download_size=cJSON_CreateObject());
                cJSON_AddNumberToObject(temp_download_size,"S",total_bytes);
                cJSON_AddNumberToObject(temp_download_size,"T",transfer_time);
               // printf(",{\"S\":%ld,\"T\":%f}",total_bytes, transfer_time);
            }
        }
        pthread_mutex_unlock(&lock);

        if (debug == 1) {
            fprintf(stderr, "[%f] Object_size: %ld, transfer_time: %f\n",
                end_time,
                (long)bytes + header_bytes,
                transfer_time);
        }

        onComplete(obj_name);

        pthread_mutex_lock(&thread_count_mutex);
        thread_count--;
        /*if (thread_count==0){
            printf("BECOME 0 in run_worker\n");
            fflush(stdout);
        }*/

        pthread_cond_signal(&thread_count_cv);
        pthread_mutex_unlock(&thread_count_mutex);




    }
    return 0;
}

/*
check the total number of
parallel connections
*/

int
global_array_sum()
{
    int i = 0;
    int sum = 0;
    for (i = 0; i < max_con; i++){
        sum += worker_status[i];
    }
    return sum;
}

/* a handle to number lookup, highly ineffective when we do many
   transfers... */
static int
hnd2num(CURL *hnd)
{
    int i;
    for (i=0; i< num_transfers; i++){
        if (curl_hnd[i] == hnd) {
            return i;
        }
    }
    return 0; /* weird, but just a fail-safe */
}

void *
phttpget_start_programm() {
    char phttpget_argument[STRING_BUFFER];
    int phttpget_status = 0;

    /* try to run phttpget in background */
    snprintf(phttpget_argument, STRING_BUFFER, "HTTP_PIPE=YES ./phttpget %s > phttpget.log 2>&1", server);
    //snprintf(phttpget_argument, STRING_BUFFER, "HTTP_PIPE=YES ./phttpget %s", server);
    phttpget_status = system(phttpget_argument);

    fprintf(stderr, "phttpget terminated .... should not see me! - status : %d\n", phttpget_status);
    exit(EXIT_FAILURE);
    return 0;
}

/*
** read from incoming pipe and notify coresponding thread
*/
void *
phttpget_recv_handler()
{
    struct phttpget_request *request = NULL;
    struct sctp_pipe_data pipe_data_temp;
    uint8_t found = 0;
    ssize_t len = 0;
    ssize_t len_left = 0;
    char *bufptr = NULL;

    if (debug) {
        fprintf(stderr, "[%d][%s] - receiver thread started...\n", __LINE__, __func__);
    }

    while (1) {

        len_left = sizeof(struct sctp_pipe_data);
        bufptr = (char *) &pipe_data_temp;
        while (len_left > 0) {
            len = read(fifo_in_fd, bufptr + sizeof(struct sctp_pipe_data) - len_left, len_left);

            if (len == 0 || len == -1) {
                fprintf(stderr, "[%d][%s] - read failed\n", __LINE__, __func__);
                exit(EXIT_FAILURE);
            }

            len_left -= len;
        }

        /* search for thread */
        found = 0;
        TAILQ_FOREACH(request, &phttpget_requests_pending, entries) {
            if (request->pipe_data.id == pipe_data_temp.id) {
                found = 1;
                break;
            }
        }

        /* thread not found - this should not happen ... */
        if (!found) {
            fprintf(stderr, "[%d][%s] - request %d (%s) not found - fix logic!!\n", __LINE__, __func__, pipe_data_temp.id, pipe_data_temp.path);
            exit(EXIT_FAILURE);
        }

        /* copy pipe_data */
        /* felix : ugly - todo! ... */
        memcpy(&(request->pipe_data), &pipe_data_temp, sizeof(struct sctp_pipe_data));

        /*if (debug && !json_output) {
            fprintf(stderr, "handling response %d - %s\n", request->pipe_data.id, request->pipe_data.path);
        }*/

        /* notify waiting thread */
        pthread_mutex_lock(&(request->recv_mutex));
        request->got_response = 1;
        pthread_cond_signal(&(request->recv_cv));
        pthread_mutex_unlock(&(request->recv_mutex));
    }

    if (debug) {
        fprintf(stderr, "[%d][%s] - read failed - read retured %d (%s)\n", __LINE__, __func__, errno, strerror(errno));
    }

    return 0;
}

/*
** request an url via phttpget pipe
*/

void *
phttpget_request_url(void *arg)
{
    cJSON *obj_name = NULL;
    int i = 0;
    struct timeval te;
    struct timeval time_request;
    struct timeval time_response;
    double end_time = 0.0;
    uint32_t bytes = 0;
    long total_bytes = 0;
    long header_bytes = 0;
    double transfer_time = 0.0;
    struct phttpget_request *request = NULL;
    cJSON *obj = NULL;
    cJSON *this_obj = NULL;
    ssize_t len = 0;
    ssize_t len_left = 0;
    char *bufptr = NULL;

    obj_name = arg;
    i = cJSON_HasArrayItem(this_objs_array, cJSON_GetObjectItem(obj_name, "obj_id")->valuestring);

    if (i != -1) {
        obj = cJSON_GetArrayItem(this_objs_array, i);
        this_obj = cJSON_GetObjectItem(obj, cJSON_GetObjectItem(obj_name, "obj_id")->valuestring);

        /* prepare request and enqueue to queue */
        if ((request = malloc(sizeof(struct phttpget_request))) == NULL) {
            fprintf(stderr, "[%d][%s] - malloc failed\n", __LINE__, __func__);
            exit(EXIT_FAILURE);
        }
        memset(request, 0, sizeof(struct phttpget_request));

        /* initialize mutex for this thread */
        pthread_mutex_init(&(request->recv_mutex), NULL);
        pthread_cond_init(&(request->recv_cv), NULL);
        request->got_response = 0;

        /* fill pipe data */
        /* write url to buffer and save length */
        request->pipe_data.path_len = snprintf(
            request->pipe_data.path,
            FIFO_BUFFER_SIZE,
            "%s",
            cJSON_GetObjectItem(this_obj, "path")->valuestring
        );

        /* check pathlen */
        if (request->pipe_data.path_len <= 0) {
            fprintf(stderr, "[%d][%s] - pathlen <= 0\n", __LINE__, __func__);
            exit(EXIT_FAILURE);
        }

        pthread_mutex_lock(&phttpget_write_mutex);
        phttpget_request_counter++;
        request->pipe_data.id = phttpget_request_counter;
        request->pipe_data.cookie_len = cookie_size;
        /* enqueue request */
        TAILQ_INSERT_TAIL(&phttpget_requests_pending, request, entries);

        /* write request to pipe */
        len_left = sizeof(struct sctp_pipe_data);
        bufptr = (char *) &(request->pipe_data);
        while (len_left > 0) {
            len = write(fifo_out_fd, bufptr + sizeof(struct sctp_pipe_data) - len_left, len_left);
            if (len == -1 || len == 0) {
                fprintf(stderr, "[%d][%s] - write failed\n", __LINE__, __func__);
                //exit(EXIT_FAILURE);
                break;
            }
            len_left -= len;
        }
        gettimeofday(&time_request, 0);
        pthread_mutex_unlock(&phttpget_write_mutex);

        /*
        fprintf(stderr, "[%d][%s] - requesting %d : %s\n", __LINE__, __func__, request->pipe_data.id, request->pipe_data.path);
        */

        /* wait for receiver thread */
        pthread_mutex_lock(&(request->recv_mutex));
        while (!request->got_response) {
            pthread_cond_wait(&(request->recv_cv), &(request->recv_mutex));
        }
        pthread_mutex_unlock(&(request->recv_mutex));

        gettimeofday(&time_response, 0);
        transfer_time = ((time_response.tv_sec - time_request.tv_sec) * 1000 + (double)(time_response.tv_usec - time_request.tv_usec) / 1000);
        phttpget_response_counter++;

        /*
        if (debug && !json_output) {
            printf("####### PHTTPGET\n");
            printf("response: %d\n", phttpget_response_counter);
            printf("id      : %d\n", request->pipe_data.id);
            printf("payload : %d\n", request->pipe_data.size_payload);
            printf("header  : %d\n", request->pipe_data.size_header);
        }
        */

        /* cleanup and statistics */
        pthread_mutex_destroy(&(request->recv_mutex));
        pthread_cond_destroy(&(request->recv_cv));

        gettimeofday(&te, NULL);

        pthread_mutex_lock(&lock);
        page_load_time = end_time= ((te.tv_sec - start.tv_sec) * 1000 + (double)(te.tv_usec - start.tv_usec) / 1000);

        total_bytes = request->pipe_data.payload_len + request->pipe_data.header_len;
        page_size += request->pipe_data.payload_len;

        TAILQ_REMOVE(&phttpget_requests_pending, request, entries);
        object_count++;

        if (json_output == 1) {
            if (first_object == 0) {
                cJSON_AddItemToArray(download_size,temp_download_size=cJSON_CreateObject());
                cJSON_AddNumberToObject(temp_download_size,"S",total_bytes);
                cJSON_AddNumberToObject(temp_download_size,"T",transfer_time);
                first_object = 1;
            } else {
                cJSON_AddItemToArray(download_size,temp_download_size=cJSON_CreateObject());
                cJSON_AddNumberToObject(temp_download_size,"S",total_bytes);
                cJSON_AddNumberToObject(temp_download_size,"T",transfer_time);
            }
        }

        if (debug) {
            fprintf(stderr,"[%f] Object_size: %u, transfer_time: %f\n", end_time, request->pipe_data.payload_len + request->pipe_data.header_len, transfer_time);
        }

        free(request);
        pthread_mutex_unlock(&lock);

        onComplete(obj_name);

        /* reduce thread_count and signal finish */
        pthread_mutex_lock(&thread_count_mutex);
        thread_count--;
        pthread_cond_signal(&thread_count_cv);
        pthread_mutex_unlock(&thread_count_mutex);

    } else {
        if (debug) {
            fprintf(stderr, "[%d][%s] - object not found - fix file!!!...\n", __LINE__, __func__);
            exit(EXIT_FAILURE);
        }
    }
    return 0;
}

void *
request_url(void *arg)
{
    cJSON *obj_name = arg;
    char url[400];
    int i = cJSON_HasArrayItem(this_objs_array, cJSON_GetObjectItem(obj_name, "obj_id")->valuestring);
    struct timeval te;
    double end_time;

    if (i != -1){
        cJSON *obj= cJSON_GetArrayItem(this_objs_array, i);
        cJSON * this_obj= cJSON_GetObjectItem(obj, cJSON_GetObjectItem(obj_name, "obj_id")->valuestring);
        int still_running = 0; /* keep number of running handles */
        CURL *eh;
        FILE *out;
        char filename[128];
        int num=0;
        double bytes = 0.0;
        long total_bytes = 0;
        long header_bytes = 0;
        double transfer_time = 0.0;
        int res = 0;


        snprintf(url, sizeof url,"%s%s%s%s","https://", server, ":8000",cJSON_GetObjectItem(this_obj,"path")->valuestring);
        //if (debug==1 && json_output==0)
        //printf("URL: %s\n",url);
        //printf("when_comp_start--: %d\n",cJSON_GetObjectItem(this_obj,"when_comp_start")->valueint);

        gettimeofday(&te, NULL);
        end_time = ((te.tv_sec - start.tv_sec) * 1000 + (double)(te.tv_usec - start.tv_usec) / 1000);
        if (debug) {
            fprintf(stderr,"[%f] URL: %s\n", end_time, url);
        }


        eh = curl_easy_init();
        /* set options */

        /* set source interface */
        curl_easy_setopt(eh, CURLOPT_INTERFACE, source_interface);
        
	snprintf(filename, 128, "dl-%d", num);
        out = fopen(filename, "wb");
        // write to this file
        curl_easy_setopt(eh, CURLOPT_WRITEDATA, out);

        /* send all data to this function  */
        //curl_easy_setopt(hnd, CURLOPT_WRITEFUNCTION, write_data);

         /*Nagle off please */
        curl_easy_setopt(eh, CURLOPT_TCP_NODELAY, 1L);

        /* set the same URL */
        curl_easy_setopt(eh, CURLOPT_URL, url);

        /* send it verbose for max debuggaility */
        //curl_easy_setopt(hnd, CURLOPT_VERBOSE, 1L);
        //curl_easy_setopt(hnd, CURLOPT_DEBUGFUNCTION, my_trace);

        /* HTTP/2 please */
        curl_easy_setopt(eh, CURLOPT_HTTP_VERSION, CURL_HTTP_VERSION_2_0);

        /* we use a self-signed test server, skip verification during debugging */
        curl_easy_setopt(eh, CURLOPT_SSL_VERIFYPEER, 0L);
        curl_easy_setopt(eh, CURLOPT_SSL_VERIFYHOST, 0L);

#if (CURLPIPE_MULTIPLEX > 0)
        /* wait for pipe connection to confirm */
        curl_easy_setopt(eh, CURLOPT_PIPEWAIT, 1L);
#endif

        /* add the individual transfer */
        curl_multi_add_handle(multi_handle, eh);


        curl_multi_setopt(multi_handle, CURLMOPT_PIPELINING, CURLPIPE_MULTIPLEX);

        pthread_mutex_lock(&lock);

        /* we start some action by calling perform right away */
        curl_multi_perform(multi_handle, &still_running);
        pthread_mutex_unlock(&lock);

        do {
            struct timeval timeout;
            int rc; /* select() return code */
            CURLMcode mc; /* curl_multi_fdset() return code */

            fd_set fdread;
            fd_set fdwrite;
            fd_set fdexcep;
            int maxfd = -1;


            long curl_timeo = -1;

            FD_ZERO(&fdread);
            FD_ZERO(&fdwrite);
            FD_ZERO(&fdexcep);

            /* set a suitable timeout to play around with */
            timeout.tv_sec = 1;
            timeout.tv_usec = 0;

            curl_multi_timeout(multi_handle, &curl_timeo);
            if (curl_timeo >= 0) {
                timeout.tv_sec = curl_timeo / 1000;
                if (timeout.tv_sec > 1) {
                    timeout.tv_sec = 1;
                } else {
                    timeout.tv_usec = (curl_timeo % 1000) * 1000;
                }
            }

            /* get file descriptors from the transfers */
            mc = curl_multi_fdset(multi_handle, &fdread, &fdwrite, &fdexcep, &maxfd);

            if (mc != CURLM_OK) {
                fprintf(stderr, "curl_multi_fdset() failed, code %d.\n", mc);
                break;
            }

            /* On success the value of maxfd is guaranteed to be >= -1. We call
               select(maxfd + 1, ...); specially in case of (maxfd == -1) there are
               no fds ready yet so we call select(0, ...) --or Sleep() on Windows--
               to sleep 100ms, which is the minimum suggested value in the
               curl_multi_fdset() doc. */

            if (maxfd == -1) {
#ifdef _WIN32
                Sleep(100);
                rc = 0;
#else
                /* Portable sleep for platforms other than Windows. */
                struct timeval wait = { 0, 100 * 1000 }; /* 100ms */
                rc = select(0, NULL, NULL, NULL, &wait);
#endif
            } else {
                /* Note that on some platforms 'timeout' may be modified by select().
                   If you need access to the original value save a copy beforehand. */
                rc = select(maxfd+1, &fdread, &fdwrite, &fdexcep, &timeout);
            }
                switch (rc) {
                    case -1:
                        /* select error */
                        break;
                    case 0:
                    default:
                        /* timeout or readable/writable sockets */
                        pthread_mutex_lock(&lock);
                        curl_multi_perform(multi_handle, &still_running);
                        pthread_mutex_unlock(&lock);
                        break;
                }
        } while (still_running);



        if ((res = curl_easy_getinfo(eh, CURLINFO_SIZE_DOWNLOAD, &bytes)) != CURLE_OK ||
            (res = curl_easy_getinfo(eh, CURLINFO_HEADER_SIZE, &header_bytes)) != CURLE_OK ||
            (res = curl_easy_getinfo(eh, CURLINFO_TOTAL_TIME, &transfer_time)) != CURLE_OK ) {
                fprintf(stderr, "cURL error: %s\n", curl_easy_strerror(res));
            }


        gettimeofday(&te, NULL);
        pthread_mutex_lock(&lock);
        page_load_time = end_time= ((te.tv_sec - start.tv_sec) * 1000 + (double)(te.tv_usec - start.tv_usec) / 1000);
        total_bytes = (long)bytes + header_bytes;
        page_size += (long)bytes;

        object_count++;
        pthread_mutex_unlock(&lock);

        if (json_output == 1) {
            if (first_object == 0) {
                //printf("{\"S\":%ld,\"T\":%f}",total_bytes, transfer_time);
                cJSON_AddItemToArray(download_size,temp_download_size=cJSON_CreateObject());
                cJSON_AddNumberToObject(temp_download_size,"S",total_bytes);
                cJSON_AddNumberToObject(temp_download_size,"T",transfer_time);
                first_object = 1;
            } else {
                cJSON_AddItemToArray(download_size,temp_download_size=cJSON_CreateObject());
                cJSON_AddNumberToObject(temp_download_size,"S",total_bytes);
                cJSON_AddNumberToObject(temp_download_size,"T",transfer_time);
               // printf(",{\"S\":%ld,\"T\":%f}",total_bytes, transfer_time);
            }
        }
        if (debug) {
            fprintf(stderr,"[%f] Object_size: %ld, transfer_time: %f\n", end_time, (long)bytes+header_bytes, transfer_time);
        }

        onComplete(obj_name);
        pthread_mutex_lock(&thread_count_mutex);

        thread_count--;
        /*if (thread_count==0){
            printf("BECOME 0 in request_url\n");
                fflush(stdout);
        }*/

        pthread_cond_signal(&thread_count_cv);
        pthread_mutex_unlock(&thread_count_mutex);
    }
    return 0;
}

int
cJSON_HasArrayItem(cJSON *array, const char *string)
{
    cJSON *obj = NULL;
    int i;

    for (i = 0; i < cJSON_GetArraySize(array); i++) {
        obj = cJSON_GetArrayItem(array, i);
        if (cJSON_HasObjectItem(obj, string)) {
            return i;
        }
    }
    return -1;
}

int
checkDependedActivities(char *id)
{
    int is_all_complete = 1;
    int i = cJSON_HasArrayItem(this_acts_array, id);
    int j = 0;
    if (i != -1){
        cJSON * objs = cJSON_GetArrayItem(this_acts_array, i);
        cJSON * obj = cJSON_GetObjectItem(objs, id);
        cJSON *deps = cJSON_GetObjectItem(obj, "deps");
        for (j = 0; j < cJSON_GetArraySize(deps); j++){
            cJSON * dep = cJSON_GetArrayItem(deps, j);
            if (cJSON_GetObjectItem(dep, "time")->valueint < 0) {
                if (cJSON_HasObjectItem(map_complete, cJSON_GetObjectItem(dep, "id")->valuestring)) {
                    if (cJSON_GetObjectItem(map_complete, cJSON_GetObjectItem(dep, "id")->valuestring)->valueint != 1) {
                        is_all_complete = 0;
                        break;
                    }
                } else {
                    is_all_complete = 0;
                    break;
                }
            } else {
                if (cJSON_HasObjectItem(map_start, cJSON_GetObjectItem(dep, "id")->valuestring)) {
                    if (cJSON_GetObjectItem(map_start, cJSON_GetObjectItem(dep, "id")->valuestring)->valueint != 1) {
                        is_all_complete=0;
                        break;
                    }
                } else {
                    is_all_complete = 0;
                    break;
                }
            }
        }
    }
    return is_all_complete;
}

void
onComplete(cJSON *obj_name)
{
    struct timeval te;
    int i = 0;
    gettimeofday(&te, NULL);
    double end_time = ((te.tv_sec - start.tv_sec) * 1000 + (double)(te.tv_usec - start.tv_usec) / 1000);
    pthread_mutex_lock(&lock);
    page_load_time=end_time=((te.tv_sec-start.tv_sec)*1000+(double)(te.tv_usec-start.tv_usec)/1000);
    pthread_mutex_unlock(&lock);
    cJSON_AddNumberToObject(obj_name, "ts_e", end_time);

    if (debug) {
        fprintf(stderr,"=== [onComplete][%f] {\"id\":%s,\"type\":%s,\"is_started\":%d,\"ts_s\":%f,\"ts_e\":%f}\n",
            end_time,
            cJSON_GetObjectItem(obj_name,"id")->valuestring,
            cJSON_GetObjectItem(obj_name,"type")->valuestring,
            cJSON_GetObjectItem(obj_name,"is_started")->valueint,
            cJSON_GetObjectItem(obj_name,"ts_s")->valuedouble,
            cJSON_GetObjectItem(obj_name,"ts_e")->valuedouble);
    }

    pthread_mutex_lock(&lock);
    // TO DO update task completion maps
    if (!cJSON_HasObjectItem(map_complete, cJSON_GetObjectItem(obj_name, "id")->valuestring)) {
        cJSON_AddNumberToObject(map_complete, cJSON_GetObjectItem(obj_name, "id")->valuestring, 1);
    } else {
        fprintf(stderr, "dublicate object - fix logic!\n");
        exit(EXIT_FAILURE);
    }
    pthread_mutex_unlock(&lock);

    // Check whether should trigger dependent activities when 'time' == -1
    if (cJSON_HasObjectItem(obj_name, "triggers")) {
        cJSON *triggers = cJSON_GetObjectItem(obj_name, "triggers");
        for (i = 0; i < cJSON_GetArraySize(triggers); i++) {
            cJSON *trigger = cJSON_GetArrayItem(triggers, i);
            if (cJSON_GetObjectItem(trigger,"time")->valueint == -1) {
                // Check whether all activities that trigger.id depends on are finished
                if (checkDependedActivities(cJSON_GetObjectItem(trigger, "id")->valuestring)) {
                    createActivity(cJSON_GetObjectItem(trigger, "id")->valuestring);
                }
            }
        }
    }
}

void
setTimeout(int ms, char *s)
{
    struct timeval ts;
    struct timeval te;
    struct timespec tim;
    struct timespec tim2;

    gettimeofday(&ts,NULL);
    if (debug) {
        fprintf(stderr,"Timeout starts (obj id %s): %f ms - sleeping for %d ms\n",
            s,
            ((ts.tv_sec - start.tv_sec) * 1000 + (double)(ts.tv_usec - start.tv_usec) / 1000),
            ms
        );
    }

    tim.tv_sec = ms / 1000;
    tim.tv_nsec = (ms % 1000) * NANOSLEEP_MS_MULTIPLIER;
    nanosleep(&tim, &tim2);

    gettimeofday(&te, NULL);
    if (debug) {
        fprintf(stderr,"Timeout ends (obj id %s): %f ms \n",
            s,
            ((te.tv_sec - start.tv_sec) * 1000 + (double)(te.tv_usec - start.tv_usec) / 1000)
        );
    }
}

void
*compActivity(void *arg)
{
    cJSON *obj_name = arg;
    //printf("Time out value: %d, object name: %s\n",cJSON_GetObjectItem(obj_name,"time")->valueint, cJSON_GetObjectItem(obj_name,"obj_id")->valuestring);
    setTimeout(cJSON_GetObjectItem(obj_name, "time")->valueint, cJSON_GetObjectItem(obj_name, "obj_id")->valuestring);
    onComplete(obj_name);
    pthread_mutex_lock(&thread_count_mutex);
    thread_count--;
    /*if (thread_count==0){
        printf("BECOME 0 in compActivity\n");
    fflush(stdout);
    }*/

    pthread_cond_signal(&thread_count_cv);
    pthread_mutex_unlock(&thread_count_mutex);
    return ((void*)0);
}

void
*createActivityAfterTimeout(void *arg)
{
    cJSON *trigger = arg;
    setTimeout(cJSON_GetObjectItem(trigger, "time")->valueint, cJSON_GetObjectItem(trigger, "id")->valuestring);
    createActivity(cJSON_GetObjectItem(trigger, "id")->valuestring);

    pthread_mutex_lock(&thread_count_mutex);
    thread_count--;
    if (thread_count==0){
        printf("BECOME 0 in createActivityAfterTimeout\n");
        fflush(stdout);
    }

    pthread_cond_signal(&thread_count_cv);
    pthread_mutex_unlock(&thread_count_mutex);
    return ((void*)0);
}


void
createActivity(char *job_id)
{
    pthread_t tid1, tid2;
    int error;
    struct timeval ts_s;
    cJSON * obj;
    cJSON * obj_name;
    uint8_t duplicate_job = 0;


    int i = cJSON_HasArrayItem(this_acts_array, job_id);

    if (i != -1) {
        obj = cJSON_GetArrayItem(this_acts_array, i);
        obj_name = cJSON_GetObjectItem(obj, job_id);

        pthread_mutex_lock(&lock);
        if (cJSON_HasObjectItem(obj_name, "is_started")){
            if (cJSON_GetObjectItem(obj_name, "is_started")->valueint == 1) {
                //fprintf(stderr, "%s : activity already started ... fix logic?\n", cJSON_GetObjectItem(obj_name, "obj_id")->valuestring);
                //exit(EXIT_FAILURE);
                duplicate_job = 1;
            } else {
                cJSON_GetObjectItem(obj_name,"is_started")->valueint = 1;
            }
        } else {
            cJSON_AddNumberToObject(obj_name,"is_started",1);
        }
        pthread_mutex_unlock(&lock);

        if (duplicate_job) {
            return;
        }


        gettimeofday(&ts_s, NULL);
        cJSON_AddNumberToObject(
            obj_name,
            "ts_s",
            ((ts_s.tv_sec - start.tv_sec) * 1000 + (double)(ts_s.tv_usec - start.tv_usec) / 1000)
        );

        if (debug) {
            fprintf(stderr,"Object id: %s, type: %s started at %f ms\n",
                cJSON_GetObjectItem(obj_name,"obj_id")->valuestring,
                cJSON_GetObjectItem(obj_name,"type")->valuestring,
                ((ts_s.tv_sec - start.tv_sec) * 1000 + (double)(ts_s.tv_usec - start.tv_usec) / 1000)
            );
        }

        if (cJSON_strcasecmp(cJSON_GetObjectItem(obj_name, "type")->valuestring, "download") == 0) {
            i = cJSON_HasArrayItem(this_objs_array, cJSON_GetObjectItem(obj_name, "obj_id")->valuestring);

            if (i != -1) {
                obj= cJSON_GetArrayItem(this_objs_array, i);
                if (protocol == HTTP2) {
                    pthread_mutex_lock(&thread_count_mutex);
                    thread_count++;
                    pthread_cond_signal(&thread_count_cv);
                    pthread_mutex_unlock(&thread_count_mutex);
                    error = pthread_create(&tid2, NULL, request_url, (void *) obj_name);
                    if (error) {
                        fprintf(stderr, "Couldn't run thread number %d, errno %d\n", i, error);
                        exit(EXIT_FAILURE);
                    }
                    pthread_detach(tid2);

                } else if (protocol == HTTP1 || protocol == HTTPS) {
                    while (1) {
                        if (global_array_sum() < max_con) {
                            pthread_mutex_lock(&thread_count_mutex);
                            thread_count++;
                            pthread_cond_signal(&thread_count_cv);
                            pthread_mutex_unlock(&thread_count_mutex);
                            error = pthread_create(&tid2,NULL,run_worker,(void *)obj_name);
                            if (error) {
                                fprintf(stderr, "Couldn't run thread number %d, errno %d\n", i, error);
                                exit(EXIT_FAILURE);
                            }
                            pthread_detach(tid2);
                            break;
                        }
                    }
                } else if (protocol == PHTTPGET) {
                    pthread_mutex_lock(&thread_count_mutex);
                    thread_count++;
                    pthread_cond_signal(&thread_count_cv);
                    pthread_mutex_unlock(&thread_count_mutex);
                    error = pthread_create(&tid2, NULL, phttpget_request_url, (void *) obj_name);
                    if (error) {
                        fprintf(stderr, "Couldn't run thread number %d, errno %d\n", i, error);
                        exit(EXIT_FAILURE);
                    }
                    pthread_detach(tid2);
                }
            }
        } else {
            // For comp activity
            pthread_mutex_lock(&thread_count_mutex);
            thread_count++;
            pthread_cond_signal(&thread_count_cv);
            pthread_mutex_unlock(&thread_count_mutex);
            error = pthread_create(&tid1, NULL, compActivity, (void *) obj_name);
            if (error) {
                fprintf(stderr, "Couldn't run thread number %d, errno %d\n", i, error);
                exit(EXIT_FAILURE);
            }
            pthread_detach(tid1);
        }
        // TO DO update task start maps
        pthread_mutex_lock(&lock);
        if (!cJSON_HasObjectItem(map_start, cJSON_GetObjectItem(obj_name, "id")->valuestring)) {
            cJSON_AddNumberToObject(map_start, cJSON_GetObjectItem(obj_name, "id")->valuestring,1);
        }
        pthread_mutex_unlock(&lock);

        // Check whether should trigger dependent activities when 'time' != -1
        if (cJSON_HasObjectItem(obj_name, "triggers")) {
            cJSON *triggers = cJSON_GetObjectItem(obj_name, "triggers");
            for (i = 0; i < cJSON_GetArraySize(triggers); i++) {
                cJSON *trigger = cJSON_GetArrayItem(triggers, i);
                if (cJSON_GetObjectItem(trigger, "time")->valueint != -1) {
                    // Check whether all activities that trigger.id depends on are finished
                    if (checkDependedActivities(cJSON_GetObjectItem(trigger, "id")->valuestring)){
                        pthread_mutex_lock(&thread_count_mutex);
                        thread_count++;
                        pthread_cond_signal(&thread_count_cv);
                        pthread_mutex_unlock(&thread_count_mutex);
                        error = pthread_create(&tid2, NULL, createActivityAfterTimeout, (void *) trigger);
                        if (error) {
                            fprintf(stderr, "Couldn't run thread number %d, errno %d\n", i, error);
                            exit(EXIT_FAILURE);
                        }
                        pthread_detach(tid2);
                    }
                }
            }
        }
    }
}


void
run()
{
    map_start = cJSON_CreateObject();
    map_complete = cJSON_CreateObject();

    if (protocol == HTTP1){
        init_worker();
    } else if (protocol == HTTPS){
        init_tls_worker();
    }
    gettimeofday(&start, NULL);

    createActivity(cJSON_GetObjectItem(json,"start_activity")->valuestring);

    pthread_mutex_lock(&thread_count_mutex);
    while (thread_count > 0) {
        pthread_cond_wait(&thread_count_cv, &thread_count_mutex);
    }
    pthread_mutex_unlock(&thread_count_mutex);

    if (total_download_request_from_input!=object_count)
    {
        fprintf(stderr, "Download error\n");
        EXIT_FAILURE;
    }else{
        cJSON_AddNumberToObject(json_for_output,"num_objects",object_count);
        cJSON_AddNumberToObject(json_for_output,"PLT",page_load_time);
        cJSON_AddNumberToObject(json_for_output,"page_size",page_size);

        char *out;
        out=cJSON_Print(json_for_output);
        cJSON_Delete(json_for_output);
        printf("%s\n", out);
        free(out);
    }

    /*printf("],\"num_objects\":%d,\"PLT\":%f, \"page_size\":%ld}\n",
        object_count,
        page_load_time,
        page_size
    );*/


}

void
doit(char *text)
{
   json = cJSON_Parse(text);
   int i = 0;
   int j = 0;
   char *out = NULL;
   char *a1 = NULL;
   char dep_id[16];
   int deps_length = 0;
   cJSON *comp = NULL;
   cJSON *this_objs = NULL;
   cJSON *temp1 = NULL;
   cJSON *temp2 = NULL;
   cJSON *this_acts = NULL;
   cJSON *comps = NULL;
   cJSON *root = NULL;
   cJSON *b1 = NULL;
   cJSON *b2 = NULL;
   cJSON *temp = NULL;
   cJSON *temp_array = NULL;

   if (!json) {
       printf("Error before: [%s]\n", cJSON_GetErrorPtr());
   }


   cJSON *objs = cJSON_GetObjectItem(json, "objs");
   if (!objs) {
       printf("Error before: [%s]\n", cJSON_GetErrorPtr());
   }

   cJSON *deps = cJSON_GetObjectItem(json,"deps");
   if (!deps) {
       printf("Error before: [%s]\n", cJSON_GetErrorPtr());
   }

   this_objs_array = cJSON_CreateArray();
   this_acts_array = cJSON_CreateArray();

   for (i = 0; i < cJSON_GetArraySize(objs); i++)
        {
        cJSON * obj = cJSON_GetArrayItem(objs, i);
        /* Handle array of comp */
        comps = cJSON_GetObjectItem(obj, "comps");
        if (!comps) {
            printf("Error before: [%s]\n",cJSON_GetErrorPtr());
        }

        /* Handle download */
        cJSON * download = cJSON_GetObjectItem(obj, "download");
        cJSON_AddStringToObject(download, "obj_id",cJSON_GetObjectItem(obj, "id")->valuestring);
        cJSON_DeleteItemFromObject(download, "type");
        cJSON_AddStringToObject(download, "type", "download");
        cJSON_AddStringToObject(download, "mime", "download");

        /* Index obj by object id */

        temp1 = cJSON_CreateObject();
        cJSON_AddStringToObject(temp1, "id",cJSON_GetObjectItem(obj, "id")->valuestring);
        cJSON_AddStringToObject(temp1, "host",cJSON_GetObjectItem(obj, "host")->valuestring);
        cJSON_AddStringToObject(temp1, "path",cJSON_GetObjectItem(obj, "path")->valuestring);
        if (cJSON_GetObjectItem(obj,"path")->valuestring[0]!='\0'){
            total_download_request_from_input++;
        }
        cJSON_AddNumberToObject(temp1, "when_comp_start", cJSON_GetObjectItem(obj, "when_comp_start")->valueint);
        cJSON_AddItemReferenceToObject(temp1, "download",download);
        cJSON_AddItemReferenceToObject(temp1, "comps",comps);

        this_objs = cJSON_CreateObject();
        cJSON_AddItemToObject(this_objs, cJSON_GetObjectItem(obj, "id")->valuestring, temp1);
        cJSON_AddItemToArray(this_objs_array, this_objs);

        this_acts=cJSON_CreateObject();
        cJSON_AddItemToObject(this_acts,cJSON_GetObjectItem(download,"id")->valuestring,download);
        cJSON_AddItemToArray(this_acts_array,this_acts);


        /* printf("||||||\n");
        out=cJSON_Print(obj);
        printf("%s\n",out);
        printf("||||||\n"); */

        for (j = 0; j < cJSON_GetArraySize(comps); j++) {
            comp = cJSON_GetArrayItem(comps, j);
            cJSON_AddStringToObject(comp, "obj_id",cJSON_GetObjectItem(obj, "id")->valuestring);
             /*Add natural dependency
                     Depends on download activity
                     Depends on its previous comp activity*/
            if (j == 0){
                a1 = cJSON_GetObjectItem(download, "id")->valuestring;
            } else {
                a1 = cJSON_GetObjectItem(cJSON_GetArrayItem(comps, j - 1),"id")->valuestring;
            }

            root = cJSON_CreateObject();
            deps_length = cJSON_GetArraySize(deps);
            snprintf(dep_id, 16, "dep%d", deps_length+1);
            cJSON_AddStringToObject(root, "id", dep_id);
            cJSON_AddStringToObject(root, "a1", a1);
            cJSON_AddStringToObject(root, "a2", cJSON_GetObjectItem(comp, "id")-> valuestring);
            cJSON_AddNumberToObject(root, "time", -1);
            cJSON_AddItemToArray(deps,root);
             //out=cJSON_Print(deps);

            temp2 = cJSON_CreateObject();

            cJSON_AddStringToObject(temp2, "id", cJSON_GetObjectItem(comp, "id")->valuestring);


            // cJSON_AddStringToObject(temp2,"type",cJSON_GetObjectItem(comp,"type")->valuestring);
            //printf ("==%s==\n",cJSON_GetObjectItem(comp,"type")->valuestring);
            if (cJSON_GetObjectItem(comp, "type")->valuestring != NULL) {
                cJSON_AddStringToObject(temp2, "type", cJSON_GetObjectItem(comp, "type")->valuestring);
            } else {
                cJSON_AddNumberToObject(temp2, "type", cJSON_GetObjectItem(comp, "type")->valueint);
            }
             //printf("%s\n",a1);

            cJSON_AddNumberToObject(temp2, "time", cJSON_GetObjectItem(comp, "time")->valueint);
            cJSON_AddStringToObject(temp2, "obj_id", cJSON_GetObjectItem(obj, "id")->valuestring);

            this_acts = cJSON_CreateObject();

            cJSON_AddItemToObject(this_acts, cJSON_GetObjectItem(comp, "id")->valuestring,temp2);
            cJSON_AddItemToArray(this_acts_array, this_acts);
        }
    }

    /* Add dependencies to activities */
    for (i = 0; i < cJSON_GetArraySize(deps); i++){
        cJSON * dep = cJSON_GetArrayItem(deps,i);

        for (j = 0; j < cJSON_GetArraySize(this_acts_array); j++){
            cJSON * obj = cJSON_GetArrayItem(this_acts_array, j);

            if (!obj) {
                printf("Error before: [%s]\n",cJSON_GetErrorPtr());
            }


            //printf("=I am here=\n");

            // out=cJSON_Print(dep);
            // printf("%s\n",out);

            out = cJSON_Print(obj);
            //printf("%s\n",out);

            char *Cidd;
            //sprintf(Cid,"%.9s",out);
            Cidd = strtok(out, ":");
            char* Cid = Cidd+4;
            Cid[strlen(Cid)-1] = 0;

            char *pch = strstr(Cid, cJSON_GetObjectItem(dep, "a1")->valuestring);


            if (pch && (strlen(Cid) == strlen(cJSON_GetObjectItem(dep, "a1")->valuestring))) {
                b1 = cJSON_GetObjectItem(obj, cJSON_GetObjectItem(dep, "a1")->valuestring);
            }

            char *pch1 = strstr(Cid, cJSON_GetObjectItem(dep, "a2")->valuestring);

            if (pch1 && (strlen(Cid) == strlen(cJSON_GetObjectItem(dep, "a2")->valuestring))) {
                b2 = cJSON_GetObjectItem(obj, cJSON_GetObjectItem(dep, "a2")->valuestring);
            }

            free(Cidd);
        }

        /* Add to a2 that 'a2 depends on a1' */

        temp = cJSON_CreateObject();
        temp_array = cJSON_CreateArray();
        cJSON_AddStringToObject(temp, "id", cJSON_GetObjectItem(b1, "id")->valuestring);
        cJSON_AddNumberToObject(temp, "time", cJSON_GetObjectItem(dep, "time")->valueint);
        if (cJSON_HasObjectItem(b2,"deps")) {
            cJSON_AddItemToArray(cJSON_GetObjectItem(b2, "deps"),temp);
            free(temp_array);
        } else {
            cJSON_AddItemToArray(temp_array, temp);
            cJSON_AddItemToObject(b2, "deps", temp_array);
        }

        temp = cJSON_CreateObject();
        temp_array = cJSON_CreateArray();
        cJSON_AddStringToObject(temp, "id", cJSON_GetObjectItem(b2, "id")->valuestring);
        cJSON_AddNumberToObject(temp, "time", cJSON_GetObjectItem(dep, "time")->valueint);

        if (cJSON_HasObjectItem(b1, "triggers")) {
            cJSON_AddItemToArray(cJSON_GetObjectItem(b1, "triggers"), temp);
            free(temp_array);
        } else {
            cJSON_AddItemToArray(temp_array, temp);
            cJSON_AddItemToObject(b1,"triggers", temp_array);
        }
    }
    if (debug) {
        fprintf(stderr,"===[objects]");
        out = cJSON_Print(this_objs_array);
        fprintf(stderr,"%s\n", out);
        free(out);

        fprintf(stderr,"===[activities]");
        out=cJSON_Print(this_acts_array);
        fprintf(stderr,"%s\n", out);
        free(out);
    }

    run();
}


/* Read a file, parse, render back, etc. */
void
dofile(char *filename)
{
    FILE *f;
    long len;
    char *data;
    ssize_t result;

    f = fopen(filename,"rb");
    if (f == NULL) {
        perror("Error opening file\n");
        exit(EXIT_FAILURE);
    }

    fseek(f, 0, SEEK_END);
    len = ftell(f);
    fseek(f, 0, SEEK_SET);

    data = (char*)malloc(len + 1);
    if (data == NULL) {
        fprintf(stderr, "malloc failed\n");
        exit(EXIT_FAILURE);
    }

    result = fread(data, 1, len, f);
    if (result != len) {
        fprintf(stderr, "fread failed\n");
        exit(EXIT_FAILURE);
    }

    fclose(f);
    doit(data);
    free(data);
}


int main (int argc, char * argv[]) {
    if (argc < 4 || argc > 7){
        fprintf(stderr,"usage: %s source_interface server testfile [http|https|http2|phttpget] [max-connections] [cookie-size]\n", argv[0]);
        exit(EXIT_FAILURE);
    }
    
    source_interface=argv[1];
    server = argv[2];
    testfile = argv[3];

    /* User defined a protocol via arguments - HTTP1 is default */
    if (argc > 4) {
        if (strcmp(argv[4], "http2") == 0) {
            protocol = HTTP2;
        } else if (strcmp(argv[4],"http") == 0) {
            protocol = HTTP1;
        } else if (strcmp(argv[4],"https") == 0) {
            protocol = HTTPS;
        } else if (strcmp(argv[4],"phttpget") == 0) {
            protocol = PHTTPGET;

            TAILQ_INIT(&phttpget_requests_pending);

            pthread_create(&phttpget_program_thread, NULL, phttpget_start_programm, NULL);
            pthread_detach(phttpget_program_thread);

            /* create pipes for phttpget */
            mkfifo(fifo_out_name, 0666);
            mkfifo(fifo_in_name, 0666);
            fifo_out_fd = open(fifo_out_name, O_WRONLY);
            fifo_in_fd = open(fifo_in_name, O_RDONLY);

            /* start receiver thread */
            pthread_create(&phttpget_recv_thread, NULL, phttpget_recv_handler, NULL);
            pthread_detach(phttpget_recv_thread);
        } else {
            fprintf(stderr, "Protocol not supported\n");
            exit(EXIT_FAILURE);
        }
    }

    /* User defined max parallel conn */
    if (argc > 5){
        max_con = strtol(argv[5], NULL, 10);
        if (max_con < 1){
            fprintf(stderr, "Invalid number of connections\n");
            exit(EXIT_FAILURE);
        }
        worker_status = malloc(max_con * sizeof(worker_status[0]));
        for (int i=0; i<max_con; i++){
            worker_status[i]=0;
        }
    } else {
        max_con = 6;
        worker_status = malloc(max_con * sizeof(worker_status[0]));
        for (int i=0;i<max_con;i++){
            worker_status[i]=0;
        }
    }

    /* User defined cookie size */
    if (argc > 6) {
        cookie_size = strtol(argv[6], NULL, 10);
    }

    /* Prepare cookie */
    if ((cookie_string = malloc(sizeof(char) * cookie_size + 1)) == NULL) {
        perror("malloc");
    }

    memset(cookie_string, 97, cookie_size);
    cookie_string[cookie_size] = '\0';

    /* init a multi stack */
    multi_handle = curl_multi_init();
    if (pthread_mutex_init(&lock, NULL) != 0) {
        fprintf(stderr, "mutex init failed\n");
        exit(EXIT_FAILURE);
    }

    json_for_output=cJSON_CreateObject();
    download_size=cJSON_CreateArray();

    if (json_output == 1) {
        if (strrchr(testfile, '/') == NULL) {
            cJSON_AddStringToObject(json_for_output,"url",testfile);
           // printf("\"url_file\": \"%s\",\"OLT\":[", testfile);
        } else {
            cJSON_AddStringToObject(json_for_output,"url",strrchr(testfile,'/')+1);
            //printf("\"url_file\": \"%s\",\"OLT\":[", strrchr(testfile, '/') + 1);
        }
    }

    cJSON_AddStringToObject(json_for_output,"Protocol",argv[4]);
    cJSON_AddItemToObject(json_for_output,"OLT",download_size);

    dofile(testfile);
    pthread_mutex_destroy(&lock);

    //sleep(2);

    //cJSON_Delete(json);
    return 0;
}
