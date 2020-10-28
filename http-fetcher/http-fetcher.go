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
	"strings"
)

var httpRoundTripper *http.Transport = http.DefaultTransport.(*http.Transport)

var tlsCh = make(chan *utls.UConn)
var browserClientHello string
var grpc_port = os.Getenv("HTTP_GRPC_PORT")

type Server struct {
	pb.UnimplementedHttpClientServer
	roundTrippers map[string]http.RoundTripper
}

func main() {
	grpcServer := grpc.NewServer()
	var roundTrippers = make(map[string]http.RoundTripper)

	server := Server{
		roundTrippers: roundTrippers,
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

	req, err := http.NewRequest("GET", request.Url, nil)
	if err != nil {
		log.Print(err)
		return &pb.Response{Error: "gRPC server error: couldn't format HTTP GET request"}, nil
	}

	var altsvc string
	for k, v := range request.Headers {
		if k == "Alt-Svc" {
			altsvc = v
			// If connecting to an onion Alt-Svc, connect to standard Tor
			// process instead (Tor manages this better when allowing it
			// to build the circuit)
			request.Proxy = "socks5://tor:9050"
			continue
		}
		log.Printf("%s, %s\n", k, v)
		req.Header.Add(k, v)
	}

	proxyURI, _ := url.Parse(request.Proxy)
	httpRoundTripper.Proxy = http.ProxyURL(proxyURI)

	// Create a UTLSRoundTripper for each proxy connection,
	// store it in a map for reuse on next request
	if _, found := s.roundTrippers[request.Proxy]; !found {
		rt, err := NewUTLSRoundTripper(
			request.ClientHello, &altsvc, nil, proxyURI,
		)
		if err == nil {
			s.roundTrippers[request.Proxy] = rt
		} else {
			return nil, err
		}
	}

	resp, err := s.roundTrippers[request.Proxy].RoundTrip(req)
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

	var responseHeaders = make(map[string]string)
	for key, val := range resp.Header {
		a := strings.Join(val, " ")
		responseHeaders[key] = a
	}

	resp.Body.Close()

	return &pb.Response{
		Status:  resp.Status,
		Headers: responseHeaders,
		Body:    body,
		Error:   ""}, nil
}
