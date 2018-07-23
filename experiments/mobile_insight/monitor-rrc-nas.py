#file name: monitor-rrc-nas.py
import os
import sys

#Import MobileInsight modules
from mobile_insight.monitor import OnlineMonitor
from mobile_insight.analyzer import MsgLogger
if __name__ == "__main__":
        
                  if len(sys.argv) < 3:
                     print "Error: please specify physical port name and baudrate."
                     print __file__,"SERIAL_PORT_NAME BAUNRATE"
                     sys.exit(1)

                  # Initialize a 3G/4G monitor
                  src = OnlineMonitor()
                  src.set_skip_decoding(True)
                  src.set_serial_port(sys.argv[1]) #the serial port to collect the traces
                  src.set_baudrate(int(sys.argv[2])) #the baudrate of the port

                  # Enable 3G/4G messages to be monitored. 
                  # These are all the RRC and NAS monitors for the different technologies
                  # Enable them according to the technology you are testing 
                  src.enable_log("LTE_RRC_OTA_Packet")
                  src.enable_log("LTE_RRC_MIB_Message_Log_Packet")
                  src.enable_log("LTE_RRC_Serv_Cell_Info")
                  src.enable_log("LTE_RRC_MIB_Packet")
               #   src.enable_log("LTE_NAS_EMM_State")
               #   src.enable_log("LTE_NAS_ESM_OTA_Incoming_Packet")
               #   src.enable_log("LTE_NAS_ESM_OTA_Outgoing_Packet")
               #   src.enable_log("LTE_NAS_ESM_State")
               #   src.enable_log("LTE_NAS_EMM_OTA_Outgoing_Packet")
               #   src.enable_log("LTE_NAS_EMM_OTA_Incoming_Packet")
               #   src.enable_log("UMTS_NAS_GMM_State")
               #   src.enable_log("UMTS_NAS_MM_REG_State")
               #   src.enable_log("UMTS_NAS_OTA_Packet")
               #   src.enable_log("UMTS_NAS_MM_State")
               #   src.enable_log("WCDMA_RRC_OTA_Packet")
               #   src.enable_log("WCDMA_RRC_Serv_Cell_Info")

                  # This enables all supported logs
              #    src.enable_log_all()

                  # Save the monitoring results as an offline log
                  src.save_log_as("./test-rrc-nas.mi2log")

                 #Dump the messages to std I/O. Comment it if it is not needed.
                  dumper = MsgLogger()
                  dumper.set_source(src)
                 #save the messages (decoded) in a file. Formats are XML, JSON or plain text. Comment if not needed
                  dumper.set_decoding(MsgLogger.XML)
                  dumper.set_dump_type(5)
                  dumper.save_decoded_msg_as("./test-rrc-nas-decoded.xml")

                 #Start the monitoring
                  src.run()
