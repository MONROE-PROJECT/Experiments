
include ../../common.mk

CONTAINER:=ping
RUNOPTIONS:=--net=host -v /outdir:/outdir -v /etc/nodeid:/nodeid:ro 
RUNARGS:=wwan0

run-fixme:
	docker run --net=host -d -v /outdir:/outdir -v /etc/config/nodeid:/nodeid:ro monroe/ping wwan0 
	docker run --net=host -d -v /outdir:/outdir -v /etc/config/nodeid:/nodeid:ro monroe/ping eth0

	
