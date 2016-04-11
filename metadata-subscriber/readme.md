
# Metadata subscriber
Attaches as a subscriber to the ZeroMQ socket on tcp://localhost:5556 and save the metadata in a json format suitable for later import in monroe db
All json files are saved in /outdir inside the container.

## Requirements
The /outdir directory in the container must be mapped to a directory on the host to access the json files.
This mapped directory ("outdir") must be emptied on regular intervals by an external process to avoid filling the disk.

## Example usage of file
```bash
python metadata_subscriber.py
```


## Docker misc usage
docker ps  # list running images
docker exec -it [container id] bash   # attach to running container
