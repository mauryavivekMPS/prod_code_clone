package httpmon

import (
	"fmt"
	"io"

	"github.com/opentracing/opentracing-go"
	"github.com/uber/jaeger-client-go/config"
)

// NewOpenTracerFromEnv attempts to initialize a jaeger opentracing.Tracer
// implementation using environment variables for its configuration.  For
// details see https://github.com/jaegertracing/jaeger-client-go/ and
// https://godoc.org/github.com/jaegertracing/jaeger-client-go/config#Configuration.FromEnv
func NewOpenTracerFromEnv(name string, options ...config.Option) (tracer opentracing.Tracer, closer io.Closer, err error) {
	cfg, err := config.FromEnv()
	if err != nil {
		err = fmt.Errorf("error initializing jaeger Configuration from env: %w", err)
		return nil, nil, err
	}

	return cfg.New(name, options...)
}
