package main

import (
	"fmt"
	"github.com/gocql/gocql"
)

type Meta struct {
	Table      *gocql.TableMetadata
	PrimaryKey map[string]bool
	Columns    []gocql.ColumnInfo
}

func NewMeta(session *gocql.Session, keyspace, table string) (*Meta, error) {
	p := &Meta{}
	ok := false

	km, err := session.KeyspaceMetadata(keyspace)
	if err != nil {
		return nil, fmt.Errorf("unable to retrieve meta for keyspace %s: %w", keyspace, err)
	}

	p.Table, ok = km.Tables[table]
	if !ok {
		return nil, fmt.Errorf("unable to retrieve meta for table %s.%s", keyspace, table)
	}

	p.PrimaryKey = map[string]bool{}
	for _, colmeta := range p.Table.PartitionKey {
		p.PrimaryKey[colmeta.Name] = true
	}
	for _, colmeta := range p.Table.ClusteringColumns {
		p.PrimaryKey[colmeta.Name] = true
	}

	return p, nil
}

func (p *Meta) WithColumns(columns []gocql.ColumnInfo) *Meta {
	return &Meta{
		Table:      p.Table,
		PrimaryKey: p.PrimaryKey,
		Columns:    columns,
	}
}
