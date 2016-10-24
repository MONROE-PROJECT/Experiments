SRC2=udp_bw_est_rcvr.c
HDRS=udp_bw_est_packets.h 
CPLR=gcc
BNAME_R=UDPbwEstimatorRcvr

all: BNAME_R

BNAME_R: $(SRC2) Makefile
	$(CPLR) $(SRC2)  -o $(BNAME_R)
clean:
	rm -rf $(BNAME_R)
