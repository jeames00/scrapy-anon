FROM golang:1.15.2-alpine

RUN apk update && apk add --no-cache --wait 10 protoc git
RUN go get github.com/golang/protobuf/protoc-gen-go
COPY http-fetcher /http-fetcher
RUN mkdir /http-fetcher/pb
COPY import/protobuf/http.proto /grpcimport/
RUN protoc --go_out=plugins=grpc:/http-fetcher/pb --go_opt=paths=source_relative -I/grpcimport http.proto
WORKDIR /http-fetcher
RUN go mod init http-fetcher && go install .
USER 1000
