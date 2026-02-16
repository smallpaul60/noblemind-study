package main

import (
	"embed"
	"encoding/json"
	"io"
	"log"
	"net/http"
	"strconv"
	"strings"
)

//go:embed dashboard.html
var dashboardFS embed.FS

// authToken is set from the environment or config.
var authToken string

// SetupRoutes configures all HTTP routes.
func SetupRoutes(mux *http.ServeMux) {
	mux.HandleFunc("POST /api/analytics/event", handleBeacon)
	mux.HandleFunc("/api/analytics/event", handleBeaconCORS) // OPTIONS preflight
	mux.HandleFunc("GET /api/analytics/stats", requireAuth(handleStats))
	mux.HandleFunc("GET /api/analytics/realtime", requireAuth(handleRealtime))
	mux.HandleFunc("GET /console", requireAuth(handleDashboard))
	mux.HandleFunc("GET /console/", requireAuth(handleDashboard))
}

// handleBeaconCORS handles OPTIONS preflight for the beacon endpoint.
func handleBeaconCORS(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
	w.WriteHeader(http.StatusNoContent)
}

// handleBeacon receives analytics beacons from visitors.
func handleBeacon(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "*")

	// Limit body size to 4KB
	body, err := io.ReadAll(io.LimitReader(r.Body, 4096))
	if err != nil {
		http.Error(w, "bad request", http.StatusBadRequest)
		return
	}
	defer r.Body.Close()

	beacon, err := ParseBeacon(body)
	if err != nil {
		http.Error(w, "invalid json", http.StatusBadRequest)
		return
	}

	// Extract and hash IP — raw IP is never stored
	rawIP := ExtractIP(r.Header.Get("X-Forwarded-For"), r.RemoteAddr)
	visitorHash := HashIP(rawIP)

	// GeoIP lookup
	country := LookupCountry(rawIP)

	// Parse User-Agent — raw UA is never stored
	browser, osName, device := ParseUserAgent(r.Header.Get("User-Agent"))

	if beacon.Type == "pageview" {
		err = InsertPageView(
			beacon.Path,
			beacon.Referrer,
			visitorHash,
			country,
			device,
			browser,
			osName,
			beacon.Screen,
		)
	} else {
		err = InsertEvent(beacon.Type, visitorHash, beacon.Metadata)
	}

	if err != nil {
		log.Printf("beacon insert error: %v", err)
		http.Error(w, "internal error", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"ok":true}`))
}

// handleStats returns dashboard statistics.
func handleStats(w http.ResponseWriter, r *http.Request) {
	periodStr := r.URL.Query().Get("period")
	days := parsePeriod(periodStr)

	stats, err := QueryStats(days)
	if err != nil {
		log.Printf("stats query error: %v", err)
		http.Error(w, "internal error", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(stats)
}

// handleRealtime returns last 30-minute activity.
func handleRealtime(w http.ResponseWriter, r *http.Request) {
	data, err := QueryRealtime()
	if err != nil {
		log.Printf("realtime query error: %v", err)
		http.Error(w, "internal error", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(data)
}

// handleDashboard serves the embedded dashboard HTML.
func handleDashboard(w http.ResponseWriter, r *http.Request) {
	data, err := dashboardFS.ReadFile("dashboard.html")
	if err != nil {
		http.Error(w, "dashboard not found", http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	w.Header().Set("Cache-Control", "no-cache")
	w.Write(data)
}

// requireAuth wraps a handler with token authentication.
func requireAuth(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if authToken == "" {
			// No token configured — allow access (dev mode)
			next(w, r)
			return
		}

		token := r.URL.Query().Get("token")
		if token == "" {
			token = extractBearerToken(r.Header.Get("Authorization"))
		}

		if token != authToken {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}

		next(w, r)
	}
}

func extractBearerToken(auth string) string {
	if strings.HasPrefix(auth, "Bearer ") {
		return strings.TrimPrefix(auth, "Bearer ")
	}
	return ""
}

func parsePeriod(s string) int {
	s = strings.TrimSpace(strings.ToLower(s))
	if s == "" {
		return 7
	}
	s = strings.TrimSuffix(s, "d")
	n, err := strconv.Atoi(s)
	if err != nil || n < 1 {
		return 7
	}
	if n > 365 {
		return 365
	}
	return n
}
