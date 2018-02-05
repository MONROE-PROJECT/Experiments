#!/usr/bin/python3
import json
from dateutil import parser
import sys

# Open the HAR, and parse it
har = json.load(open(sys.argv[1], "r"))

# Instantiate counters
objects=[]
bytes=[]
tot_bytes=0
tot_obj=0
base_time=2**32 #Get the first object starting time and use it as page load starting point

# Loop over all objects
for entry in har["har"]["Objects"]:

    # Parse timings and size
    obj_start_time=parser.parse(entry["startedDateTime"]).timestamp()
    obj_delta_time= sum( [ v for v in entry["timings"].values() if v != -1])
    obj_time = obj_start_time + obj_delta_time/1000
    size = entry["objectSize"]
    
    # Add entries in the counters
    objects.append( (obj_time, 1   ) )
    bytes.append  ( (obj_time, size) )
    tot_bytes+=size
    tot_obj+=1
    
    # Find the minimum  <obj_start_time>
    if obj_start_time < base_time:
        base_time=obj_start_time

# Sort counters (might not be sorted)
objects_sorted=sorted(objects, key=lambda t: t[0])
bytes_sorted=sorted(bytes, key=lambda t: t[0])

# Calculate cumulative bytes/object value and normalize the time to make objects begin from t=0
objects_cumul=[]
cum_sum=0
for time,value in objects_sorted:
    cum_sum+=value
    objects_cumul.append( (time-base_time,cum_sum/tot_obj) )

# Do the same for bytes
bytes_cumul=[]
cum_sum=0
for time,value in bytes_sorted:
    cum_sum+=value
    bytes_cumul.append( (time-base_time,cum_sum/tot_bytes) )

# Calculate Object Index - Init Counters
prec_score=0
prec_time=0
objects_index=0

#Iterate over objects
for time, score in objects_cumul:
    component=(time-prec_time)*prec_score
    objects_index+=component
    prec_score = score
    prec_time  = time

# Calculate Byte Index - Init Counters
prec_score=0
prec_time=0
bytes_index=0

# Iterate over objects
for time, score in bytes_cumul:
    component=(time-prec_time)*prec_score
    bytes_index+=component
    prec_score=score
    prec_time = time

# Print the output in json format
print(json.dumps({"ObjectIndex":objects_index, "ByteIndex":bytes_index}))













