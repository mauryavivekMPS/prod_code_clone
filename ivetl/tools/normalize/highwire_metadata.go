package main

import (
	"context"
	"fmt"
	"io"
	"log"
	"reflect"
	"strings"

	"github.com/gocql/gocql"
	"github.com/highwire/cqlbind"
)

func normalizeHighwireMetadata(ctx context.Context, session *gocql.Session, meta *Meta, ch chan string, errc chan error) error {

	// normalize journal_doi
	cleanup := func(pk []string, set []map[string]interface{}) error {

		merged := make(map[string]interface{})

		invalidDOI := false
		for i := (len(set) - 1); i >= 0; i-- {
			for _, col := range meta.Columns {
				if _, ok := merged[col.Name]; ok {
					continue
				}

				v, ok := set[i][col.Name]
				if !ok {
					continue
				}

				switch x := v.(type) {
				case string:
					if col.Name == "journal_doi" {
						s, _ := cqlbind.StripBOM(cqlbind.UTF8_BOM, x)
						s = strings.ToLower(strings.TrimSpace(s))

						doiType := MatchDOI(s)
						if doiType == MATCH_NO_DOI {
							doi, doiType := FindDOI(s)
							if doiType != MATCH_NO_DOI {
								s = doi
							} else {
								log.Printf("invalid DOI for %s.%s row %v: %s",
									col.Keyspace, col.Table, pk, s)
								invalidDOI = true
							}
						}

						merged[col.Name] = s
					} else {
						merged[col.Name] = v
					}
				default:
					merged[col.Name] = v
				}
			}
		}

		// compute what's been modified from the last record in set
		modified, pkmod := modified(meta, set[len(set)-1], merged)
		// if nothing has changed and set is 1 item, we're done
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

		if invalidDOI && deleteInvalidDOI {
			for i := range set {
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
			return nil
		}

		// delete duplicates and insert the lowercase version
		for i := 0; i < len(set); i++ {
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
