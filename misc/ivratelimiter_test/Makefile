IMAGE=fr-harbor.highwire.org/impactvizor/ivratelimiter_test:latest

all: build

build: FAKE
	docker build -t ${IMAGE} .

push: FAKE
	docker push ${IMAGE}

FAKE:
