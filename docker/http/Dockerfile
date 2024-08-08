FROM golang:1.23rc2-alpine3.20

RUN apk update && apk add --no-cache --wait 10 protoc git
RUN go install github.com/golang/protobuf/protoc-gen-go@latest
RUN mkdir -p /scrapy-anon/http-fetcher/pb
COPY import/protobuf/http.proto /grpcimport/
RUN protoc --go_out=plugins=grpc:/scrapy-anon/http-fetcher/pb --go_opt=paths=source_relative -I/grpcimport http.proto
WORKDIR /scrapy-anon/http-fetcher
RUN go mod init http-fetcher
COPY http-fetcher /scrapy-anon/http-fetcher
RUN go mod tidy
RUN go build -o http-fetcher
USER 1000
