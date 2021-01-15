package httpmon

import (
	"crypto/tls"
	"fmt"
	"net/http/httptrace"
	"net/textproto"

	"github.com/opentracing/opentracing-go"
	"github.com/opentracing/opentracing-go/log"
)

func NewClientTrace(span opentracing.Span) *httptrace.ClientTrace {
	trace := &clientTrace{
		span: span,
	}
	return &httptrace.ClientTrace{
		GetConn:              trace.GetConn,
		GotConn:              trace.GotConn,
		PutIdleConn:          trace.PutIdleConn,
		GotFirstResponseByte: trace.GotFirstResponseByte,
		Got100Continue:       trace.Got100Continue,
		Got1xxResponse:       trace.Got1xxResponse,
		DNSStart:             trace.DNSStart,
		DNSDone:              trace.DNSDone,
		ConnectStart:         trace.ConnectStart,
		ConnectDone:          trace.ConnectDone,
		TLSHandshakeStart:    trace.TLSHandshakeStart,
		TLSHandshakeDone:     trace.TLSHandshakeDone,
		WroteHeaderField:     trace.WroteHeaderField,
		WroteHeaders:         trace.WroteHeaders,
		Wait100Continue:      trace.Wait100Continue,
		WroteRequest:         trace.WroteRequest,
	}
}

type clientTrace struct {
	span opentracing.Span
}

func (p *clientTrace) GetConn(hostPort string) {
	p.span.LogFields(
		log.String("event", "GetConn"),
		log.String("hostPort", hostPort),
	)
}

func (p *clientTrace) GotConn(info httptrace.GotConnInfo) {
	p.span.LogFields(
		log.String("event", "GotConn"),
		log.Bool("Reused", info.Reused),
		log.Bool("WasIdle", info.WasIdle),
		log.Int64("IdleTime", int64(info.IdleTime)),
	)
}

func (p *clientTrace) PutIdleConn(err error) {
	if err != nil {
		p.span.LogFields(
			log.String("event", "PutIdleConn"),
			log.String("err", err.Error()),
		)
	} else {
		p.span.LogFields(
			log.String("event", "PutIdleConn"),
		)
	}
}

func (p *clientTrace) GotFirstResponseByte() {
	p.span.LogFields(
		log.String("event", "GotFirstResponseByte"),
	)
}

func (p *clientTrace) Got100Continue() {
	p.span.LogFields(
		log.String("event", "Got100Continue"),
	)
}

func (p *clientTrace) Got1xxResponse(code int, header textproto.MIMEHeader) error {
	p.span.LogFields(
		log.String("event", "Got1xxResponse"),
		log.Int("code", code),
		log.String("header", fmt.Sprintf("%#v", header)),
	)
	return nil
}

func (p *clientTrace) DNSStart(info httptrace.DNSStartInfo) {
	p.span.LogFields(
		log.String("event", "DNSStart"),
		log.String("host", info.Host),
	)
}

func (p *clientTrace) DNSDone(info httptrace.DNSDoneInfo) {
	p.span.LogFields(
		log.String("event", "DNSDone"),
	)
}

func (p *clientTrace) ConnectStart(network, addr string) {
	p.span.LogFields(
		log.String("event", "ConnectStart"),
		log.String("network", network),
		log.String("addr", addr),
	)
}

func (p *clientTrace) ConnectDone(network, addr string, err error) {
	if err != nil {
		p.span.LogFields(
			log.String("event", "ConnectDone"),
			log.String("network", network),
			log.String("addr", addr),
			log.String("err", err.Error()),
		)
	} else {
		p.span.LogFields(
			log.String("event", "ConnectDone"),
			log.String("network", network),
			log.String("addr", addr),
		)
	}
}

func (p *clientTrace) TLSHandshakeStart() {
	p.span.LogFields(
		log.String("event", "TLSHandshakeStart"),
	)
}

func (p *clientTrace) TLSHandshakeDone(state tls.ConnectionState, err error) {
	p.span.LogFields(
		log.String("event", "TLSHandshakeDone"),
		log.String("Version", fmt.Sprintf("%x", state.Version)),
		log.Bool("HandshakeComplete", state.HandshakeComplete),
		log.Bool("DidResume", state.DidResume),
		log.String("NegotiatedProtocol", state.NegotiatedProtocol),
		log.Bool("NegotiatedProtocolIsMutual", state.NegotiatedProtocolIsMutual),
		log.String("ServerName", state.ServerName),
	)
}

func (p *clientTrace) WroteHeaderField(key string, value []string) {
	p.span.LogFields(
		log.String("event", "WroteHeaderField"),
	)
}

func (p *clientTrace) WroteHeaders() {
	p.span.LogFields(
		log.String("event", "WroteHeaders"),
	)
}

func (p *clientTrace) Wait100Continue() {
	p.span.LogFields(
		log.String("event", "Wait100Continue"),
	)
}

func (p *clientTrace) WroteRequest(info httptrace.WroteRequestInfo) {
	p.span.LogFields(
		log.String("event", "WroteRequest"),
	)
}
