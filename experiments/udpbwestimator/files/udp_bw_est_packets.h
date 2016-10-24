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

#include <stdint.h>

//To be on the safe size wrt headers and stuff
#define MAX_PAYLOAD_LEN 1400

typedef enum{
    NEW_SESSION=0, //The sender should start a new send session
    DATA, //Pkt shall be used for measurement
    END_SESSION, //Sent from sender after last data packet
    SENDER_FULL
} pkt_type;

struct pkt_hdr{
    uint8_t type;  
};

struct new_session_pkt{
    uint8_t type;
    uint16_t num_packets;
    uint16_t num_bursts; 
    uint16_t payload_len;
};
