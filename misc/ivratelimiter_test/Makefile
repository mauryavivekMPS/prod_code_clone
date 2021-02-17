IMAGE=fr-harbor.highwire.org/impactvizor/ivratelimiter_test:latest

all: build

build: FAKE
	docker build -t ${IMAGE} .

push: FAKE
	docker push ${IMAGE}

test: FAKE
	 docker run --rm --network iv_default ${IMAGE}

FAKE:
