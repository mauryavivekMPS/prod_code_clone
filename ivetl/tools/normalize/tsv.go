package main

import (
	"strings"

	"github.com/gocql/gocql"
	"github.com/highwire/cqlbind"
)

// TsvPublisher extends cqlbind.IvTsvPublisher and additionally cleans up the
// primary key value, stripping any BOM or leading/trailing whitespace
type TsvPublisher struct {
	cqlbind.IvTsvPublisher
}

func (p TsvPublisher) Row(colinfo []gocql.ColumnInfo, m map[string]interface{}) ([]string, error) {
	row, err := p.IvTsvPublisher.Row(colinfo, m)
	if err != nil {
		return nil, err
	}

	for i := 0; i < len(row)-1; i++ {
		if s, ok := cqlbind.StripBOM(cqlbind.UTF8_BOM, row[i]); ok {
			row[i] = s
		}
		row[i] = strings.TrimSpace(row[i])
	}

	return row, nil
}
