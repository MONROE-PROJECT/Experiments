import datetime
import dateutil.relativedelta
from __future__ import division

def sizeof_fmt(num, suffix='B'):
   for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
       if abs(num) < 1024.0:
           return "%3.1f%s%s" % (num, unit, suffix)
       num /= 1024.0
   return "%.1f%s%s" % (num, 'Yi', suffix)

logfile=open("test","r")
num_packets=0

first=0
total_bytes=0
count=0
while True:
   line=logfile.readline()
   if line =='\n':
       count+=1
       first=0      
      # print tstamp
       duration=float(tstamp)-float(start)
       print ((total_bytes*8)/(1024*1024))
       print duration, sizeof_fmt(total_bytes), ((total_bytes*8)/(1024*1024))/duration
       total_bytes=0
       if count==3:
           break
   else:
       line = line.strip().split(' ')
       num_packets=num_packets+1
       if first==0:
           start, numbytes=line[0], int(line[1])
           total_bytes+=numbytes
           first=1
       else:
           tstamp, numbytes=line[0], int(line[1])
           total_bytes+=numbytes

print num_packets
