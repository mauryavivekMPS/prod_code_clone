package main

import (
	"context"
	"fmt"
	"io"
	"reflect"
	"regexp"
	"sort"
	"strings"
	"time"

	"github.com/gocql/gocql"
	"github.com/highwire/cqlbind"
)

func modified(meta *Meta, original, merged map[string]interface{}) (modified map[string]interface{}, pkmod bool) {
	modified = make(map[string]interface{})
	for k, ov := range original {
		if nv, ok := merged[k]; ok {
			if !reflect.DeepEqual(ov, nv) {
				if meta.PrimaryKey[k] {
					pkmod = true
				}
				modified[k] = nv
			}
		}
	}
	return modified, pkmod
}

func normalizeArticleCitations(ctx context.Context, session *gocql.Session, meta *Meta, ch chan string, errc chan error) error {

	// cleanup processes a set of entries that share the same normalized
	// (lower case) primary key
	cleanup := func(pk []string, entries []map[string]interface{}) error {

		var set ArticleCitations
		for i := range entries {
			set = append(set, ArticleCitation(entries[i]))
		}

		// sort the set by criteria laid out in ArticleCitations.Less,
		// then process then from highest index to lowest to determine
		// what we think the final row should look like, storing that
		// into the map 'merged'
		merged := make(map[string]interface{})
		sort.Sort(set)
		for i := (len(set) - 1); i >= 0; i-- {
			for _, col := range meta.Columns {

				// once a key has been set, keep its value
				if _, ok := merged[col.Name]; ok {
					continue
				}

				// normalize values
				switch v := set[i][col.Name].(type) {
				case string:
					// strip leading BOM and any leading or
					// trailing whitespace
					s, _ := cqlbind.StripBOM(cqlbind.UTF8_BOM, v)
					s = strings.TrimSpace(s)

					// for primary keys we want to
					// lowercase the DOI values
					if meta.PrimaryKey[col.Name] {
						switch col.Name {
						case "article_doi", "citation_doi":
							s = strings.ToLower(s)
						}
					}
					merged[col.Name] = s
				case time.Time:
					if !v.IsZero() {
						merged[col.Name] = v
					}
				default:
					merged[col.Name] = v
				}
			}
		}
		// compute what's been modified from the last record in set
		modified, pkmod := modified(meta, set[len(set)-1], merged)

		// if nothing has changed and set is len 1 then there is
		// nothing to do
		if len(modified) == 0 && len(set) == 1 {
			return nil
		}

		delete_stmt, delete_bind, err := cqlbind.Delete(
			meta.Columns, meta.PrimaryKey)
		if err != nil {
			return fmt.Errorf("error initializing delete statement: %w", err)
		}

		insert_stmt, insert_bind, err := cqlbind.Insert(
			meta.Columns, meta.PrimaryKey)
		if err != nil {
			return fmt.Errorf("error initializing insert statement: %w", err)
		}

		update_stmt, update_bind, err := cqlbind.Update(
			meta.Columns, meta.PrimaryKey, modified)
		if err != nil {
			return fmt.Errorf("error initializing update statement: %w", err)
		}

		for i := 0; i < len(set); i++ {
			// anything up to the penultimate entry can be deleted
			if i < (len(set) - 1) {
				col, val := delete_bind(set[i], nil)
				dq := session.Query(delete_stmt, val...)
				if execute {
					if err := dq.Exec(); err != nil {
						return fmt.Errorf("unable to execute query %v: %w", dq, err)
					}
				} else {
					s, err := cqlbind.Sprintf(dq.Statement(), col, val)
					if err != nil {
						return fmt.Errorf("error parsing DELETE statement %s: %w",
							dq.Statement(), err)
					} else {
						fmt.Println(s)
					}
				}
			}

			// if the primary key was modified we need to delete
			// then insert, otherwise we can just perform an
			// update.
			if pkmod {
				col, val := delete_bind(set[i], nil)
				dq := session.Query(delete_stmt, val...)
				if execute {
					if err := dq.Exec(); err != nil {
						return fmt.Errorf("unable to execute query %v: %w", dq, err)
					}
				} else {
					s, err := cqlbind.Sprintf(dq.Statement(), col, val)
					if err != nil {
						return fmt.Errorf("error parsing DELETE statement %s: %w",
							dq.Statement(), err)
					} else {
						fmt.Println(s)
					}
				}

				col, val = insert_bind(set[i], merged)
				iq := session.Query(insert_stmt, val...)
				if execute {
					if err := iq.Exec(); err != nil {
						return fmt.Errorf("unable to execute query %v: %w", iq, err)
					}
				} else {
					s, err := cqlbind.Sprintf(iq.Statement(), col, val)
					if err != nil {
						return fmt.Errorf("error parsing INSERT statement %s: %w",
							iq.Statement(), err)
					} else {
						fmt.Println(s)
					}
				}
			} else if len(modified) > 0 {
				col, val := update_bind(set[i], modified)
				uq := session.Query(update_stmt, val...)
				if execute {
					if err := uq.Exec(); err != nil {
						return fmt.Errorf("unable to execute query %v: %w", uq, err)
					}
				} else {
					s, err := cqlbind.Sprintf(uq.Statement(), col, val)
					if err != nil {
						return fmt.Errorf("error parsing UPDATE statement %s: %w",
							uq.Statement(), err)
					} else {
						fmt.Println(s)
					}
				}
			}
		}

		return nil
	}

	// sets will gather together all the entries that share the same pk
	// once it has been normalized
	var sets []map[string]interface{}

	// prev records the last pk seen before the current one - if it changes
	// then, since our entries are sorted by pk, we know we've collected
	// any duplicates and can send them off for processing
	var prev []string

	r := cqlbind.NewIvTsvReader(ctx, meta.Columns, ch, errc)
	for {
		curr, entry, err := r.Read()
		if err != nil {
			if err != io.EOF {
				return err
			}
			break
		}

		for i := range curr {
			curr[i] = strings.ToLower(curr[i])
		}

		if len(sets) != 0 && !reflect.DeepEqual(curr, prev) {
			if err := cleanup(prev, sets); err != nil {
				return err
			}
			sets = sets[0:0]
		}

		sets = append(sets, entry)
		if prev == nil {
			prev = make([]string, len(curr))
		}
		copy(prev, curr)
	}
	if len(sets) != 0 {
		if err := cleanup(prev, sets); err != nil {
			return err
		}
	}

	return nil
}

// scopusRegex matches Scopus ID patterns
// examples:
// - S0305417917302140
// - S0828282X12015498
// - 1-s2.0-0005276089900568
// - 2-s2.0-85032793922
var scopusRegex = regexp.MustCompile(`^([12]-[Ss][0-9]\.[0-9]-[Ss]?[0-9]+|[Ss][0-9]+[Xx]?[0-9]+)$`)

// magRegex matches Microsoft Academic Graph ID patterns
// examples:
// - 2965451962
// - 2898202428
// - 2606489083
var magRegex = regexp.MustCompile(`^[0-9]+$`)

// zeroTime is used to indicate no valid value
var zeroTime = time.Time{}

type ArticleCitations []ArticleCitation

// Swap two positions in the set
func (p ArticleCitations) Swap(i, j int) { p[i], p[j] = p[j], p[i] }

// Len returns the length of the set
func (p ArticleCitations) Len() int { return len(p) }

// Less will order ArticleCitation by the following criteria
// when used in sort.Sort:
//
// - Scopus before MAG
// - Crossref before MAG
// - Updated time from oldest to newest
//
// The set ordered by this criteria should basically be in "historical" order,
// with the oldest entries first (Scopus), then new newer (MAG) entries, with
// MAG preferred over Crossref.  Any remaining ties are broken by Updated time,
// with the most recent updates being last.
func (p ArticleCitations) Less(i, j int) bool {
	a, b := p[i], p[j]

	if a.HasScopusID() && b.HasMagID() {
		return true
	}

	if a.CrossRefSourced() && !b.CrossRefSourced() {
		return true
	}

	return a.Updated().Before(b.Updated())
}

type ArticleCitation map[string]interface{}

func (p ArticleCitation) HasScopusID() bool {
	if v, ok := p["citation_scopus_id"]; ok {
		if s, ok := v.(string); ok {
			return scopusRegex.MatchString(s)
		}
	}
	return false
}

func (p ArticleCitation) HasMagID() bool {
	if v, ok := p["citation_scopus_id"]; ok {
		if s, ok := v.(string); ok {
			return magRegex.MatchString(s)
		}
	}
	return false
}

func (p ArticleCitation) CrossRefSourced() bool {
	if v, ok := p["citation_scopus_source"]; ok {
		if b, ok := v.(bool); ok {
			return b
		}
	}
	return true
}

func (p ArticleCitation) Updated() time.Time {
	if v, ok := p["updated"]; ok {
		if t, ok := v.(time.Time); ok {
			return t
		}
	}
	return zeroTime
}
