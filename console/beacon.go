package main

import (
	"encoding/json"
	"strings"
)

// BeaconPayload represents the JSON body from the client beacon.
type BeaconPayload struct {
	Type     string `json:"type"`     // "pageview" or event type (pwa_install, pwa_prompt, file_download)
	Path     string `json:"path"`     // page path
	Referrer string `json:"referrer"` // document.referrer
	Screen   string `json:"screen"`   // e.g. "1920x1080"
	Metadata string `json:"metadata"` // extra info for events (e.g. filename)
}

// ParseBeacon parses and validates a beacon JSON payload.
func ParseBeacon(body []byte) (*BeaconPayload, error) {
	var bp BeaconPayload
	if err := json.Unmarshal(body, &bp); err != nil {
		return nil, err
	}

	// Sanitize path — keep only the path component, max 500 chars
	bp.Path = sanitizePath(bp.Path)

	// Reduce referrer to domain only
	bp.Referrer = ReduceReferrer(bp.Referrer)

	// Validate type
	bp.Type = strings.TrimSpace(bp.Type)
	if bp.Type == "" {
		bp.Type = "pageview"
	}

	// Validate screen format (should be like "1920x1080")
	bp.Screen = sanitizeScreen(bp.Screen)

	// Limit metadata length
	if len(bp.Metadata) > 500 {
		bp.Metadata = bp.Metadata[:500]
	}

	return &bp, nil
}

func sanitizePath(p string) string {
	p = strings.TrimSpace(p)
	if p == "" {
		p = "/"
	}
	// Strip query params and fragments
	if idx := strings.IndexByte(p, '?'); idx >= 0 {
		p = p[:idx]
	}
	if idx := strings.IndexByte(p, '#'); idx >= 0 {
		p = p[:idx]
	}
	// Ensure it starts with /
	if !strings.HasPrefix(p, "/") {
		p = "/" + p
	}
	if len(p) > 500 {
		p = p[:500]
	}
	return p
}

func sanitizeScreen(s string) string {
	s = strings.TrimSpace(s)
	if len(s) > 20 {
		s = s[:20]
	}
	// Basic validation: should contain digits and 'x'
	if s != "" && !strings.ContainsRune(s, 'x') {
		return ""
	}
	return s
}
