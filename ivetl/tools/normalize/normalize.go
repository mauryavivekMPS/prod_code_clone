package main

import (
	"context"
	"fmt"
	"time"

	"github.com/gocql/gocql"
	"github.com/highwire/cqlbind"
)

// normalizerFn defines a function that will be used to clean up a row from a
// keyspace.table
type normalizerFn func(context.Context, *gocql.Session, *Meta, chan string, chan error) error

// normalizerMap maps keyspace.table to the appropriate normalizerFn that will
// perform the actual cleanup work
var normalizerMap = map[string]normalizerFn{
	"impactvizor.article_citations":        normalizeArticleCitations,
	"impactvizor.altmetrics_social_data":   normalizeAltmetricsSocialData,
	"impactvizor.f1000_social_data":        normalizeF1000SocialData,
	"impactvizor.highwire_metadata":        normalizeHighwireMetadata,
	"impactvizor.published_article_values": normalizePublishedArticleValues,
}

// printFn is a no-op implementation of normalizerFn that simply prints to
// stdout
func printFn(ctx context.Context, session *gocql.Session, meta *Meta, ch chan string, errc chan error) error {
	for {
		select {
		case <-ctx.Done():
			return nil
		case s, ok := <-ch:
			if !ok {
				return nil
			}
			fmt.Println(s)
		case err, ok := <-errc:
			if ok {
				return err
			}
		}
	}
}

// normalize process every row in a specified keyspace.table and passes the
// results off to the appropriate normalizerFn.  If no normalizerFn has been
// mapped for the keyspace.table in normalizerMap then the default printFn will
// be used.
func normalize(hosts []string, keyspace, table, constrain string) (err error) {
	defer func() {
		if r := recover(); r != nil {
			err = fmt.Errorf("panic encountered: %s", r)
		}
	}()

	cfg := gocql.NewCluster(hosts...)

	// since we're doing huge selects, potentially iterating all rows, set
	// a long timeout
	cfg.Timeout = time.Minute

	session, err := cfg.CreateSession()
	if err != nil {
		return fmt.Errorf("error initializing new cassandra session: %w", err)
	}
	defer session.Close()

	// select the rows to scan, by default select all rows, but optionally
	// apply a WHERE or LIMIT constraint if one as provided.
	var query *gocql.Query
	if constrain == "" {
		query = session.Query(fmt.Sprintf("SELECT * FROM %s.%s", keyspace, table))
		defer query.Release()
	} else {
		query = session.Query(fmt.Sprintf("SELECT * FROM %s.%s %s", keyspace, table, constrain))
		defer query.Release()
	}

	meta, err := NewMeta(session, keyspace, table)
	if err != nil {
		return fmt.Errorf("error reading meta from cassandra: %w", err)
	}

	// setup the context, enable sorting
	ctx, cancelFn := context.WithCancel(context.Background())
	ctx = context.WithValue(ctx, "sort", true)
	ctx = context.WithValue(ctx, "sort.ci", true)
	ctx = context.WithValue(ctx, "sort.dir", "/var/tmp")
	defer cancelFn()

	// set up the normalizer function, if none is provided default to just
	// printing out the lines
	normalizerFn, ok := normalizerMap[fmt.Sprintf("%s.%s", keyspace, table)]
	if !ok {
		normalizerFn = printFn
	}

	// start processing the results
	itr := query.Iter()

	meta = meta.WithColumns(itr.Columns())

	tsv := TsvPublisher{}
	tsv.PrimaryKey = meta.PrimaryKey

	sorted, errc := cqlbind.Tsv(ctx, itr, tsv)

	return normalizerFn(ctx, session, meta, sorted, errc)
}
