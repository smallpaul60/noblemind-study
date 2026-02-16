package main

import (
	"context"
	"flag"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

func main() {
	var (
		addr    = flag.String("addr", ":3001", "listen address")
		dbPath  = flag.String("db", "analytics.db", "SQLite database path")
		geoPath = flag.String("geoip", "", "path to IP2Location LITE DB1 CSV file")
		token   = flag.String("token", "", "auth token for dashboard (or set CONSOLE_TOKEN env)")
	)
	flag.Parse()

	// Auth token from flag or environment
	authToken = *token
	if authToken == "" {
		authToken = os.Getenv("CONSOLE_TOKEN")
	}

	// Initialize database
	if err := initDB(*dbPath); err != nil {
		log.Fatalf("database init failed: %v", err)
	}
	defer db.Close()
	log.Println("database initialized")

	// Load GeoIP database (optional)
	LoadGeoIP(*geoPath)

	// Start background aggregation
	StartAggregationLoop()

	// Setup routes
	mux := http.NewServeMux()
	SetupRoutes(mux)

	server := &http.Server{
		Addr:         *addr,
		Handler:      mux,
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Graceful shutdown
	done := make(chan os.Signal, 1)
	signal.Notify(done, os.Interrupt, syscall.SIGTERM)

	go func() {
		log.Printf("noblemind-console listening on %s", *addr)
		if authToken != "" {
			log.Println("auth token configured — dashboard requires ?token=... parameter")
		} else {
			log.Println("WARNING: no auth token set — dashboard is publicly accessible")
		}
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("server error: %v", err)
		}
	}()

	<-done
	log.Println("shutting down...")

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := server.Shutdown(ctx); err != nil {
		log.Fatalf("shutdown error: %v", err)
	}
	log.Println("stopped")
}
