package main

import (
	"regexp"
)

type DOIType int

const (
	MATCH_CROSSREF_MODERN_DOI DOIType = iota
	MATCH_CROSSREF_LEGACY_DOI
	MATCH_ANY_DOI
	MATCH_NO_DOI
)

// https://support.crossref.org/hc/en-us/articles/214669823-Constructing-your-identifiers
// places more reasonable limits on values allowed, restricting modern ones to
// suffixes containing "a-z", "A-Z", "0-9" and "-._;()/", with legacy ones
// containing other ASCII characters such as #, +, <, and >.
var doiCrossrefModernPattern = `(10\.\d+(\.\d+)*/[a-zA-Z0-9._;\(\)/\-\+]+)`

// https://support.crossref.org/hc/en-us/articles/214669823-Constructing-your-identifiers
// allows for legacy characters and the implication is that it's ASCII
// characters. It is not specifically stated but we're limiting it to graphical
// characters.
var doiLegacyCrossrefPattern = `(10\.\d+(\.\d+)*/[[:graph]]+)`

// https://www.doi.org/doi_handbook/2_Numbering.html#2.2.2 says A minimum DOI
// pattern consists of a DOI prefix and suffix, with the prefix consisting of a
// prefix '10.' followed by one or more dot separated numbers, and a suffix
// that can basically be anything considered a printable character.
var doiAnyPattern = `(10\.\d+(\.\d+)*/.+)`

// doiMatchPatterns anchor the DOI patterns and are for exact Regexp.Match
// operations
var doiMatchPatterns = []*regexp.Regexp{
	regexp.MustCompile(`^` + doiCrossrefModernPattern + `$`),
	regexp.MustCompile(`^` + doiLegacyCrossrefPattern + `$`),
	regexp.MustCompile(`^` + doiAnyPattern + `$`),
}

// doiMatchPatterns do not anchor the DOI patterns and are for exact
// Regexp.Substring operations
var doiSubstringPatterns = []*regexp.Regexp{
	regexp.MustCompile(doiCrossrefModernPattern),
	regexp.MustCompile(doiLegacyCrossrefPattern),
	regexp.MustCompile(doiAnyPattern),
}

// MatchDOI returns the DOIType of s, which may be MATCH_NO_DOI if no match was
// found.
func MatchDOI(s string) DOIType {
	for i, p := range doiMatchPatterns {
		if p.MatchString(s) {
			return DOIType(i)
		}
	}
	return MATCH_NO_DOI
}

// FindDOI searche s for a substring that matches the DOIType patterns and
// returns the match and its type, or an empty string and MATCH_NO_DOI if none
// is found
func FindDOI(s string) (string, DOIType) {
	for i, p := range doiSubstringPatterns {
		if s := p.FindStringSubmatch(s); s != nil {
			return s[0], DOIType(i)
		}
	}
	return "", MATCH_NO_DOI
}
