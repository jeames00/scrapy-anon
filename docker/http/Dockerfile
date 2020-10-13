FROM golang:1.15.2-alpine

RUN apk update && apk add protoc git
RUN go get github.com/golang/protobuf/protoc-gen-go
COPY http-fetcher /http-fetcher
RUN mkdir /http-fetcher/pb
COPY protobuf/http.proto /grpcimport/
RUN protoc --go_out=plugins=grpc:/http-fetcher/pb -I/grpcimport http.proto
WORKDIR /http-fetcher
RUN go mod init http-fetcher && go install .
USER 1000
