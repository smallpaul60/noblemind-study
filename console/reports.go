package main

// Structured analytics reports. The dashboard's existing tiles answer
// "what's happening right now"; the reports answer "who's reading,
// what are they reading, where did they come from, and is it landing."
//
// One handler (handleReports) fans out to several query functions and
// returns a single JSON payload that the dashboard renders into a
// "Reports" panel. Each section is independent — adding or removing
// one is a one-line edit at the bottom of buildReport.

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strings"
)

// Report is the top-level payload returned by /api/nm/reports.
type Report struct {
	Days             int                 `json:"days"`
	GeneratedAt      string              `json:"generated_at"`
	Overview         ReportOverview      `json:"overview"`
	ReturningReaders []ReturningReader   `json:"returning_readers"`
	PerBook          []BookEngagement    `json:"per_book"`
	Discovery        []DiscoveryBucket   `json:"discovery"`
	StandoutSessions []StandoutSession   `json:"standout_sessions"`
	Downloads        []DownloadRecord    `json:"downloads"`
	Audio            []PageEngagement    `json:"audio_engagement"`
	TestThisClaim    []PageEngagement    `json:"test_this_claim"`
}

type ReportOverview struct {
	TotalViews        int            `json:"total_views"`
	UniqueVisitors    int            `json:"unique_visitors"`
	ReturningVisitors int            `json:"returning_visitors"`
	TopCountries      []CountRow     `json:"top_countries"`
	DeviceSplit       map[string]int `json:"device_split"`
}

type CountRow struct {
	Label string `json:"label"`
	Count int    `json:"count"`
}

type ReturningReader struct {
	VisitorHash string   `json:"visitor_hash"`
	Location    string   `json:"location"`
	Device      string   `json:"device"`
	DaysSeen    []string `json:"days_seen"`
	TotalViews  int      `json:"total_views"`
	TotalDwell  int      `json:"total_dwell_seconds"`
	FirstSeen   string   `json:"first_seen"`
	LastSeen    string   `json:"last_seen"`
	TopPaths    []string `json:"top_paths"`
	Downloads   []string `json:"downloads"`
}

type BookEngagement struct {
	Book           string `json:"book"`
	Visitors       int    `json:"visitors"`
	Views          int    `json:"views"`
	TotalDwell     int    `json:"total_dwell_seconds"`
	DeepestChapter string `json:"deepest_chapter"`
	Downloads      int    `json:"downloads"`
}

type DiscoveryBucket struct {
	Bucket   string     `json:"bucket"`
	Visitors int        `json:"visitors"`
	Views    int        `json:"views"`
	Examples []CountRow `json:"examples"`
}

type StandoutSession struct {
	Date        string   `json:"date"`
	VisitorHash string   `json:"visitor_hash"`
	Location    string   `json:"location"`
	Device      string   `json:"device"`
	Views       int      `json:"views"`
	DwellSec    int      `json:"dwell_seconds"`
	FirstSeen   string   `json:"first_seen"`
	LastSeen    string   `json:"last_seen"`
	TopPaths    []string `json:"top_paths"`
}

type DownloadRecord struct {
	Timestamp string `json:"timestamp"`
	File      string `json:"file"`
	FromPage  string `json:"from_page"`
	Visitor   string `json:"visitor_hash"`
	Location  string `json:"location"`
}

type PageEngagement struct {
	Path       string `json:"path"`
	Visitors   int    `json:"visitors"`
	Views      int    `json:"views"`
	TotalDwell int    `json:"total_dwell_seconds"`
	AvgDwell   int    `json:"avg_dwell_seconds"`
}

// handleReports is the HTTP handler. Auth-protected via requireAuth in handlers.go.
func handleReports(w http.ResponseWriter, r *http.Request) {
	days := parsePeriod(r.URL.Query().Get("days"))
	if days <= 0 {
		days = parsePeriod(r.URL.Query().Get("period"))
	}

	report, err := buildReport(days)
	if err != nil {
		log.Printf("reports query error: %v", err)
		http.Error(w, "internal error", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Cache-Control", "no-store")
	json.NewEncoder(w).Encode(report)
}

// buildReport runs every section query in turn. Errors short-circuit and bubble up.
func buildReport(days int) (*Report, error) {
	r := &Report{
		Days:        days,
		GeneratedAt: nowUTC(),
	}

	var err error
	if r.Overview, err = queryOverview(days); err != nil {
		return nil, fmt.Errorf("overview: %w", err)
	}
	if r.ReturningReaders, err = queryReturningReaders(days); err != nil {
		return nil, fmt.Errorf("returning: %w", err)
	}
	if r.PerBook, err = queryPerBook(days); err != nil {
		return nil, fmt.Errorf("per_book: %w", err)
	}
	if r.Discovery, err = queryDiscovery(days); err != nil {
		return nil, fmt.Errorf("discovery: %w", err)
	}
	if r.StandoutSessions, err = queryStandoutSessions(days); err != nil {
		return nil, fmt.Errorf("standout: %w", err)
	}
	if r.Downloads, err = queryDownloads(days); err != nil {
		return nil, fmt.Errorf("downloads: %w", err)
	}
	if r.Audio, err = queryPagePattern(days, "%/audio.html", 20); err != nil {
		return nil, fmt.Errorf("audio: %w", err)
	}
	if r.TestThisClaim, err = queryPagePattern(days, "/test-this-claim/%", 30); err != nil {
		return nil, fmt.Errorf("ttc: %w", err)
	}
	return r, nil
}

func nowUTC() string {
	var s string
	db.QueryRow(`SELECT strftime('%Y-%m-%dT%H:%M:%SZ', 'now')`).Scan(&s)
	return s
}

// ---------------------------------------------------------------------------
// Overview: top-level numbers for the period
// ---------------------------------------------------------------------------

func queryOverview(days int) (ReportOverview, error) {
	var o ReportOverview
	o.DeviceSplit = map[string]int{}

	row := db.QueryRow(fmt.Sprintf(`
		SELECT COUNT(*), COUNT(DISTINCT visitor_hash)
		FROM page_views
		WHERE is_admin=0 AND timestamp >= datetime('now','-%d days')`, days))
	if err := row.Scan(&o.TotalViews, &o.UniqueVisitors); err != nil {
		return o, err
	}

	// Returning: visitor_hash that appears on >= 2 distinct dates in the window.
	row = db.QueryRow(fmt.Sprintf(`
		SELECT COUNT(*) FROM (
			SELECT visitor_hash
			FROM page_views
			WHERE is_admin=0 AND timestamp >= datetime('now','-%d days')
			GROUP BY visitor_hash
			HAVING COUNT(DISTINCT substr(timestamp,1,10)) >= 2
		)`, days))
	row.Scan(&o.ReturningVisitors)

	rows, err := db.Query(fmt.Sprintf(`
		SELECT
			CASE WHEN city != '' AND region != '' THEN city || ', ' || region || ', ' || country
			     WHEN region != '' THEN region || ', ' || country
			     WHEN country != '' THEN country
			     ELSE 'Unknown' END AS loc,
			COUNT(DISTINCT visitor_hash) AS v
		FROM page_views
		WHERE is_admin=0 AND timestamp >= datetime('now','-%d days')
		GROUP BY loc ORDER BY v DESC LIMIT 8`, days))
	if err == nil {
		defer rows.Close()
		for rows.Next() {
			var c CountRow
			rows.Scan(&c.Label, &c.Count)
			o.TopCountries = append(o.TopCountries, c)
		}
	}

	rows, err = db.Query(fmt.Sprintf(`
		SELECT COALESCE(NULLIF(device,''),'Unknown'), COUNT(DISTINCT visitor_hash)
		FROM page_views
		WHERE is_admin=0 AND timestamp >= datetime('now','-%d days')
		GROUP BY device`, days))
	if err == nil {
		defer rows.Close()
		for rows.Next() {
			var k string
			var n int
			rows.Scan(&k, &n)
			o.DeviceSplit[k] = n
		}
	}

	return o, nil
}

// ---------------------------------------------------------------------------
// Returning readers: visitors seen on multiple days in the window
// ---------------------------------------------------------------------------

func queryReturningReaders(days int) ([]ReturningReader, error) {
	rows, err := db.Query(fmt.Sprintf(`
		SELECT visitor_hash, COUNT(*) AS views,
		       COUNT(DISTINCT substr(timestamp,1,10)) AS days_seen,
		       MIN(timestamp), MAX(timestamp)
		FROM page_views
		WHERE is_admin=0 AND timestamp >= datetime('now','-%d days')
		GROUP BY visitor_hash
		HAVING days_seen >= 2
		ORDER BY views DESC, days_seen DESC
		LIMIT 15`, days))
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []ReturningReader
	for rows.Next() {
		var r ReturningReader
		var nDays int
		rows.Scan(&r.VisitorHash, &r.TotalViews, &nDays, &r.FirstSeen, &r.LastSeen)
		out = append(out, r)
		_ = nDays
	}
	rows.Close()

	for i := range out {
		fillReturningReader(&out[i], days)
	}
	return out, nil
}

func fillReturningReader(r *ReturningReader, days int) {
	// Days seen
	dRows, _ := db.Query(`
		SELECT DISTINCT substr(timestamp,1,10) AS d
		FROM page_views
		WHERE visitor_hash = ? AND is_admin=0
		ORDER BY d`, r.VisitorHash)
	if dRows != nil {
		for dRows.Next() {
			var d string
			dRows.Scan(&d)
			r.DaysSeen = append(r.DaysSeen, d)
		}
		dRows.Close()
	}

	// Most representative location and device (last seen)
	db.QueryRow(`
		SELECT
			CASE WHEN city != '' AND region != '' THEN city || ', ' || region || ', ' || country
			     WHEN region != '' THEN region || ', ' || country
			     WHEN country != '' THEN country
			     ELSE 'Unknown' END,
			COALESCE(NULLIF(browser,''),'')|| '/' ||
			COALESCE(NULLIF(os,''),'')     || '/' ||
			COALESCE(NULLIF(device,''),'')
		FROM page_views
		WHERE visitor_hash = ? AND is_admin=0
		ORDER BY timestamp DESC LIMIT 1`, r.VisitorHash).Scan(&r.Location, &r.Device)

	// Total dwell from page_exit events (metadata is duration in seconds as string).
	db.QueryRow(`
		SELECT COALESCE(SUM(CAST(metadata AS INTEGER)), 0)
		FROM events
		WHERE visitor_hash = ? AND event_type = 'page_exit'
		  AND timestamp >= datetime('now', ?)`,
		r.VisitorHash, fmt.Sprintf("-%d days", days)).Scan(&r.TotalDwell)

	// Top 5 paths by view count
	pRows, _ := db.Query(fmt.Sprintf(`
		SELECT path, COUNT(*) AS n
		FROM page_views
		WHERE visitor_hash = ? AND is_admin=0
		  AND timestamp >= datetime('now','-%d days')
		GROUP BY path ORDER BY n DESC LIMIT 5`, days), r.VisitorHash)
	if pRows != nil {
		for pRows.Next() {
			var p string
			var n int
			pRows.Scan(&p, &n)
			r.TopPaths = append(r.TopPaths, fmt.Sprintf("%s (%d)", p, n))
		}
		pRows.Close()
	}

	// Downloads
	dlRows, _ := db.Query(fmt.Sprintf(`
		SELECT metadata FROM events
		WHERE visitor_hash = ? AND event_type='file_download'
		  AND timestamp >= datetime('now','-%d days')
		ORDER BY timestamp`, days), r.VisitorHash)
	if dlRows != nil {
		for dlRows.Next() {
			var m string
			dlRows.Scan(&m)
			r.Downloads = append(r.Downloads, m)
		}
		dlRows.Close()
	}
}

// ---------------------------------------------------------------------------
// Per-book engagement: derived from the first path segment
// ---------------------------------------------------------------------------

// bookFromPath returns the book directory name for a path like
// "/WhyTheDivision/chapter-01.html" -> "WhyTheDivision". Returns ""
// for non-book paths (index, books, principles, study tool, etc.).
func bookFromPath(p string) string {
	if p == "" || p == "/" {
		return ""
	}
	p = strings.TrimPrefix(p, "/")
	idx := strings.IndexByte(p, '/')
	if idx <= 0 {
		return ""
	}
	first := p[:idx]
	// Skip non-book directories
	switch first {
	case "test-this-claim", "maps", "console", "api", "assets", "design-refs",
		"data", "Acts-Enhanced", "StraitWay", "StraitWay-Enhanced":
		return ""
	}
	// Heuristic: book directories use mixed-case or hyphens. Filter out files.
	if strings.Contains(first, ".") {
		return ""
	}
	return first
}

func queryPerBook(days int) ([]BookEngagement, error) {
	// Pull every page view in window with path, visitor, location.
	rows, err := db.Query(fmt.Sprintf(`
		SELECT path, visitor_hash, timestamp
		FROM page_views
		WHERE is_admin=0 AND timestamp >= datetime('now','-%d days')`, days))
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	type bookAgg struct {
		visitors map[string]bool
		views    int
		deepest  string // alphabetically-greatest "chapter-NN.html" seen
	}
	books := map[string]*bookAgg{}

	for rows.Next() {
		var path, vh, ts string
		rows.Scan(&path, &vh, &ts)
		book := bookFromPath(path)
		if book == "" {
			continue
		}
		b, ok := books[book]
		if !ok {
			b = &bookAgg{visitors: map[string]bool{}}
			books[book] = b
		}
		b.visitors[vh] = true
		b.views++
		// Track deepest chapter — naive but useful: the highest chapter-NN seen.
		if strings.Contains(path, "chapter-") {
			seg := path[strings.LastIndex(path, "/")+1:]
			if seg > b.deepest {
				b.deepest = seg
			}
		}
	}
	rows.Close()

	// Total dwell per book (sum of page_exit durations whose path is in this book)
	type dwellKey struct{ book string }
	dwellByBook := map[string]int{}
	dRows, _ := db.Query(fmt.Sprintf(`
		SELECT path, metadata FROM events
		WHERE event_type='page_exit'
		  AND timestamp >= datetime('now','-%d days')`, days))
	if dRows != nil {
		for dRows.Next() {
			var p, m string
			dRows.Scan(&p, &m)
			book := bookFromPath(p)
			if book == "" {
				continue
			}
			var sec int
			fmt.Sscan(m, &sec)
			dwellByBook[book] += sec
		}
		dRows.Close()
	}

	// Downloads per book (metadata holds the file path; first segment = book dir)
	dlByBook := map[string]int{}
	dlRows, _ := db.Query(fmt.Sprintf(`
		SELECT metadata FROM events
		WHERE event_type='file_download'
		  AND timestamp >= datetime('now','-%d days')`, days))
	if dlRows != nil {
		for dlRows.Next() {
			var m string
			dlRows.Scan(&m)
			// metadata may be "FromTheBeginning/FromTheBeginning.pdf" or just "X.pdf"
			if i := strings.IndexByte(m, '/'); i > 0 {
				dlByBook[m[:i]]++
			}
		}
		dlRows.Close()
	}

	out := make([]BookEngagement, 0, len(books))
	for name, b := range books {
		out = append(out, BookEngagement{
			Book:           name,
			Visitors:       len(b.visitors),
			Views:          b.views,
			TotalDwell:     dwellByBook[name],
			DeepestChapter: b.deepest,
			Downloads:      dlByBook[name],
		})
	}
	// Sort by views desc
	for i := 0; i < len(out); i++ {
		for j := i + 1; j < len(out); j++ {
			if out[j].Views > out[i].Views {
				out[i], out[j] = out[j], out[i]
			}
		}
	}
	return out, nil
}

// ---------------------------------------------------------------------------
// Discovery: bucket referrers into Search / Direct / Internal / Social /
// IPFS gateway / Other
// ---------------------------------------------------------------------------

func bucketReferrer(ref string) string {
	r := strings.ToLower(ref)
	if r == "" {
		return "Direct"
	}
	switch {
	case strings.Contains(r, "google."), strings.Contains(r, "bing."),
		strings.Contains(r, "duckduckgo."), strings.Contains(r, "yahoo."),
		strings.Contains(r, "yandex."), strings.Contains(r, "brave."),
		strings.Contains(r, "ecosia."), strings.Contains(r, "kagi.com"):
		return "Search"
	case strings.Contains(r, "noblemind.study"):
		if strings.HasPrefix(r, "ipfs.") || strings.Contains(r, "ipfs.noblemind") {
			return "IPFS gateway"
		}
		return "Internal"
	case strings.Contains(r, "ipfs.io"), strings.Contains(r, "dweb.link"),
		strings.Contains(r, "cf-ipfs.com"):
		return "IPFS gateway"
	case strings.Contains(r, "facebook."), strings.Contains(r, "fb.com"),
		strings.Contains(r, "twitter."), strings.Contains(r, "x.com"),
		strings.Contains(r, "t.co"), strings.Contains(r, "reddit."),
		strings.Contains(r, "linkedin."), strings.Contains(r, "instagram."),
		strings.Contains(r, "youtube."), strings.Contains(r, "youtu.be"):
		return "Social"
	}
	return "Other"
}

func queryDiscovery(days int) ([]DiscoveryBucket, error) {
	rows, err := db.Query(fmt.Sprintf(`
		SELECT referrer, visitor_hash
		FROM page_views
		WHERE is_admin=0 AND timestamp >= datetime('now','-%d days')`, days))
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	type aggBucket struct {
		visitors map[string]bool
		views    int
		domains  map[string]int
	}
	buckets := map[string]*aggBucket{}

	for rows.Next() {
		var ref, vh string
		rows.Scan(&ref, &vh)
		name := bucketReferrer(ref)
		b, ok := buckets[name]
		if !ok {
			b = &aggBucket{visitors: map[string]bool{}, domains: map[string]int{}}
			buckets[name] = b
		}
		b.visitors[vh] = true
		b.views++
		if ref != "" {
			b.domains[ref]++
		}
	}
	rows.Close()

	out := []DiscoveryBucket{}
	for name, b := range buckets {
		// Top 3 example domains
		var examples []CountRow
		for d, n := range b.domains {
			examples = append(examples, CountRow{Label: d, Count: n})
		}
		for i := 0; i < len(examples); i++ {
			for j := i + 1; j < len(examples); j++ {
				if examples[j].Count > examples[i].Count {
					examples[i], examples[j] = examples[j], examples[i]
				}
			}
		}
		if len(examples) > 3 {
			examples = examples[:3]
		}
		out = append(out, DiscoveryBucket{
			Bucket:   name,
			Visitors: len(b.visitors),
			Views:    b.views,
			Examples: examples,
		})
	}
	for i := 0; i < len(out); i++ {
		for j := i + 1; j < len(out); j++ {
			if out[j].Views > out[i].Views {
				out[i], out[j] = out[j], out[i]
			}
		}
	}
	return out, nil
}

// ---------------------------------------------------------------------------
// Standout sessions: a single visitor's activity on a single day,
// where they read deeply (>=5 pages or >=10 minutes dwell)
// ---------------------------------------------------------------------------

func queryStandoutSessions(days int) ([]StandoutSession, error) {
	rows, err := db.Query(fmt.Sprintf(`
		SELECT substr(timestamp,1,10) AS d, visitor_hash, COUNT(*) AS views,
		       MIN(timestamp), MAX(timestamp)
		FROM page_views
		WHERE is_admin=0 AND timestamp >= datetime('now','-%d days')
		GROUP BY d, visitor_hash
		HAVING views >= 5
		ORDER BY views DESC LIMIT 15`, days))
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []StandoutSession
	for rows.Next() {
		var s StandoutSession
		rows.Scan(&s.Date, &s.VisitorHash, &s.Views, &s.FirstSeen, &s.LastSeen)
		out = append(out, s)
	}
	rows.Close()

	for i := range out {
		s := &out[i]
		db.QueryRow(`
			SELECT
				CASE WHEN city != '' AND region != '' THEN city || ', ' || region || ', ' || country
				     WHEN region != '' THEN region || ', ' || country
				     WHEN country != '' THEN country
				     ELSE 'Unknown' END,
				COALESCE(NULLIF(browser,''),'')|| '/' ||
				COALESCE(NULLIF(os,''),'')     || '/' ||
				COALESCE(NULLIF(device,''),'')
			FROM page_views
			WHERE visitor_hash = ? AND substr(timestamp,1,10)=?
			ORDER BY timestamp DESC LIMIT 1`, s.VisitorHash, s.Date).Scan(&s.Location, &s.Device)

		db.QueryRow(`
			SELECT COALESCE(SUM(CAST(metadata AS INTEGER)), 0)
			FROM events
			WHERE visitor_hash = ? AND event_type='page_exit'
			  AND substr(timestamp,1,10)=?`, s.VisitorHash, s.Date).Scan(&s.DwellSec)

		pRows, _ := db.Query(`
			SELECT path, COUNT(*) FROM page_views
			WHERE visitor_hash=? AND substr(timestamp,1,10)=?
			GROUP BY path ORDER BY COUNT(*) DESC LIMIT 5`, s.VisitorHash, s.Date)
		if pRows != nil {
			for pRows.Next() {
				var p string
				var n int
				pRows.Scan(&p, &n)
				s.TopPaths = append(s.TopPaths, fmt.Sprintf("%s (%d)", p, n))
			}
			pRows.Close()
		}
	}
	return out, nil
}

// ---------------------------------------------------------------------------
// Downloads: every file_download event in the window
// ---------------------------------------------------------------------------

func queryDownloads(days int) ([]DownloadRecord, error) {
	rows, err := db.Query(fmt.Sprintf(`
		SELECT timestamp, metadata, path, visitor_hash,
			CASE WHEN city != '' AND region != '' THEN city || ', ' || region || ', ' || country
			     WHEN region != '' THEN region || ', ' || country
			     WHEN country != '' THEN country
			     ELSE 'Unknown' END
		FROM events
		WHERE event_type='file_download'
		  AND timestamp >= datetime('now','-%d days')
		ORDER BY timestamp DESC LIMIT 100`, days))
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []DownloadRecord
	for rows.Next() {
		var d DownloadRecord
		rows.Scan(&d.Timestamp, &d.File, &d.FromPage, &d.Visitor, &d.Location)
		out = append(out, d)
	}
	return out, nil
}

// ---------------------------------------------------------------------------
// Page-pattern engagement: used for audio.html and /test-this-claim/
// ---------------------------------------------------------------------------

func queryPagePattern(days int, pattern string, limit int) ([]PageEngagement, error) {
	rows, err := db.Query(fmt.Sprintf(`
		SELECT path, COUNT(*) AS views, COUNT(DISTINCT visitor_hash) AS visitors
		FROM page_views
		WHERE is_admin=0
		  AND path LIKE ?
		  AND timestamp >= datetime('now','-%d days')
		GROUP BY path
		ORDER BY views DESC LIMIT %d`, days, limit), pattern)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []PageEngagement
	for rows.Next() {
		var p PageEngagement
		rows.Scan(&p.Path, &p.Views, &p.Visitors)
		out = append(out, p)
	}
	rows.Close()

	// Add dwell per path
	for i := range out {
		var sum, count int
		db.QueryRow(fmt.Sprintf(`
			SELECT COALESCE(SUM(CAST(metadata AS INTEGER)),0), COUNT(*)
			FROM events
			WHERE event_type='page_exit'
			  AND path = ?
			  AND timestamp >= datetime('now','-%d days')`, days), out[i].Path).Scan(&sum, &count)
		out[i].TotalDwell = sum
		if count > 0 {
			out[i].AvgDwell = sum / count
		}
	}
	return out, nil
}
