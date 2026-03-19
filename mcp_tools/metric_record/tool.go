// Package main implements the metric_record MCP tool.
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"
)

// Params holds the tool parameters.
type Params struct {
	Name  string `json:"name"`
	Value string `json:"value"`
	Tags  string `json:"tags,omitempty"`
}

// metricEntry represents a single metric data point written to the file.
type metricEntry struct {
	Timestamp string                 `json:"timestamp"`
	Name      string                 `json:"name"`
	Value     string                 `json:"value"`
	Tags      map[string]interface{} `json:"tags"`
}

// Run records a metric data point to a JSON lines file.
func Run(params Params) (string, error) {
	homeDir, err := os.UserHomeDir()
	if err != nil {
		return "", fmt.Errorf("failed to get home directory: %v", err)
	}
	metricsFile := filepath.Join(homeDir, ".arqitect_metrics.jsonl")

	var tags map[string]interface{}
	if params.Tags != "" {
		if err := json.Unmarshal([]byte(params.Tags), &tags); err != nil {
			return "", fmt.Errorf("invalid tags JSON: %v", err)
		}
	} else {
		tags = map[string]interface{}{}
	}

	entry := metricEntry{
		Timestamp: time.Now().UTC().Format(time.RFC3339),
		Name:      params.Name,
		Value:     params.Value,
		Tags:      tags,
	}

	entryJSON, err := json.Marshal(entry)
	if err != nil {
		return "", fmt.Errorf("failed to marshal entry: %v", err)
	}

	f, err := os.OpenFile(metricsFile, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return "", fmt.Errorf("failed to open metrics file: %v", err)
	}
	defer f.Close()

	if _, err := f.WriteString(string(entryJSON) + "\n"); err != nil {
		return "", fmt.Errorf("failed to write metric: %v", err)
	}

	return "ok", nil
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintf(os.Stderr, "usage: tool <json-params>\n")
		os.Exit(1)
	}
	var params Params
	if err := json.Unmarshal([]byte(os.Args[1]), &params); err != nil {
		fmt.Fprintf(os.Stderr, "invalid params: %v\n", err)
		os.Exit(1)
	}
	result, err := Run(params)
	if err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
		os.Exit(1)
	}
	fmt.Print(result)
}
