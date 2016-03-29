
# Experiment
Script to create valid json format form the output of fping 

## Requirements

These directories must exist and be writable by the user/process running fping_json_formatter.py:    
/output/    
/tmp/    


## Example usage
```bash
fping -D -p 1000 -l 8.8.8.8 | python ./fping_json_formatter.py
```

## Docker misc usage

docker ps  # list running images
docker exec -it [container id] bash   # attach to running container
