package main

import (
	"bufio"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"log"
	"net"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"
)

// SaltManager handles daily salt rotation for IP hashing.
type SaltManager struct {
	mu   sync.RWMutex
	salt string
	date string
}

var saltMgr = &SaltManager{}

// GetSalt returns today's salt, generating a new one if the day changed.
func (sm *SaltManager) GetSalt() string {
	today := time.Now().UTC().Format("2006-01-02")

	sm.mu.RLock()
	if sm.date == today && sm.salt != "" {
		defer sm.mu.RUnlock()
		return sm.salt
	}
	sm.mu.RUnlock()

	sm.mu.Lock()
	defer sm.mu.Unlock()

	// Double-check after acquiring write lock
	if sm.date == today && sm.salt != "" {
		return sm.salt
	}

	// Try to load from DB
	var salt string
	err := db.QueryRow(`SELECT salt FROM daily_salt WHERE date = ?`, today).Scan(&salt)
	if err == nil {
		sm.salt = salt
		sm.date = today
		return sm.salt
	}

	// Generate new salt
	b := make([]byte, 32)
	if _, err := rand.Read(b); err != nil {
		log.Fatalf("failed to generate salt: %v", err)
	}
	salt = hex.EncodeToString(b)

	db.Exec(`INSERT OR REPLACE INTO daily_salt (date, salt) VALUES (?, ?)`, today, salt)
	sm.salt = salt
	sm.date = today
	return sm.salt
}

// HashIP takes an IP string, combines it with today's salt, and returns
// a truncated SHA-256 hash. The raw IP is never stored.
func HashIP(ip string) string {
	salt := saltMgr.GetSalt()
	h := sha256.Sum256([]byte(ip + "|" + salt))
	return hex.EncodeToString(h[:])[:16]
}

// ExtractIP gets the client IP from X-Forwarded-For or RemoteAddr.
func ExtractIP(xForwardedFor, remoteAddr string) string {
	if xForwardedFor != "" {
		parts := strings.Split(xForwardedFor, ",")
		ip := strings.TrimSpace(parts[0])
		if ip != "" {
			return ip
		}
	}
	host, _, err := net.SplitHostPort(remoteAddr)
	if err != nil {
		return remoteAddr
	}
	return host
}

// ParseUserAgent extracts browser, OS, and device type from a User-Agent string.
func ParseUserAgent(ua string) (browser, osName, device string) {
	lower := strings.ToLower(ua)

	// Device type
	switch {
	case strings.Contains(lower, "mobile") || (strings.Contains(lower, "android") && !strings.Contains(lower, "tablet")):
		device = "Mobile"
	case strings.Contains(lower, "tablet") || strings.Contains(lower, "ipad"):
		device = "Tablet"
	default:
		device = "Desktop"
	}

	// Browser detection
	switch {
	case strings.Contains(lower, "edg/") || strings.Contains(lower, "edga/") || strings.Contains(lower, "edgios/"):
		browser = "Edge"
	case strings.Contains(lower, "opr/") || strings.Contains(lower, "opera"):
		browser = "Opera"
	case strings.Contains(lower, "brave"):
		browser = "Brave"
	case strings.Contains(lower, "vivaldi"):
		browser = "Vivaldi"
	case strings.Contains(lower, "chrome") || strings.Contains(lower, "crios"):
		browser = "Chrome"
	case strings.Contains(lower, "firefox") || strings.Contains(lower, "fxios"):
		browser = "Firefox"
	case strings.Contains(lower, "safari") && !strings.Contains(lower, "chrome"):
		browser = "Safari"
	case strings.Contains(lower, "msie") || strings.Contains(lower, "trident"):
		browser = "IE"
	default:
		browser = "Other"
	}

	// OS detection
	switch {
	case strings.Contains(lower, "windows"):
		osName = "Windows"
	case strings.Contains(lower, "mac os") || strings.Contains(lower, "macintosh"):
		osName = "macOS"
	case strings.Contains(lower, "linux") && !strings.Contains(lower, "android"):
		osName = "Linux"
	case strings.Contains(lower, "android"):
		osName = "Android"
	case strings.Contains(lower, "iphone") || strings.Contains(lower, "ipad") || strings.Contains(lower, "ipod"):
		osName = "iOS"
	case strings.Contains(lower, "cros"):
		osName = "ChromeOS"
	default:
		osName = "Other"
	}

	return
}

// ReduceReferrer strips a referrer URL down to just the domain.
func ReduceReferrer(ref string) string {
	if ref == "" {
		return ""
	}
	ref = strings.TrimPrefix(ref, "https://")
	ref = strings.TrimPrefix(ref, "http://")
	if idx := strings.IndexByte(ref, '/'); idx >= 0 {
		ref = ref[:idx]
	}
	if idx := strings.IndexByte(ref, '?'); idx >= 0 {
		ref = ref[:idx]
	}
	return ref
}

// GeoIPDB holds IP geolocation data in memory.
type GeoIPDB struct {
	mu      sync.RWMutex
	records []geoRecord
	loaded  bool
}

type geoRecord struct {
	ipFrom  uint32
	ipTo    uint32
	country string
	region  string
	city    string
}

// GeoLocation holds the result of a GeoIP lookup.
type GeoLocation struct {
	Country string
	Region  string
	City    string
}

var geoIP = &GeoIPDB{}

// LookupLocation returns the country, region, and city for an IPv4 address.
func LookupLocation(ip string) GeoLocation {
	geoIP.mu.RLock()
	defer geoIP.mu.RUnlock()

	if !geoIP.loaded || len(geoIP.records) == 0 {
		return GeoLocation{}
	}

	parsed := net.ParseIP(ip)
	if parsed == nil {
		return GeoLocation{}
	}
	ipv4 := parsed.To4()
	if ipv4 == nil {
		return GeoLocation{}
	}

	ipNum := uint32(ipv4[0])<<24 | uint32(ipv4[1])<<16 | uint32(ipv4[2])<<8 | uint32(ipv4[3])

	lo, hi := 0, len(geoIP.records)-1
	for lo <= hi {
		mid := (lo + hi) / 2
		rec := geoIP.records[mid]
		if ipNum < rec.ipFrom {
			hi = mid - 1
		} else if ipNum > rec.ipTo {
			lo = mid + 1
		} else {
			return GeoLocation{Country: rec.country, Region: rec.region, City: rec.city}
		}
	}
	return GeoLocation{}
}

// LoadGeoIP loads a GeoIP CSV file. Supports multiple formats:
//   - City CSV: "1.0.0.0,1.0.0.255,AU,Queensland,,South Brisbane,..." (dbip-city)
//   - Country CSV: "1.0.0.0,1.0.0.255,AU" (dbip-country)
//   - Numeric ranges: "16777216","16777471","AU","Australia" (IP2Location)
func LoadGeoIP(path string) {
	if path == "" {
		log.Println("geoip: no database path configured, country lookup disabled")
		return
	}

	f, err := os.Open(path)
	if err != nil {
		log.Printf("geoip: could not load %s: %v (country lookup disabled)", path, err)
		return
	}
	defer f.Close()

	var records []geoRecord
	scanner := bufio.NewScanner(f)
	scanner.Buffer(make([]byte, 1024*1024), 1024*1024)

	for scanner.Scan() {
		line := scanner.Text()

		var fields []string
		var from, to uint32
		var country, region, city string

		// Detect TSV (tab-separated hex format from GitLab/tdulcet)
		if strings.Contains(line, "\t") {
			fields = strings.Split(line, "\t")
			if len(fields) < 5 {
				continue
			}
			// Hex IP ranges: "1000000\t10000ff\tAU\tQueensland\tSouth Brisbane\t..."
			f64, err1 := strconv.ParseUint(fields[0], 16, 32)
			t64, err2 := strconv.ParseUint(fields[1], 16, 32)
			if err1 != nil || err2 != nil {
				continue
			}
			from = uint32(f64)
			to = uint32(t64)
			country = fields[2]
			region = fields[3]
			city = fields[4]
		} else {
			// CSV format
			fields = parseCSVLine(line)
			if len(fields) < 3 {
				continue
			}

			if strings.Contains(fields[0], ".") {
				// IP string format: "1.0.0.0,1.0.0.255,AU,Queensland,,South Brisbane,..."
				fromIP := net.ParseIP(fields[0])
				toIP := net.ParseIP(fields[1])
				if fromIP == nil || toIP == nil {
					continue
				}
				f4 := fromIP.To4()
				t4 := toIP.To4()
				if f4 == nil || t4 == nil {
					continue
				}
				from = uint32(f4[0])<<24 | uint32(f4[1])<<16 | uint32(f4[2])<<8 | uint32(f4[3])
				to = uint32(t4[0])<<24 | uint32(t4[1])<<16 | uint32(t4[2])<<8 | uint32(t4[3])
				country = fields[2]
				if len(fields) >= 6 {
					region = fields[3]
					city = fields[5]
				}
			} else {
				// Numeric decimal format: "16777216","16777471","AU","Australia"
				from = parseUint32(fields[0])
				to = parseUint32(fields[1])
				country = fields[2]
			}
		}

		if from == 0 && to == 0 {
			continue
		}
		records = append(records, geoRecord{ipFrom: from, ipTo: to, country: country, region: region, city: city})
	}

	geoIP.mu.Lock()
	geoIP.records = records
	geoIP.loaded = true
	geoIP.mu.Unlock()

	log.Printf("geoip: loaded %d records from %s", len(records), path)
}

// parseCSVLine handles the quoted CSV format from IP2Location.
func parseCSVLine(line string) []string {
	var fields []string
	var field strings.Builder
	inQuote := false
	for i := 0; i < len(line); i++ {
		c := line[i]
		switch {
		case c == '"':
			inQuote = !inQuote
		case c == ',' && !inQuote:
			fields = append(fields, field.String())
			field.Reset()
		default:
			field.WriteByte(c)
		}
	}
	fields = append(fields, field.String())
	return fields
}

func parseUint32(s string) uint32 {
	s = strings.TrimSpace(s)
	var n uint64
	for _, c := range s {
		if c >= '0' && c <= '9' {
			n = n*10 + uint64(c-'0')
		}
	}
	return uint32(n)
}
