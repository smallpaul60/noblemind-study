package main

import (
	"database/sql"
	"fmt"
	"log"
	"strings"
	"time"

	_ "modernc.org/sqlite"
)

var db *sql.DB

func initDB(path string) error {
	var err error
	db, err = sql.Open("sqlite", path)
	if err != nil {
		return fmt.Errorf("open database: %w", err)
	}

	// SQLite pragmas for performance
	pragmas := []string{
		"PRAGMA journal_mode=WAL",
		"PRAGMA synchronous=NORMAL",
		"PRAGMA busy_timeout=5000",
		"PRAGMA cache_size=-20000",
		"PRAGMA foreign_keys=ON",
	}
	for _, p := range pragmas {
		if _, err := db.Exec(p); err != nil {
			return fmt.Errorf("pragma %q: %w", p, err)
		}
	}

	if err := createSchema(); err != nil {
		return err
	}
	return migrateSchema()
}

func createSchema() error {
	schema := `
	CREATE TABLE IF NOT EXISTS page_views (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
		path TEXT NOT NULL,
		referrer TEXT NOT NULL DEFAULT '',
		visitor_hash TEXT NOT NULL,
		ip_address TEXT NOT NULL DEFAULT '',
		country TEXT NOT NULL DEFAULT '',
		region TEXT NOT NULL DEFAULT '',
		city TEXT NOT NULL DEFAULT '',
		device TEXT NOT NULL DEFAULT '',
		browser TEXT NOT NULL DEFAULT '',
		os TEXT NOT NULL DEFAULT '',
		screen TEXT NOT NULL DEFAULT ''
	);

	CREATE TABLE IF NOT EXISTS events (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
		event_type TEXT NOT NULL,
		visitor_hash TEXT NOT NULL,
		metadata TEXT NOT NULL DEFAULT ''
	);

	CREATE TABLE IF NOT EXISTS daily_aggregates (
		date TEXT NOT NULL,
		path TEXT NOT NULL DEFAULT '',
		views INTEGER NOT NULL DEFAULT 0,
		unique_visitors INTEGER NOT NULL DEFAULT 0,
		PRIMARY KEY (date, path)
	);

	CREATE TABLE IF NOT EXISTS daily_salt (
		date TEXT PRIMARY KEY,
		salt TEXT NOT NULL
	);

	CREATE INDEX IF NOT EXISTS idx_pv_timestamp ON page_views(timestamp);
	CREATE INDEX IF NOT EXISTS idx_pv_visitor ON page_views(visitor_hash);
	CREATE INDEX IF NOT EXISTS idx_pv_path ON page_views(path);
	CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
	CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
	CREATE INDEX IF NOT EXISTS idx_agg_date ON daily_aggregates(date);
	`
	_, err := db.Exec(schema)
	return err
}

// migrateSchema adds columns that may not exist in older databases.
func migrateSchema() error {
	migrations := []string{
		`ALTER TABLE page_views ADD COLUMN ip_address TEXT NOT NULL DEFAULT ''`,
		`ALTER TABLE page_views ADD COLUMN region TEXT NOT NULL DEFAULT ''`,
		`ALTER TABLE page_views ADD COLUMN city TEXT NOT NULL DEFAULT ''`,
	}
	for _, m := range migrations {
		// Ignore "duplicate column" errors for idempotency
		_, err := db.Exec(m)
		if err != nil && !strings.Contains(err.Error(), "duplicate column") {
			log.Printf("migration skipped: %v", err)
		}
	}
	return nil
}

// InsertPageView records a page view.
func InsertPageView(path, referrer, visitorHash, ipAddress, country, region, city, device, browser, os, screen string) error {
	_, err := db.Exec(
		`INSERT INTO page_views (path, referrer, visitor_hash, ip_address, country, region, city, device, browser, os, screen)
		 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
		path, referrer, visitorHash, ipAddress, country, region, city, device, browser, os, screen,
	)
	return err
}

// InsertEvent records a discrete event.
func InsertEvent(eventType, visitorHash, metadata string) error {
	_, err := db.Exec(
		`INSERT INTO events (event_type, visitor_hash, metadata) VALUES (?, ?, ?)`,
		eventType, visitorHash, metadata,
	)
	return err
}

// StatsResult holds dashboard data.
type StatsResult struct {
	TotalViews     int              `json:"total_views"`
	UniqueVisitors int              `json:"unique_visitors"`
	ActiveNow      int              `json:"active_now"`
	TimeSeries     []TimePoint      `json:"time_series"`
	TopPages       []PathCount      `json:"top_pages"`
	TopReferrers   []PathCount      `json:"top_referrers"`
	Browsers       []PathCount      `json:"browsers"`
	Devices        []PathCount      `json:"devices"`
	OSStats        []PathCount      `json:"os_stats"`
	Countries      []PathCount      `json:"countries"`
	Events         []EventSummary   `json:"events"`
	Screens        []PathCount      `json:"screens"`
}

type TimePoint struct {
	Date  string `json:"date"`
	Views int    `json:"views"`
	Uniq  int    `json:"uniq"`
}

type PathCount struct {
	Name  string `json:"name"`
	Count int    `json:"count"`
}

type EventSummary struct {
	Type  string `json:"type"`
	Count int    `json:"count"`
}

// QueryStats returns dashboard stats for the given number of days.
func QueryStats(days int) (*StatsResult, error) {
	since := time.Now().UTC().AddDate(0, 0, -days).Format("2006-01-02T15:04:05Z")
	result := &StatsResult{}

	// Total views
	row := db.QueryRow(`SELECT COUNT(*) FROM page_views WHERE timestamp >= ?`, since)
	row.Scan(&result.TotalViews)

	// Unique visitors
	row = db.QueryRow(`SELECT COUNT(DISTINCT visitor_hash) FROM page_views WHERE timestamp >= ?`, since)
	row.Scan(&result.UniqueVisitors)

	// Active now (last 30 minutes)
	thirtyAgo := time.Now().UTC().Add(-30 * time.Minute).Format("2006-01-02T15:04:05Z")
	row = db.QueryRow(`SELECT COUNT(DISTINCT visitor_hash) FROM page_views WHERE timestamp >= ?`, thirtyAgo)
	row.Scan(&result.ActiveNow)

	// Time series (per day)
	rows, err := db.Query(`
		SELECT date(timestamp) as d, COUNT(*) as views, COUNT(DISTINCT visitor_hash) as uniq
		FROM page_views WHERE timestamp >= ?
		GROUP BY d ORDER BY d`, since)
	if err == nil {
		defer rows.Close()
		for rows.Next() {
			var tp TimePoint
			rows.Scan(&tp.Date, &tp.Views, &tp.Uniq)
			result.TimeSeries = append(result.TimeSeries, tp)
		}
	}

	// Top pages
	result.TopPages = queryPathCounts(`
		SELECT path, COUNT(*) as c FROM page_views WHERE timestamp >= ?
		GROUP BY path ORDER BY c DESC LIMIT 20`, since)

	// Top referrers
	result.TopReferrers = queryPathCounts(`
		SELECT referrer, COUNT(*) as c FROM page_views WHERE timestamp >= ? AND referrer != ''
		GROUP BY referrer ORDER BY c DESC LIMIT 20`, since)

	// Browsers
	result.Browsers = queryPathCounts(`
		SELECT browser, COUNT(*) as c FROM page_views WHERE timestamp >= ? AND browser != ''
		GROUP BY browser ORDER BY c DESC LIMIT 10`, since)

	// Devices
	result.Devices = queryPathCounts(`
		SELECT device, COUNT(*) as c FROM page_views WHERE timestamp >= ? AND device != ''
		GROUP BY device ORDER BY c DESC LIMIT 10`, since)

	// OS
	result.OSStats = queryPathCounts(`
		SELECT os, COUNT(*) as c FROM page_views WHERE timestamp >= ? AND os != ''
		GROUP BY os ORDER BY c DESC LIMIT 10`, since)

	// Countries
	result.Countries = queryPathCounts(`
		SELECT country, COUNT(*) as c FROM page_views WHERE timestamp >= ? AND country != ''
		GROUP BY country ORDER BY c DESC LIMIT 20`, since)

	// Screens
	result.Screens = queryPathCounts(`
		SELECT screen, COUNT(*) as c FROM page_views WHERE timestamp >= ? AND screen != ''
		GROUP BY screen ORDER BY c DESC LIMIT 10`, since)

	// Events
	eventRows, err := db.Query(`
		SELECT event_type, COUNT(*) as c FROM events WHERE timestamp >= ?
		GROUP BY event_type ORDER BY c DESC`, since)
	if err == nil {
		defer eventRows.Close()
		for eventRows.Next() {
			var es EventSummary
			eventRows.Scan(&es.Type, &es.Count)
			result.Events = append(result.Events, es)
		}
	}

	return result, nil
}

func queryPathCounts(query, since string) []PathCount {
	rows, err := db.Query(query, since)
	if err != nil {
		return nil
	}
	defer rows.Close()
	var results []PathCount
	for rows.Next() {
		var pc PathCount
		rows.Scan(&pc.Name, &pc.Count)
		results = append(results, pc)
	}
	return results
}

// RealtimeResult holds active visitors data.
type RealtimeResult struct {
	ActiveVisitors int         `json:"active_visitors"`
	ActivePages    []PathCount `json:"active_pages"`
}

// QueryRealtime returns last-30-minute activity.
func QueryRealtime() (*RealtimeResult, error) {
	since := time.Now().UTC().Add(-30 * time.Minute).Format("2006-01-02T15:04:05Z")
	result := &RealtimeResult{}

	row := db.QueryRow(`SELECT COUNT(DISTINCT visitor_hash) FROM page_views WHERE timestamp >= ?`, since)
	row.Scan(&result.ActiveVisitors)

	result.ActivePages = queryPathCounts(`
		SELECT path, COUNT(*) as c FROM page_views WHERE timestamp >= ?
		GROUP BY path ORDER BY c DESC LIMIT 10`, since)

	return result, nil
}

// RecentVisit represents a single page view for the live log.
type RecentVisit struct {
	Timestamp   string `json:"timestamp"`
	Path        string `json:"path"`
	IPAddress   string `json:"ip_address"`
	VisitorHash string `json:"visitor_hash"`
	Country     string `json:"country"`
	Region      string `json:"region"`
	City        string `json:"city"`
	Browser     string `json:"browser"`
	OS          string `json:"os"`
	Device      string `json:"device"`
	Referrer    string `json:"referrer"`
	Screen      string `json:"screen"`
}

// QueryRecentVisitors returns the last N page views.
func QueryRecentVisitors(limit int) ([]RecentVisit, error) {
	if limit <= 0 || limit > 200 {
		limit = 50
	}
	rows, err := db.Query(`
		SELECT timestamp, path, ip_address, visitor_hash, country, region, city, browser, os, device, referrer, screen
		FROM page_views
		ORDER BY id DESC
		LIMIT ?`, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var results []RecentVisit
	for rows.Next() {
		var rv RecentVisit
		rows.Scan(&rv.Timestamp, &rv.Path, &rv.IPAddress, &rv.VisitorHash, &rv.Country,
			&rv.Region, &rv.City, &rv.Browser, &rv.OS, &rv.Device, &rv.Referrer, &rv.Screen)
		results = append(results, rv)
	}
	return results, nil
}

// RebuildAggregates rebuilds the daily_aggregates table.
func RebuildAggregates() {
	_, err := db.Exec(`
		INSERT OR REPLACE INTO daily_aggregates (date, path, views, unique_visitors)
		SELECT date(timestamp), path, COUNT(*), COUNT(DISTINCT visitor_hash)
		FROM page_views
		WHERE date(timestamp) >= date('now', '-90 days')
		GROUP BY date(timestamp), path
	`)
	if err != nil {
		log.Printf("rebuild aggregates: %v", err)
	}
}

// PurgeOldData removes raw data older than 90 days.
func PurgeOldData() {
	cutoff := time.Now().UTC().AddDate(0, 0, -90).Format("2006-01-02T15:04:05Z")
	db.Exec(`DELETE FROM page_views WHERE timestamp < ?`, cutoff)
	db.Exec(`DELETE FROM events WHERE timestamp < ?`, cutoff)
	db.Exec(`DELETE FROM daily_salt WHERE date < date('now', '-90 days')`)
	log.Println("purged data older than 90 days")
}

// StartAggregationLoop runs aggregation every 5 minutes and purge daily.
func StartAggregationLoop() {
	go func() {
		aggTicker := time.NewTicker(5 * time.Minute)
		purgeTicker := time.NewTicker(24 * time.Hour)
		defer aggTicker.Stop()
		defer purgeTicker.Stop()

		// Run once on startup
		RebuildAggregates()

		for {
			select {
			case <-aggTicker.C:
				RebuildAggregates()
			case <-purgeTicker.C:
				PurgeOldData()
			}
		}
	}()
}
