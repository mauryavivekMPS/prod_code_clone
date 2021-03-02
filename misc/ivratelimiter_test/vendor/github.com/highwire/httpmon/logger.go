package httpmon

import (
	"bufio"
	"bytes"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"strings"
	"time"
)

// DefaultLogLayout defines a general purpose HighWire Logger layout
const DefaultLogLayout = `%v %h %l %u %t %r %s %b %{Referer}i %{User-Agent}i %{X-FwdH-Backend}i %{X-Firenze-Proxy-Client}i %{X-Forwarded-For}i %tls %firstbyte %lastbyte`

// NCSALogTimeLayout defines the time.Time#Format layout used by the common
// NCSA logging format
const NCSALogTimeLayout string = `[02/Jan/2006:15:04:05 -0700]`

// EmptyUnquotedField defines an unquoted log field value to write when no real
// value is available
const EmptyUnquotedField string = `-`

// EmptyQuotedField defines a quoted log field value to write when no real
// value is available
const EmptyQuotedField string = `"-"`

// Sep is used to separate fields written to the Logger
const Sep rune = rune(' ')

// LogFieldFn defines a function to write an accesslog field to the Logger
type LogFieldFn func(w io.Writer, rsp *InstrumentedResponseWriter, req *http.Request) (int, error)

// Logger writes an accesslog entry to an io.WriteCloser
type Logger struct {
	w  io.WriteCloser
	fn []LogFieldFn
}

// NewLogger initializes a new Logger using the specified layout and writing to
// the specified io.WriteCloser.  A layout string is a whitespace separated list of
// codes, without any quotes.  Whitespace in the layout is discarded, with the
// logger adding one Sep character in-between each logged field.
//
// Valid codes for layout are:
//
// %h:
//   log the remote client address
// %l:
//   log the request Context remote_logname value in quotes
// %u:
//   log the request Context remote_user value in quotes
// %t:
//   log the time the request was received in NCSALogTimeLayout
// %r:
//   log the first line of the request in quotes
// %s:
//   log the status code
// %b:
//   log the bytes written for the body
// %{ENV}e:
//   log the value ENV from the os.Environment in quotes
// %{NAME}c:
//   log the request Context value for NAME in quotes
// %v
//   log the request Host server name
// %{NAME}o:
//   log the value of the response header NAME in quotes
// %{NAME}i:
//   log the value of the request header NAME in quotes
// %tls:
//   log "true" if the request was over a TLS connection, otherwise "-"
// %firstbyte:
//   log the first-byte response time in microseconds
// %lastbyte:
//   log the last-byte response time in microseconds
//
// Any field that is not recognized is logged as is.
//
// As an example, setting a layout of:
//
//  %v %h %l %u %t %r %s %b %{Referer}i %{User-Agent}i %{unique_id}c %{session_id}c %{X-Firenze-Proxy-Cilent}i %tls %D
//
// could produce log a line like
//
// sassfs.highwire.org 10.220.48.189 - - [08/Mar/2020:19:59:59 -0700] "HEAD /svc.atom HTTP/1.0" 200 - "-" "-" "-" "-" "10.220.48.189" "-" 69
func NewLogger(layout string, w io.WriteCloser) *Logger {
	return &Logger{
		w:  w,
		fn: parseLogLayout(layout),
	}
}

// parseLogLayout parses a layout token string to produce a []LogFieldFn for
// Logger, any unrecognized tokens will be logged as is
func parseLogLayout(layout string) []LogFieldFn {

	var fn []LogFieldFn

	scanner := bufio.NewScanner(strings.NewReader(layout))
	scanner.Split(bufio.ScanWords)

	for scanner.Scan() {
		word := scanner.Text()
		n := len(word)

		// pick the word apart to see if it's a code, possibly with an
		// optional argument. A code will either be in the form
		// '%<xyz>' or the form '%{}<x>', in the latter case <x> is a
		// single character and the arg will be whatever was inside the
		// braces.
		var code, arg string
		if n >= 5 && word[0] == '%' && word[1] == '{' && word[n-2] == '}' {
			// 1 character code w/ arg
			code = fmt.Sprintf("%%{}%c", word[n-1])
			arg = word[2 : n-2]
		} else if n >= 2 && word[0] == '%' {
			// >= 1 character %<code> w/o arg
			code = word
			arg = ""
		}

		switch code {
		case "%h":
			fn = append(fn, LogFieldClientAddress())
		case "%l":
			fn = append(fn, LogFieldContext("remote_logname"))
		case "%u":
			fn = append(fn, LogFieldContext("remote_user"))
		case "%t":
			fn = append(fn, LogFieldRequestTime(NCSALogTimeLayout))
		case "%r":
			fn = append(fn, LogFieldRequestLine())
		case "%s":
			fn = append(fn, LogFieldStatusCode())
		case "%b":
			fn = append(fn, LogFieldBytes())
		case "%{}e":
			fn = append(fn, LogFieldEnv(arg))
		case "%{}c":
			fn = append(fn, LogFieldContext(arg))
		case "%v":
			fn = append(fn, LogFieldServerName())
		case "%{}o":
			fn = append(fn, LogFieldResponseHeader(arg))
		case "%{}i":
			fn = append(fn, LogFieldRequestHeader(arg))
		case "%tls":
			fn = append(fn, LogFieldSecure())
		case "%firstbyte":
			fn = append(fn, LogFieldFirstByteResponseTime())
		case "%D", "%lastbyte":
			fn = append(fn, LogFieldLastByteResponseTime())
		default:
			fn = append(fn, LogFieldUnknown(word))
		}
	}

	return fn
}

// LogRequest writes an accesslog entry to the io.WriteCloser for this request and response
func (l *Logger) LogRequest(rsp *InstrumentedResponseWriter, req *http.Request) (n int, err error) {
	bw := bufio.NewWriter(l.w)
	defer func() {
		if n > 0 {
			bw.WriteRune('\n')
			n++
		}
		bw.Flush()
	}()

	var nbytes int
	for i, fn := range l.fn {
		if i > 0 {
			if nbytes, err = bw.WriteRune(Sep); err == nil {
				n += nbytes
			} else {
				return
			}
		}
		if nbytes, err = fn(bw, rsp, req); err == nil {
			n += nbytes
		} else {
			return
		}
	}
	return
}

// Close shuts down the underlying io.WriteCloser associated with this Logger
func (p *Logger) Close() error {
	return p.w.Close()
}

// LogFieldUnkown provides a LogFieldFn for a token that could not be parsed,
// in which case we will simply inject the unknown token into the log record.
func LogFieldUnknown(s string) LogFieldFn {
	return func(w io.Writer, rsp *InstrumentedResponseWriter, req *http.Request) (int, error) {
		return io.WriteString(w, s)
	}
}

// LogFieldEnv writes the quoted value of an os.Environ value name to the log,
// if it exists.  If the value was not set in os.Environ the EmptyQuotedField
// will be written.
func LogFieldEnv(name string) LogFieldFn {
	return func(w io.Writer, rsp *InstrumentedResponseWriter, req *http.Request) (int, error) {
		val, ok := os.LookupEnv(name)
		if ok {
			return io.WriteString(w,
				fmt.Sprintf(`"%s"`, strings.ReplaceAll(val, `"`, `\"`)))
		} else {
			return io.WriteString(w, EmptyQuotedField)
		}
	}
}

// LogFieldContext  writes the quoted value of the req.Context value name to
// the log, if it exists.  If the value was not set in the request.Context, the
// EmptyQuotedField will be written.
func LogFieldContext(key string) LogFieldFn {
	return func(w io.Writer, rsp *InstrumentedResponseWriter, req *http.Request) (int, error) {
		if val := req.Context().Value(key); val != nil {
			return io.WriteString(w,
				fmt.Sprintf(`"%s"`, strings.ReplaceAll(fmt.Sprintf(`%v`, val), `"`, `\"`)))
		} else {
			return io.WriteString(w, EmptyQuotedField)
		}
	}
}

// LogFieldServerName writes the req.Host to the log
func LogFieldServerName() LogFieldFn {
	return func(w io.Writer, rsp *InstrumentedResponseWriter, req *http.Request) (int, error) {
		return io.WriteString(w, req.Host)
	}
}

// LogFieldClientAddress writes the host portion of the req.RemoteAddr to the log field
func LogFieldClientAddress() LogFieldFn {
	return func(w io.Writer, rsp *InstrumentedResponseWriter, req *http.Request) (int, error) {
		host, _, err := net.SplitHostPort(req.RemoteAddr)
		if err != nil {
			host = req.RemoteAddr
		}
		return io.WriteString(w, host)
	}
}

// LogFieldRequestTime writes the Started time from InstrumentedResponseWriter
// using the specified layout. Note that if you want the time field to contain
// things like surrounding brackets, you need to include those in the layout.
func LogFieldRequestTime(layout string) LogFieldFn {
	return func(w io.Writer, rsp *InstrumentedResponseWriter, req *http.Request) (int, error) {
		return io.WriteString(w, rsp.Started.Format(layout))
	}
}

// LogFieldRequestLine records a quoted string containing the first line of the
// request, which should consists of the req.Method, req.URL.Path, and
// req.Proto fields
func LogFieldRequestLine() LogFieldFn {
	return func(w io.Writer, rsp *InstrumentedResponseWriter, req *http.Request) (int, error) {
		buf := &bytes.Buffer{}
		buf.WriteString(req.URL.EscapedPath())
		if req.URL.RawQuery != "" {
			buf.WriteString("?")
			buf.WriteString(req.URL.RawQuery)
		}
		return io.WriteString(w, fmt.Sprintf(`"%s %s %s"`, req.Method, buf.String(), req.Proto))
	}
}

// LogFieldStatusCode logs the StatusCode from the InstrumentedResponseWriter
func LogFieldStatusCode() LogFieldFn {
	return func(w io.Writer, rsp *InstrumentedResponseWriter, req *http.Request) (int, error) {
		return io.WriteString(w, fmt.Sprintf("%d", rsp.StatusCode))
	}
}

// LogFieldBytes logs the Bytes from the InstrumentedResponseWriter, if this is zero
// then EmptyUnquotedField is logged
func LogFieldBytes() LogFieldFn {
	return func(w io.Writer, rsp *InstrumentedResponseWriter, req *http.Request) (int, error) {
		if rsp.Bytes > 0 {
			return io.WriteString(w, fmt.Sprintf("%d", rsp.Bytes))
		} else {
			return io.WriteString(w, EmptyUnquotedField)
		}
	}
}

// LogFieldResponseHeader logs the specified header value as a quoted string,
// if the header value does not exist in the response then EmptyQuotedField
// is written
func LogFieldResponseHeader(name string) LogFieldFn {
	return func(w io.Writer, rsp *InstrumentedResponseWriter, req *http.Request) (int, error) {
		val := rsp.Header().Get(name)
		if val != "" {
			val = fmt.Sprintf(`"%s"`, strings.ReplaceAll(val, `"`, `\"`))
		} else {
			val = EmptyQuotedField
		}
		return io.WriteString(w, fmt.Sprintf(`%s`, val))
	}
}

// LogFieldResponseHeader logs the specified header value as a quoted string,
// if the header value does not exist in the response then EmptyQuotedField
// is written
func LogFieldRequestHeader(name string) LogFieldFn {
	return func(w io.Writer, rsp *InstrumentedResponseWriter, req *http.Request) (int, error) {
		val := req.Header.Get(name)
		if val != "" {
			val = fmt.Sprintf(`"%s"`, strings.ReplaceAll(val, `"`, `\"`))
		} else {
			val = EmptyQuotedField
		}
		return io.WriteString(w, fmt.Sprintf(`%s`, val))
	}
}

// LogFieldSecure logs a quoted string "true" if the request had an TLS
// connection established, otherwise it logs the EmptyQuotedField
func LogFieldSecure() LogFieldFn {
	return func(w io.Writer, rsp *InstrumentedResponseWriter, req *http.Request) (int, error) {
		if req.TLS != nil {
			return io.WriteString(w, `"true"`)
		} else {
			return io.WriteString(w, EmptyQuotedField)
		}
	}
}

// LogFieldFirstByteResponseTime logs the time it took to start writing the response,
// in microseconds
func LogFieldFirstByteResponseTime() LogFieldFn {
	return func(w io.Writer, rsp *InstrumentedResponseWriter, req *http.Request) (int, error) {
		elapsed := rsp.FirstByte.Sub(rsp.Started) / time.Microsecond
		return io.WriteString(w, fmt.Sprintf(`%d`, int64(elapsed)))
	}
}

// LogFieldLastByteResponseTime logs time it took to complete writing the response, in
// microseconds
func LogFieldLastByteResponseTime() LogFieldFn {
	return func(w io.Writer, rsp *InstrumentedResponseWriter, req *http.Request) (int, error) {
		elapsed := rsp.LastByte.Sub(rsp.Started) / time.Microsecond
		return io.WriteString(w, fmt.Sprintf(`%d`, int64(elapsed)))
	}
}
