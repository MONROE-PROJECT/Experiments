/*
-------------------------------------------------------------------------------------
    This source file is part of UDPbwEstimator.

    UDPbwEstimator is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or any later version.

    UDPbwEstimator is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with UDPbwEstimator.  If not, see <http://www.gnu.org/licenses/>.
-------------------------------------------------------------------------------------
*/

#include <stdio.h>
#include <stdint.h>
#include <unistd.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/times.h>
#include <netdb.h>
#include <string.h>
#include <arpa/inet.h>
#include "udp_bw_est_packets.h"

//#ifndef BW_ESTIMATION_RECV
//#define BW_ESTIMATION_RECV

#define NEW_SESSION_TIMEOUT 5 //Timeout between new session packets
#define RETRANSMISSION_THRESHOLD 5
#define DEFAULT_TIMEOUT 60 //Timeout waiting for the next data pack/END_SESSION

#define NUM_CONN_ATTEMPTS 5

//Define three states, STARTING, RECEIVING, ENDING
//- STARTING: Send NEW_SESSION every TIMEOUT second, up to N times. Abort if
//no reply is received X seconds after last message
//- RECEIVING: SESSION started, receiving data. Wait DURATION seconds for
//data, move to ENDING after DURATION has passed. Abort if no packets have
//been received. Reset DURATION upon first packet
//- ENDING: Wait ENDING_TIMEOUT seconds before aborting. This state is
//included in receiving

typedef enum{
    STARTING = 0,
    RECEIVING //Receiving also covers the ending state, as the timer is reset for each data packet
} bwrecv_state;

//#endif


socklen_t fill_sender_addr(struct sockaddr_storage *sender_addr, 
        char *sender_ip, char *sender_port){
    socklen_t addr_len = 0;
    struct addrinfo hints, *servinfo;
    int32_t rv;

    memset(&hints, 0, sizeof hints);
    hints.ai_family = AF_UNSPEC;

    if((rv = getaddrinfo(sender_ip, sender_port, &hints, &servinfo)) != 0){
        fprintf(stderr, "Getaddrinfo failed for sender address\n");
        return 0;
    }

    if(servinfo != NULL){
        memcpy(sender_addr, servinfo->ai_addr, servinfo->ai_addrlen);
        addr_len = servinfo->ai_addrlen;
    }

    freeaddrinfo(servinfo);
    return addr_len;
}



void network_loop_udp(int32_t udp_sock_fd, int16_t num_packets, int16_t num_bursts,
        int16_t payload_len, struct sockaddr_storage *sender_addr, 
        socklen_t sender_addr_len, FILE *output_file){

    fd_set recv_set;
    fd_set recv_set_copy;
    int32_t fdmax = udp_sock_fd + 1;
    int32_t retval = 0;
    struct timeval tv;
    size_t total_number_bytes = 0;
    struct timespec t0, t1;
    double data_interval;
    double estimated_bandwidth;
    int32_t rcvd_packets=0; 
    uint8_t new_session=0;

    struct msghdr msg;
    struct iovec iov;
    bwrecv_state state = STARTING; 

    uint8_t buf[MAX_PAYLOAD_LEN] = {0};
    ssize_t numbytes = 0;
    uint8_t consecutive_retrans = 0;
    struct cmsghdr *cmsg;
    uint8_t cmsg_buf[sizeof(struct cmsghdr) + sizeof(struct timespec)] = {0};
    struct timespec *recv_time;
    struct pkt_hdr *hdr = NULL;

    //Configure the variables used for the select
    FD_ZERO(&recv_set);
    FD_ZERO(&recv_set_copy);
    FD_SET(udp_sock_fd, &recv_set);

    memset(&msg, 0, sizeof(struct msghdr));
    memset(&iov, 0, sizeof(struct iovec));

    iov.iov_base = buf;
    iov.iov_len = sizeof(struct new_session_pkt);

    msg.msg_name = (void *) sender_addr;
    msg.msg_namelen = sender_addr_len;
    msg.msg_iov = &iov;
    msg.msg_iovlen = 1;
    msg.msg_control = (void *) cmsg_buf;
 
    //Send first NEW_SESSION-packet
    struct new_session_pkt *session_pkt = (struct new_session_pkt *) buf; 
    session_pkt->type = NEW_SESSION; 
    session_pkt->num_packets = num_packets;
    session_pkt->num_bursts = num_bursts;
    session_pkt->payload_len = payload_len;

    numbytes = sendmsg(udp_sock_fd, &msg, 0);
    if(numbytes <= 0){
        fprintf(stderr, "Failed to send initial NEW_SESSION message\n");
        exit(EXIT_FAILURE);
    } else {
        fprintf(stderr, "Sent first NEW_SESSION message\n");
    }

    while(1){
       
        recv_set_copy = recv_set;
        if(state == STARTING){
            tv.tv_sec = NEW_SESSION_TIMEOUT;
            tv.tv_usec = 0;
        } else {
            //The timeout is reset for each data packet I receive
            tv.tv_sec = DEFAULT_TIMEOUT; 
            tv.tv_usec = 0;
        }

        retval = select(fdmax, &recv_set_copy, NULL, NULL, &tv);
        if(retval == 0){
            if(state == RECEIVING){
                //Might be able to compute somethig, therefore break
              /*  fprintf(stderr, "%d seconds passed without any traffic," 
                        "aborting\n", duration); */
                break;
            } else if(consecutive_retrans == RETRANSMISSION_THRESHOLD){
                fprintf(stderr, "Did not receive any reply to NEW_SESSION," 
                        "aborting\n");
                exit(EXIT_FAILURE);
            } else {
                //Send retransmission
                fprintf(stderr, "Retransmitting NEW_SESSION. Consecutive " 
                        "retransmissions %d\n", ++consecutive_retrans);
                sendmsg(udp_sock_fd, &msg, 0);
            }
        } else {
            msg.msg_controllen = sizeof(cmsg_buf);
            iov.iov_len = sizeof(buf);
            numbytes = recvmsg(udp_sock_fd, &msg, 0); 
            hdr = (struct pkt_hdr*) buf;

            if(hdr->type == DATA){
                cmsg = CMSG_FIRSTHDR(&msg);
                if(cmsg->cmsg_level == SOL_SOCKET && cmsg->cmsg_type == 
                        SO_TIMESTAMPNS){
                    recv_time = (struct timespec *) CMSG_DATA(cmsg);
                    if(output_file != NULL)
                        fprintf(output_file, "%.9f %zd\n", 
                                recv_time->tv_sec + 
                                recv_time->tv_nsec/1000000000.0, numbytes);
            rcvd_packets++;
            if(new_session==1){
            memcpy(&t0, recv_time, sizeof(struct timespec));
            new_session=0;
            }
            
            if(rcvd_packets==num_packets){
            rcvd_packets=0;
                data_interval = (t1.tv_sec - t0.tv_sec) + 
                    ((t1.tv_nsec - t0.tv_nsec)/1000000000.0);
                    estimated_bandwidth = 
                        ((total_number_bytes / 1000000.0) * 8) / data_interval;
                    //Computations?
                    fprintf(stderr, "Received %zd bytes in %.8f seconds. Estimated " 
                        "bandwidth %.2f Mbit/s\n", total_number_bytes, data_interval, 
                        estimated_bandwidth);
		    printf("%.2f ",estimated_bandwidth);
                new_session=1;
		fputs("\n", output_file);
                total_number_bytes=0;
             }
                }

                if(state == STARTING){
                    memcpy(&t0, recv_time, sizeof(struct timespec));
                    state = RECEIVING;
                }

                memcpy(&t1, recv_time, sizeof(struct timespec));
                total_number_bytes += numbytes;
            } else if(hdr->type == END_SESSION){
                fprintf(stderr, "End session\n");
                break;
            } else if(hdr->type == SENDER_FULL){
                fprintf(stderr, "Sender is full, cant serve more clients\n");
                break;
            } else {
                fprintf(stderr, "Unkown\n");
            }
        }

    }

    /*if(total_number_bytes > 0){
        data_interval = (t1.tv_sec - t0.tv_sec) + 
            ((t1.tv_nsec - t0.tv_nsec)/1000000000.0);
        estimated_bandwidth = 
            ((total_number_bytes / 1000000.0) * 8) / data_interval;
        //Computations?
        fprintf(stderr, "Received %zd bytes in %.8f seconds. Estimated " 
                "bandwidth %.2f Mbit/s\n", total_number_bytes, data_interval, 
                estimated_bandwidth);
    }*/

    close(udp_sock_fd);
}

//Bind the local socket. Should work with both IPv4 and IPv6
int bind_local(char *local_addr, char *local_port, int socktype){
  struct addrinfo hints, *info, *p;
  int sockfd;
  int rv;
  int yes=1;
  
  memset(&hints, 0, sizeof hints);
  hints.ai_family = AF_UNSPEC;
  hints.ai_socktype = socktype;
  
  if((rv = getaddrinfo(local_addr, local_port, &hints, &info)) != 0){
    fprintf(stderr, "Getaddrinfo (local) failed: %s\n", gai_strerror(rv));
    return -1;
  }
  
  for(p = info; p != NULL; p = p->ai_next){
    if((sockfd = socket(p->ai_family, p->ai_socktype, p->ai_protocol)) == -1){
      fprintf(stderr, "Socket:");
      continue;
    }

    if(setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(int)) == -1) {
      close(sockfd);
      fprintf(stderr, "Setsockopt (reuseaddr)");
      continue;
    }

    if(setsockopt(sockfd, SOL_SOCKET, SO_TIMESTAMPNS, &yes, sizeof(int)) == -1){
      close(sockfd);
      fprintf(stderr, "Setsockopt (timestamp)");
      continue;
    }

    if(bind(sockfd, p->ai_addr, p->ai_addrlen) == -1){
      close(sockfd);
      fprintf(stderr, "Bind (local)");
      continue;
    }

    break;
  }

  if(p == NULL){
    fprintf(stderr, "Local bind failed\n");
    freeaddrinfo(info);  
    return -1;
  }

  freeaddrinfo(info);

  return sockfd;
}

void usage(){
    fprintf(stderr, "Supported command line arguments\n");
    fprintf(stderr, "-c : Number of back to back packets to be sent  in each second\n");
    fprintf(stderr, "-b : number of bust to be sent\n");
    fprintf(stderr, "-l : Payload length (in bytes)\n");
    fprintf(stderr, "-s : Source IP to bind to\n");
    fprintf(stderr, "-o : source port\n");
    fprintf(stderr, "-d : Destion IP\n");
    fprintf(stderr, "-p : Destion port\n");
    fprintf(stderr, "-w : Provide an optional filename for writing the "\
            "packet receive times\n");
}

int main(int argc, char *argv[]){
    uint8_t num_conn_retries = 0;
    uint16_t num_packets = 0, num_bursts = 0, payload_len = 0, iat = 0;
    char *src_ip = NULL, *src_port = NULL, *sender_ip = NULL, *sender_port = NULL, 
         *file_name = NULL;
    int32_t retval, socket_fd = -1, socktype = SOCK_DGRAM;
    struct sockaddr_storage sender_addr;
    socklen_t sender_addr_len = 0;
    char addr_presentation[INET6_ADDRSTRLEN];
    FILE *output_file = NULL;

    while((retval = getopt(argc, argv, "c:b:l:s:o:d:p:w:")) != -1){
        switch(retval){
            case 'c':
                num_packets = atoi(optarg);
                break;
            case 'b':
                num_bursts = atoi(optarg);
                break;
            case 'l':
                payload_len = atoi(optarg);
                break;
            case 's':
                src_ip = optarg;
                break;
            case 'o':
                src_port = optarg;
                break;
            case 'd':
                sender_ip = optarg;
                break;
            case 'p':
                sender_port = optarg;
                break;
            case 'w':
                file_name = optarg;
                break;
            default:
                usage();
                exit(EXIT_FAILURE);
        }
    }


    if((num_bursts == 0) || src_ip == NULL || sender_ip == NULL ||
            sender_port == NULL){
        usage();
        exit(EXIT_FAILURE);
    }

    if(num_packets == 0 || payload_len == 0){
        usage();
        exit(EXIT_FAILURE);
    }

    if(payload_len > MAX_PAYLOAD_LEN){
        fprintf(stderr, "Payload length exceeds limit (%d)\n", MAX_PAYLOAD_LEN);
        exit(EXIT_FAILURE);
    }

    if(file_name != NULL && ((output_file = fopen(file_name, "w")) == NULL)){
        fprintf(stderr, "Failed to open output file\n");
        printf("Opening files\n");
        exit(EXIT_FAILURE);
    }

    //Bind network socket
    if((socket_fd = bind_local(src_ip, src_port, socktype)) == -1){
        fprintf(stderr, "Binding to local IP failed\n");
        exit(EXIT_FAILURE);
    }

    fprintf(stderr, "Network socket %d\n", socket_fd);

    memset(&sender_addr, 0, sizeof(struct sockaddr_storage));
    
    if(!(sender_addr_len = fill_sender_addr(&sender_addr, sender_ip, sender_port))){
        fprintf(stderr, "Could not fill sender address struct. Is the address " 
                "correct?\n");
        exit(EXIT_FAILURE);
    }

    if(sender_addr.ss_family == AF_INET){
        inet_ntop(AF_INET, &(((struct sockaddr_in *) &sender_addr)->sin_addr),
                addr_presentation, INET6_ADDRSTRLEN);
        fprintf(stderr, "Sender (IPv4) %s:%s\n", addr_presentation, sender_port);
    } else if(sender_addr.ss_family == AF_INET6){
        inet_ntop(AF_INET6, &(((struct sockaddr_in6 *) &sender_addr)->sin6_addr),
                addr_presentation, INET6_ADDRSTRLEN);
        fprintf(stderr, "Sender (IPv6) %s:%s\n", addr_presentation, sender_port);
    }

  
    network_loop_udp(socket_fd, num_packets, num_bursts, payload_len, &sender_addr, 
                sender_addr_len, output_file);

    exit(EXIT_SUCCESS);
}
