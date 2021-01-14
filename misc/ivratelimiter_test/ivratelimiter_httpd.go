package main

import (
	"bufio"
	"bytes"
	"context"
	"flag"
	"io"
	"io/ioutil"
	"log"
	"math/rand"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"time"

	"github.com/highwire/httpmon"
)

var optAddress string = "0.0.0.0:8080"

var optHeadersFile string = ""

var optLogLayout string = "%v %h %l %u %t %r %s %b %{Referer}i %{User-Agent}i %D"

// ivratelimiter_httpd daemon reads a serialized http response from the
// filesystem and returns it in response to incoming http requests
func main() {
	log.SetFlags(log.Ldate | log.Ltime | log.Lshortfile)

	flag.StringVar(&optAddress, "a", optAddress, "http server address")
	flag.StringVar(&optHeadersFile, "f", "", "http response file")
	flag.StringVar(&optLogLayout, "l", optLogLayout, "access log layout")
	flag.Parse()

	if optHeadersFile == "" {
		log.Fatalf("missing required parameter: -f response.txt")
	}

	ctx, cancelFn := context.WithCancel(context.Background())

	handler := NewHandler(ctx, optHeadersFile)

	logger := httpmon.NewLogger(optLogLayout, os.Stdout)

	instrumentedHandler, err := httpmon.NewInstrumentedHandler(
		httpmon.InstrumentedHandlerConfig{
			Label:   filepath.Base(os.Args[0]),
			Handler: handler,
			Logger:  logger,
		},
	)
	if err != nil {
		log.Fatal(err)
	}

	server := &http.Server{
		Addr:    optAddress,
		Handler: instrumentedHandler,
	}

	go func() {
		err := server.ListenAndServe()
		if err != http.ErrServerClosed {
			log.Println(err)
		}
		cancelFn()
	}()

	go func() {
		ch := make(chan os.Signal, 1)
		signal.Notify(ch, os.Interrupt)

		<-ch
		server.Close()
		cancelFn()
	}()

	<-ctx.Done()
}

// Handler watches a filesystem path fpath for new serialized HTTP responses to
// serve to incoming requests
type Handler struct {
	ctx   context.Context
	fpath string
}

func NewHandler(ctx context.Context, fpath string) *Handler {
	h := &Handler{
		ctx:   ctx,
		fpath: fpath,
	}
	return h
}

// ServeHTTP implementing http.Handler, if no response has been provided on the
// filesystem a default response of HTTP/1.1 OK 200 is returned.
func (h *Handler) ServeHTTP(w http.ResponseWriter, req *http.Request) {

	var rsp *http.Response
	var err error

	rsp, err = parseResponse(h.fpath)
	if err == nil && rsp != nil {
		time.Sleep(time.Duration(rand.Int63n(2e9)))

		for k, v := range rsp.Header {
			for i := 0; i < len(v); i++ {
				w.Header().Add(k, v[i])
			}
		}

		w.WriteHeader(rsp.StatusCode)

		if _, err := io.Copy(w, rsp.Body); err != nil {
			log.Println(err)
		}

		return
	}

	w.WriteHeader(http.StatusOK)
}

// parseResponse parses a serialzed HTTP response from fpath and returns it
func parseResponse(fpath string) (*http.Response, error) {
	fh, err := os.Open(fpath)
	if err != nil {
		return nil, err
	}

	defer fh.Close()

	buf, err := ioutil.ReadAll(fh)
	if err != nil {
		return nil, err
	}

	r := bufio.NewReader(bytes.NewReader(buf))
	rsp, err := http.ReadResponse(r, nil)
	if err != nil {
		return nil, err
	}

	return rsp, err
}
