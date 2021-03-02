FROM golang:1.14-alpine AS build-env
WORKDIR /go/src
COPY ./ /go/src/
RUN go build -mod vendor ivratelimiter_httpd.go

FROM alpine:3.11
RUN apk update
RUN apk add bash coreutils curl gawk parallel
COPY --from=build-env /go/src/ivratelimiter_httpd /
COPY ./ivratelimiter_test.sh /

CMD /ivratelimiter_test.sh
