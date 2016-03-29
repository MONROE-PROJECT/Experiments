
## This is a common makefile for docker management.
## Include in later makefiles, which define the overrides below.



# Variables to override in including makefiles:
CONTAINER:=undef
EXTRARUNOPTIONS:=undef
EXTRARUNARGS:=


# Common configuration options (make sure to use =, not :=, for late binding)

REPO=monroe1.cs.kau.se:5000
DOCKERFILE=$(CONTAINER).docker
CONTAINERTAG=monroe/$(CONTAINER)


# Common targets

all:
	@echo "Instructions:"
	@echo "1. 'make image' is used to build image $(CONTAINERTAG)"
	@echo "2. 'make push' pushes the image to the monroe repository (be sure to 'docker login' first!)"
	@echo "3. 'make run-local' starts a container from a local build"
	@echo "4. 'make run-repo' starts a container from the repository"
	@echo "5. 'make stop' stops and removes running a container based on image $(CONTAINERTAG)."

stop:
	@echo "Stopping possibly previous running container (_undefined_ error is OK)"
	docker ps | grep $(CONTAINERTAG) | cut -f 1 -d ' ' | xargs docker rm -f _undefined_ || true

push:
	docker push  $(REPO)/$(CONTAINERTAG)

image:
	docker build -f $(DOCKERFILE) -t $(CONTAINERTAG) .  
	docker tag -f $(CONTAINERTAG) $(REPO)/$(CONTAINERTAG)

run-local: stop
	@echo "Starting container."
	docker run -i -t $(RUNOPTIONS) $(CONTAINERTAG) $(RUNARGS)
	
run-repo: stop
	@echo "Starting container."
	docker pull $(REPO)/$(CONTAINERTAG)
	docker run -i -t $(RUNOPTIONS) $(REPO)/$(CONTAINERTAG) $(RUNARGS)

run-manual:
	@echo docker run -d $(RUNOPTIONS) $(REPO)/$(CONTAINERTAG) $(RUNARGS)

pull-manual:
	@echo docker pull $(REPO)/$(CONTAINERTAG)

run-daemon: stop
	@echo "Starting daemonized container."
	docker run -d $(RUNOPTIONS) $(REPO)/$(CONTAINERTAG) $(RUNARGS)

