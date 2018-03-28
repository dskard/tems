PWD := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

PROJECT=tems
NETWORK=${PROJECT}_default
DCYML_MAIL=docker-compose.yml
PYTESTOPTS=
COMMAND=bash

test-env-up: network-up mail-server-up

test-env-down: mail-server-down network-down

mail-server-up:
	NETWORK=${NETWORK} \
	docker-compose -f ${DCYML_MAIL} -p ${PROJECT} up -d

mail-server-down:
	NETWORK=${NETWORK} \
	docker-compose -f ${DCYML_MAIL} -p ${PROJECT} stop -t 0
	NETWORK=${NETWORK} \
	docker-compose -f ${DCYML_MAIL} -p ${PROJECT} down -v

network-up:
	$(eval NETWORK_EXISTS=$(shell docker network inspect ${NETWORK} > /dev/null 2>&1 && echo 0 || echo 1))
	@if [ "${NETWORK_EXISTS}" = "1" ] ; then \
	    echo "Creating network: ${NETWORK}"; \
	    docker network create --driver bridge ${NETWORK} ; \
	fi;

network-down:
	$(eval NETWORK_EXISTS=$(shell docker network inspect ${NETWORK} > /dev/null 2>&1 && echo 0 || echo 1))
	@if [ "${NETWORK_EXISTS}" = "0" ] ; then \
	    for i in `docker network inspect -f '{{range .Containers}}{{.Name}} {{end}}' ${NETWORK}`; do \
	        echo "Removing container \"$${i}\" from network \"${NETWORK}\""; \
	        docker network disconnect -f ${NETWORK} $${i}; \
	    done; \
	    echo "Removing network: ${NETWORK}"; \
	    docker network rm ${NETWORK}; \
	fi;


test:
	docker run -it --rm \
	  --name=tems-test \
	  --network=${NETWORK} \
	  --user=$(shell id -u):$(shell id -g) \
	  --volume=${PWD}:/opt/shared/work \
	  --workdir=/opt/shared/work \
	  -e "PATH=/opt/shared/work:/usr/local/bin:/usr/bin:/bin" \
	  dskard/tew:dev \
	  pytest ${PYTESTOPTS} /opt/shared/work/test

run:
	docker run -it --rm \
	  --volume=${PWD}:/opt/shared/work \
	  --name=tems-task-$$(date +'%Y%m%d%H%M%S') \
	  --network=${NETWORK} \
	  --user=`id -u`:`id -g` \
	  --workdir=/opt/shared/work \
	  dskard/tew:dev \
	  ${COMMAND}


.PHONY: mail-server-up mail-server-down test run network-up network-down test-env-up test-env-down
