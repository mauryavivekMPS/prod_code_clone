package httpmon

import (
	"fmt"
	"log"
	"net/http"
	"net/http/httptrace"
	"net/url"
	"time"

	"github.com/opentracing/opentracing-go"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

type InstrumentedHandlerConfig struct {
	// Label identifies the service, and is used in both as a prefix in
	// prometheus counters and as the name applied to opentracing spans.
	Label string
	// Handler is the http handler to pass requests to.
	Handler http.Handler
	// Logger is called to log http requests, may be nil to deactivate
	// logging.
	Logger *Logger
	// Tracer activates opentracing using the Label as the identifier,
	// may be nil to deactivate opentracing.
	Tracer opentracing.Tracer
	// ClientTraceFn produces the http.ClientTrace to attach to a request,
	// otherwise NewClientTrace is used.
	ClientTraceFn func(span opentracing.Span) *httptrace.ClientTrace
	// UsecBin is used to initialize the prometheus buckets for counting
	// TTFB and TTLB times, if nil then a default is used.
	UsecBin []float64
	// ByteBin is used to initialize the prometheus buckets for counting
	// bytes served, if nil then a default is used.
	ByteBin []float64
}

// InstrumentedHandler is an http.Handler that tracks http.ResponseWriter
// statistics
type InstrumentedHandler struct {
	label                     string
	handler                   http.Handler
	logger                    *Logger
	tracer                    opentracing.Tracer
	clientTraceFn             func(span opentracing.Span) *httptrace.ClientTrace
	request_started           prometheus.Counter
	request_completed         prometheus.Counter
	request_usec_to_firstbyte prometheus.Histogram
	request_usec_to_lastbyte  prometheus.Histogram
	request_bytes_served      prometheus.Histogram
	request_code_served       *prometheus.CounterVec
	request_write_err         prometheus.Counter
}

// NewInstrumentedHandler initializes a new *InstrumentedHandler
func NewInstrumentedHandler(cfg InstrumentedHandlerConfig) (h *InstrumentedHandler, err error) {
	defer func() {
		if r := recover(); r != nil {
			if e, ok := r.(error); ok {
				err = e
			}
		}
	}()

	usecBin := cfg.UsecBin
	if len(usecBin) == 0 {
		usecBin = prometheus.ExponentialBuckets(1e3, 3, 10)
	}

	byteBin := cfg.ByteBin
	if len(byteBin) == 0 {
		byteBin = prometheus.ExponentialBuckets(1e3, 2, 10)
	}

	var clientTraceFn func(span opentracing.Span) *httptrace.ClientTrace
	if clientTraceFn = cfg.ClientTraceFn; clientTraceFn == nil {
		clientTraceFn = NewClientTrace
	}

	request_started := promauto.NewCounter(
		prometheus.CounterOpts{
			Name: fmt.Sprintf("%s_http_request_started", cfg.Label),
			Help: fmt.Sprintf("The number of HTTP requests started by the %s handler", cfg.Label),
		})

	request_completed := promauto.NewCounter(
		prometheus.CounterOpts{
			Name: fmt.Sprintf("%s_http_request_completed", cfg.Label),
			Help: fmt.Sprintf("The number of HTTP requests completed by the %s handler", cfg.Label),
		})

	request_usec_to_firstbyte := promauto.NewHistogram(
		prometheus.HistogramOpts{
			Name:    fmt.Sprintf("%s_http_request_usec_to_first_byte", cfg.Label),
			Help:    fmt.Sprintf("The microseconds elapsed for a request before the first byte was sent by the %s handler", cfg.Label),
			Buckets: usecBin,
		})

	request_usec_to_lastbyte := promauto.NewHistogram(
		prometheus.HistogramOpts{
			Name:    fmt.Sprintf("%s_http_request_usec_to_last_byte", cfg.Label),
			Help:    fmt.Sprintf("The microseconds elapsed for a request before the last byte was sent by the %s handler", cfg.Label),
			Buckets: usecBin,
		})

	request_bytes_served := promauto.NewHistogram(
		prometheus.HistogramOpts{
			Name:    fmt.Sprintf("%s_http_request_bytes", cfg.Label),
			Help:    fmt.Sprintf("The bytes served in a request by the %s handler", cfg.Label),
			Buckets: byteBin,
		})

	request_code_served := promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: fmt.Sprintf("%s_http_request_total", cfg.Label),
			Help: fmt.Sprintf("The number of HTTP requests served by the %s handler", cfg.Label),
		},
		[]string{"code"})

	request_write_err := promauto.NewCounter(
		prometheus.CounterOpts{
			Name: fmt.Sprintf("%s_write_err", cfg.Label),
			Help: fmt.Sprintf("The number of write errors encountered by the %s handler", cfg.Label),
		})

	h = &InstrumentedHandler{
		label:                     cfg.Label,
		handler:                   cfg.Handler,
		logger:                    cfg.Logger,
		tracer:                    cfg.Tracer,
		clientTraceFn:             clientTraceFn,
		request_started:           request_started,
		request_completed:         request_completed,
		request_usec_to_firstbyte: request_usec_to_firstbyte,
		request_usec_to_lastbyte:  request_usec_to_lastbyte,
		request_bytes_served:      request_bytes_served,
		request_code_served:       request_code_served,
		request_write_err:         request_write_err,
	}

	return h, nil
}

// ServeHTTP implements http.Handler#ServeHTTP
func (h *InstrumentedHandler) ServeHTTP(w http.ResponseWriter, req *http.Request) {
	defer func() {
		if err := recover(); err != nil {
			log.Printf("error serving %s %s: %v", req.Method, req.URL.String(), err)
			if w.Header().Get("Content-Type") == "" {
				w.WriteHeader(http.StatusInternalServerError)
			}
		}
	}()

	p := h.start(w)
	defer h.completed(p, req)
	defer p.done()

	if h.tracer != nil {
		// we'll use the request URL as part of the label, fill in the
		// missing pieces as best we can.
		reqURL := &url.URL{}
		*reqURL = *req.URL
		if reqURL.Scheme == "" {
			if req.TLS == nil {
				reqURL.Scheme = "http"
			} else {
				reqURL.Scheme = "https"
			}
		}
		if reqURL.Host == "" {
			reqURL.Host = req.Host
		}

		// final label is the req.Method + reqURL
		label := fmt.Sprintf("%s %s", req.Method, reqURL.String())

		// inherit any existing tracing context
		ctx := req.Context()
		parentSpan := opentracing.SpanFromContext(ctx)

		var parentCtx opentracing.SpanContext
		if parentSpan != nil {
			parentCtx = parentSpan.Context()
		}

		// setup a span to trace this request
		span := h.tracer.StartSpan(label, opentracing.ChildOf(parentCtx))
		defer span.Finish()

		ctx = opentracing.ContextWithSpan(ctx, span)
		trace := h.clientTraceFn(span)

		// annotate the request with the tracing context
		ctx = httptrace.WithClientTrace(ctx, trace)
		req = req.WithContext(ctx)
	}

	h.handler.ServeHTTP(p, req)
}

// start initializes a new InstrumentedResponseWriter at the start of a request
func (h *InstrumentedHandler) start(w http.ResponseWriter) *InstrumentedResponseWriter {
	h.request_started.Inc()
	return NewInstrumentedResponseWriter(w)
}

// completed records the completion of a request and updates statistics
func (h *InstrumentedHandler) completed(i *InstrumentedResponseWriter, req *http.Request) {
	h.request_completed.Inc()
	h.request_usec_to_firstbyte.Observe(float64(i.FirstByte.Sub(i.Started) / time.Microsecond))
	h.request_usec_to_lastbyte.Observe(float64(i.LastByte.Sub(i.Started) / time.Microsecond))
	h.request_bytes_served.Observe(float64(i.Bytes))
	h.request_code_served.WithLabelValues(fmt.Sprintf("%d", i.StatusCode)).Inc()
	if i.Err != nil {
		h.request_write_err.Inc()
	}
	if h.logger != nil {
		h.logger.LogRequest(i, req)
	}
}

// InstrumentedResponseWriter wraps an http.ResponseWriter and collects some
// data for InstrumentedHandler
type InstrumentedResponseWriter struct {
	// w is the actual ResponseWriter for the request
	w http.ResponseWriter

	// Started is the time the request was started
	Started time.Time

	// Firstbyte is the time the first bytes were written
	FirstByte time.Time

	// LastByte is the time the last bytes were written
	LastByte time.Time

	// StatusCode is the HTTP status code sent
	StatusCode int

	// Bytes is the number of bytes written
	Bytes int64

	// Err is the error on write, or nil
	Err error
}

// NewInstrumentedResponseWriter initializes a new instance of
// InstrumentedResponseWriter.
func NewInstrumentedResponseWriter(w http.ResponseWriter) *InstrumentedResponseWriter {
	return &InstrumentedResponseWriter{
		w:       w,
		Started: time.Now(),
	}
}

// Header implements http.ResponseWriter#Header
func (p *InstrumentedResponseWriter) Header() http.Header {
	return p.w.Header()
}

// WriteHeader implements http.ResponseWriter#WriteHeader
func (p *InstrumentedResponseWriter) WriteHeader(statusCode int) {
	p.begin(statusCode)
	p.w.WriteHeader(statusCode)
}

// Write implements http.ResponseWriter#Write
func (p *InstrumentedResponseWriter) Write(buf []byte) (int, error) {
	p.begin(http.StatusOK)
	n, err := p.w.Write(buf)
	p.Bytes += int64(n)
	p.Err = err
	return n, err
}

// begin is called whenever we're writing a response, it will set the FirstByte
// and StatusCode fields if they have not already been set
func (p *InstrumentedResponseWriter) begin(statusCode int) {
	if p.FirstByte.IsZero() {
		p.FirstByte = time.Now()
	}
	if p.StatusCode == 0 {
		p.StatusCode = statusCode
	}
}

// done is called when the response has been completed, it records the current
// time into LastByte if it has not already been set.
func (p *InstrumentedResponseWriter) done() {
	if p.LastByte.IsZero() {
		p.LastByte = time.Now()
	}
}
