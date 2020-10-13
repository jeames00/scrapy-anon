package main

import (
	"fmt"
	utls "github.com/refraction-networking/utls"
	"golang.org/x/net/context"
	"google.golang.org/grpc"
	"http-fetcher/pb"
	"io"
	"io/ioutil"
	"log"
	"net"
	"net/http"
	"net/url"
	"os"
)

var httpRoundTripper *http.Transport = http.DefaultTransport.(*http.Transport)

var tlsCh = make(chan *utls.UConn)
var browserClientHello string
var grpc_port = os.Getenv("HTTP_GRPC_PORT")

type HttpClient struct {
	HttpClient *http.Client
	TLSConn    *utls.UConn
}

type Server struct {
	pb.UnimplementedHttpClientServer
	httpClientMap map[string]*http.Client
}

func main() {
	grpcServer := grpc.NewServer()
	var httpClientMap = make(map[string]*http.Client)

	server := Server{
		httpClientMap: httpClientMap,
	}

	pb.RegisterHttpClientServer(grpcServer, &server)

	listen, err := net.Listen("tcp", "0.0.0.0:"+grpc_port)
	if err != nil {
		log.Print("could not listen to 0.0.0.0:" + grpc_port)
	}

	log.Println("Server listening on port " + grpc_port)
	log.Fatal(grpcServer.Serve(listen))
}

func (s *Server) GetURL(ctx context.Context, request *pb.Request) (*pb.Response, error) {

	proxyURI, _ := url.Parse(request.Proxy)

	req, err := http.NewRequest("GET", request.Url, nil)
	if err != nil {
		log.Print(err)
		return &pb.Response{Error: "gRPC server error: couldn't format HTTP GET request"}, nil
	}

	for k, v := range request.Headers {
		req.Header.Add(k, v)
	}

	httpRoundTripper.Proxy = http.ProxyURL(proxyURI)

	rt, err := NewUTLSRoundTripper(request.ClientHello, nil, proxyURI)
	resp, err := rt.RoundTrip(req)
	if err != nil {
		log.Print(err)
		fmt.Printf("%+v\n", err)
		return &pb.Response{Error: "gRPC server error: couldn't make HTTP request"}, nil
	}

	log.Print(resp)

	var reader io.ReadCloser

	//////////////////////////////////////////////////////////////////
	//	** De-compression/content-encoding is handled	        //
	//	by Scrapy. Un-comment below to handle here instead **	//
	//////////////////////////////////////////////////////////////////
	//
	//	import (
	//	    "compress/flate"
	//	    "compress/gzip"
	//	    "github.com/dsnet/compress/brotli"
	//	)
	//
	//	switch resp.Header.Get("Content-Encoding") {
	//	case "gzip":
	//		reader, err = gzip.NewReader(resp.Body)
	//	case "deflate":
	//		reader = flate.NewReader(resp.Body)
	//	case "br":
	//		reader, err = brotli.NewReader(resp.Body, &brotli.ReaderConfig{})
	//	default:
	//		reader = resp.Body
	//	}
	//	responseData, err := ioutil.ReadAll(reader)
	//	if err != nil {
	//		log.Print(err)
	//	}
	//
	//	body := string(responseData)

	reader = resp.Body
	responseData, err := ioutil.ReadAll(reader)
	if err != nil {
		log.Print(err)
	}
	body := responseData

	var headers = make(map[string]string)
	for key, val := range resp.Header {
		headers[key] = val[0]
	}

	resp.Body.Close()

	return &pb.Response{
		Status:  resp.Status,
		Headers: headers,
		Body:    body,
		Error:   ""}, nil
}
