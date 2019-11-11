package main

import (
	"context"
	"fmt"
	"io"
	"log"
	"reflect"
	"sort"
	"strings"

	"github.com/gocql/gocql"
	"github.com/highwire/cqlbind"
)

func normalizeF1000SocialData(ctx context.Context, session *gocql.Session, meta *Meta, ch chan string, errc chan error) error {

	// cleanup processes a set of entries that share the same normalized
	// (lower case) primary key
	cleanup := func(pk []string, entries []map[string]interface{}) error {

		var set F1000SocialDatas
		for i := range entries {
			set = append(set, F1000SocialData(entries[i]))
		}

		merged := make(map[string]interface{})
		sort.Sort(set)

		invalidDOI := false
		for i := (len(set) - 1); i >= 0; i-- {
			for _, col := range meta.Columns {
				v, ok := set[i][col.Name]
				if !ok {
					continue
				}

				if col.Name == "doi" {
					if _, ok := merged[col.Name]; ok {
						continue
					}

					s, _ := cqlbind.StripBOM(cqlbind.UTF8_BOM, v.(string))
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
					// other fields are counters, whichever
					// had the higher count wins
					if x, ok := merged[col.Name]; ok {
						switch o := x.(type) {
						case int:
							if v.(int) > o {
								merged[col.Name] = v
							}
						case int64:
							if v.(int64) > o {
								merged[col.Name] = v
							}
						case float32:
							if v.(float32) > o {
								merged[col.Name] = v
							}
						case float64:
							if v.(float64) > o {
								merged[col.Name] = v
							}
						}
					}
				}
			}
		}

		// compute what's been modified from the last record in set
		modified, pkmod := modified(meta, set[len(set)-1], merged)

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

		// if nothing has changed and set is 1 item, we're done
		if len(modified) == 0 && len(set) == 1 {
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

type F1000SocialDatas []F1000SocialData

func (p F1000SocialDatas) Len() int           { return len(p) }
func (p F1000SocialDatas) Less(i, j int) bool { return p[i].TotalScore() < p[j].TotalScore() }
func (p F1000SocialDatas) Swap(i, j int)      { p[i], p[j] = p[j], p[i] }

type F1000SocialData map[string]interface{}

func (p F1000SocialData) TotalScore() int {
	if v, ok := p["total_score"]; ok {
		if n, ok := v.(int); ok {
			return n
		}
	}
	return 0
}
