package main

import (
	"flag"
	"fmt"
	"os"
	"path"
	"strings"
)

// if execute is set to true then the cql will be sent to the brokers,
// otherwise it is merely printed to stdout
var execute bool = false

// if deleteInvalidDOI is set to true and execute is true then rows may be
// deleted if they contain invalid DOI
var deleteInvalidDOI bool = false

func usage() {
	name := path.Base(os.Args[0])
	fmt.Printf(strings.Join([]string{
		`usage: %s <parameters>`,
		`parameters:`,
		`	-brokers <hosts>[,...]`,
		`		one or more comma-separated host names of the bbroker to connect to (required)`,
		`	-target <keyspace>.<table>`,
		`		period-separated cassandra keyspace and table to process (required)`,
		`	-constrain <cql>`,
		`		cql to constrain selection, e.g., "WHERE pk1 = 'abc' AND LIMIT 5" (optional)`,
		`	-execute`,
		`		execute the update instead of just printing out the CQL to stdout (optional)`,
		`	-delete-invalid-doi`,
		`		delete rows that contain invalid DOI, otherwise just log them (optional)`,
	}, "\n")+"\n", name)
}

func main() {
	// comma separated list of [host]:port addresses to connect to
	var brokers string

	// keyspace and table, separated by a period
	var target string

	// optional cql to constrain query
	var constrain string

	// help flag
	var help bool

	// set help usage
	flag.Usage = usage

	// -brokers host[:port][,...]
	flag.StringVar(&brokers, "brokers", "", "")

	// -target keyspace.table
	flag.StringVar(&target, "target", "", "")

	// -constrain <cql>
	flag.StringVar(&constrain, "constrain", "", "")

	// -execute
	flag.BoolVar(&execute, "execute", false, "execute the updates instead if printing them out")

	// -delete-invalid-doi-
	flag.BoolVar(&deleteInvalidDOI, "delete-invalid-doi", false, "delete invalid DOI instead of just logging them")

	// -h, -help, or --help
	flag.BoolVar(&help, "h", false, "print usage")
	flag.BoolVar(&help, "help", false, "print usage")
	flag.BoolVar(&help, "--help", false, "print usage")

	flag.Parse()

	// usage help requested, print it and exit
	if help {
		usage()
		os.Exit(0)
	}

	// convert brokers to hosts []string
	var hosts []string
	for _, s := range strings.Split(brokers, ",") {
		if s = strings.TrimSpace(s); len(s) > 0 {
			hosts = append(hosts, s)
		}
	}
	if len(hosts) == 0 {
		fmt.Fprintf(os.Stderr, "error: at least one -brokers value must be provided\n")
		usage()
		os.Exit(1)
	}

	// convert target to keyspace, table string
	var keyspace, table string
	if v := strings.Split(target, "."); len(v) == 2 {
		keyspace, table = strings.TrimSpace(v[0]), strings.TrimSpace(v[1])
	}
	if keyspace == "" || table == "" {
		fmt.Fprintf(os.Stderr, "error: a -target value must provided and it must be in the form keyspace.table\n")
		usage()
		os.Exit(1)
	}

	// process the requested table columns
	if err := normalize(hosts, keyspace, table, constrain); err != nil {
		fmt.Fprintf(os.Stderr, "%v\n", err)
		os.Exit(1)
	}

	os.Exit(0)
}
