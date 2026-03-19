// Package main implements the git_log MCP tool.
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"strconv"
	"strings"
)

// Params holds the tool parameters.
type Params struct {
	Token string `json:"token"`
	Count int    `json:"count,omitempty"`
	Path  string `json:"path,omitempty"`
}

// Run shows commit history of a Git repository.
func Run(params Params) (string, error) {
	if params.Token == "" {
		return "", fmt.Errorf("Git token is required for authentication")
	}

	path := params.Path
	if path == "" {
		path = "."
	}

	count := params.Count
	if count <= 0 {
		count = 10
	}

	// Verify the path is a valid git repository
	checkCmd := exec.Command("git", "-C", path, "rev-parse", "--git-dir")
	if out, err := checkCmd.CombinedOutput(); err != nil {
		return "", fmt.Errorf("'%s' is not a valid Git repository: %s", path, strings.TrimSpace(string(out)))
	}

	// Use git log with a format matching the Python output:
	// <short_hash> <date> <time> <author>: <subject>
	cmd := exec.Command("git", "-C", path, "log",
		"--max-count", strconv.Itoa(count),
		"--format=%h %ai %an: %s",
	)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("Failed to read commit log: %s", strings.TrimSpace(string(out)))
	}

	output := strings.TrimSpace(string(out))
	if output == "" {
		return "No commits found", nil
	}

	// Reformat the date from "2024-01-15 10:30:00 +0200" to "2024-01-15 10:30:00"
	// The git %ai format outputs: "2024-01-15 10:30:00 +0200"
	// The Python version outputs: "2024-01-15 10:30:00"
	lines := strings.Split(output, "\n")
	var formatted []string
	for _, line := range lines {
		if line == "" {
			continue
		}
		// Format: <hash> <date> <time> <tz> <author>: <subject>
		// We need to remove the timezone part
		parts := strings.SplitN(line, " ", 5)
		if len(parts) >= 5 {
			// parts[0]=hash, parts[1]=date, parts[2]=time, parts[3]=tz, parts[4]=author: subject
			formatted = append(formatted, fmt.Sprintf("%s %s %s %s", parts[0], parts[1], parts[2], parts[4]))
		} else {
			formatted = append(formatted, line)
		}
	}

	return strings.Join(formatted, "\n"), nil
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
