
package httpmon // import "github.com/highwire/httpmon"


CONSTANTS

const EmptyQuotedField string = `"-"`
    EmptyQuotedField defines a quoted log field value to write when no real
    value is available

const EmptyUnquotedField string = `-`
    EmptyUnquotedField defines an unquoted log field value to write when no real
    value is available

const NCSALogTimeLayout string = `[02/Jan/2006:15:04:05 -0700]`
    NCSALogTimeLayout defines the time.Time#Format layout used by the common
    NCSA logging format

const Sep rune = rune(' ')
    Sep is used to separate fields written to the Logger


TYPES

type InstrumentedHandler struct {
	// Has unexported fields.
}
    InstrumentedHandler is an http.Handler that tracks http.ResponseWriter
    statistics

func NewInstrumentedHandler(label string, usec_bin, byte_bin []float64, handler http.Handler, logger *Logger) (h *InstrumentedHandler, err error)
    https://godoc.org/github.com/prometheus/client_golang/prometheus#LinearBuckets
    https://godoc.org/github.com/prometheus/client_golang/prometheus#ExponentialBuckets

    If usec_bin is empty, prometheus.ExponentialBuckets(1e3, 3, 10) is used. If
    byte_bin is empty, prometheus.ExponentialBuckets(1e3, 2, 10) is used.

func (h *InstrumentedHandler) ServeHTTP(w http.ResponseWriter, req *http.Request)
    ServeHTTP implements http.Handler#ServeHTTP

type InstrumentedResponseWriter struct {

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
	// Has unexported fields.
}
    InstrumentedResponseWriter wraps an http.ResponseWriter and collects some
    data for InstrumentedHandler

func NewInstrumentedResponseWriter(w http.ResponseWriter) *InstrumentedResponseWriter
    NewInstrumentedResponseWriter initializes a new instance of
    InstrumentedResponseWriter.

func (p *InstrumentedResponseWriter) Header() http.Header
    Header implements http.ResponseWriter#Header

func (p *InstrumentedResponseWriter) Write(buf []byte) (int, error)
    Write implements http.ResponseWriter#Write

func (p *InstrumentedResponseWriter) WriteHeader(statusCode int)
    WriteHeader implements http.ResponseWriter#WriteHeader

type LogFieldFn func(w io.Writer, rsp *InstrumentedResponseWriter, req *http.Request) (int, error)
    LogFieldFn defines a function to write an accesslog field to the Logger

func LogFieldBytes() LogFieldFn
    LogFieldBytes logs the Bytes from the InstrumentedResponseWriter, if this is
    zero then EmptyUnquotedField is logged

func LogFieldClientAddress() LogFieldFn
    LogFieldClientAddress writes the host portion of the req.RemoteAddr to the
    log field

func LogFieldContext(key string) LogFieldFn
    LogFieldContext writes the quoted value of the req.Context value name to the
    log, if it exists. If the value was not set in the request.Context, the
    EmptyQuotedField will be written.

func LogFieldEnv(name string) LogFieldFn
    LogFieldEnv writes the quoted value of an os.Environ value name to the log,
    if it exists. If the value was not set in os.Environ the EmptyQuotedField
    will be written.

func LogFieldFirstByteResponseTime() LogFieldFn
    LogFieldFirstByteResponseTime logs the time it took to start writing the
    response, in microseconds

func LogFieldLastByteResponseTime() LogFieldFn
    LogFieldLastByteResponseTime logs time it took to complete writing the
    response, in microseconds

func LogFieldRequestHeader(name string) LogFieldFn
    LogFieldResponseHeader logs the specified header value as a quoted string,
    if the header value does not exist in the response then EmptyQuotedField is
    written

func LogFieldRequestLine() LogFieldFn
    LogFieldRequestLine records a quoted string containing the first line of the
    request, which should consists of the req.Method, req.URL.Path, and
    req.Proto fields

func LogFieldRequestTime(layout string) LogFieldFn
    LogFieldRequestTime writes the Started time from InstrumentedResponseWriter
    using the specified layout. Note that if you want the time field to contain
    things like surrounding brackets, you need to include those in the layout.

func LogFieldResponseHeader(name string) LogFieldFn
    LogFieldResponseHeader logs the specified header value as a quoted string,
    if the header value does not exist in the response then EmptyQuotedField is
    written

func LogFieldSecure() LogFieldFn
    LogFieldSecure logs a quoted string "true" if the request had an TLS
    connection established, otherwise it logs the EmptyQuotedField

func LogFieldServerName() LogFieldFn
    LogFieldServerName writes the req.Host to the log

func LogFieldStatusCode() LogFieldFn
    LogFieldStatusCode logs the StatusCode from the InstrumentedResponseWriter

func LogFieldUnknown(s string) LogFieldFn
    LogFieldUnkown provides a LogFieldFn for a token that could not be parsed,
    in which case we will simply inject the unknown token into the log record.

type Logger struct {
	// Has unexported fields.
}
    Logger writes an accesslog entry to an io.WriteCloser

func NewLogger(layout string, w io.WriteCloser) *Logger
    NewLogger initializes a new Logger using the specified layout and writing to
    the specified io.WriteCloser. A layout string is a whitespace separated list
    of codes, without any quotes. Whitespace in the layout is discarded, with
    the logger adding one Sep character in-between each logged field.

    Valid codes for layout are:

    %h:

        log the remote client address

    %l:

        log the request Context remote_logname value in quotes

    %u:

        log the request Context remote_user value in quotes

    %t:

        log the time the request was received in NCSALogTimeLayout

    %r:

        log the first line of the request in quotes

    %s:

        log the status code

    %b:

        log the bytes written for the body

    %{ENV}e:

        log the value ENV from the os.Environment in quotes

    %{NAME}c:

        log the request Context value for NAME in quotes

    %v

        log the request Host server name

    %{NAME}o:

        log the value of the response header NAME in quotes

    %{NAME}i:

        log the value of the request header NAME in quotes

    %tls:

        log "true" if the request was over a TLS connection, otherwise "-"

    %firstbyte:

        log the first-byte response time in microseconds

    %lastbyte:

        log the last-byte response time in microseconds

    Any field that is not recognized is logged as is.

    As an example, setting a layout of:

        %v %h %l %u %t %r %s %b %{Referer}i %{User-Agent}i %{unique_id}c %{session_id}c %{X-Firenze-Proxy-Cilent}i %tls %D

    could produce log a line like

    sassfs.highwire.org 10.220.48.189 - - [08/Mar/2020:19:59:59 -0700] "HEAD
    /svc.atom HTTP/1.0" 200 - "-" "-" "-" "-" "10.220.48.189" "-" 69

func (p *Logger) Close() error
    Close shuts down the underlying io.WriteCloser associated with this Logger

func (l *Logger) LogRequest(rsp *InstrumentedResponseWriter, req *http.Request) (n int, err error)
    LogRequest writes an accesslog entry to the io.WriteCloser for this request
    and response

