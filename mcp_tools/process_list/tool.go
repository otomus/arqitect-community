// Package main implements the process_list MCP tool.
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"strings"
)

// Params holds the tool parameters.
type Params struct {
	Filter string `json:"filter,omitempty"`
}

// Run lists running system processes, optionally filtered by name.
func Run(params Params) (string, error) {
	cmd := exec.Command("ps", "aux")
	out, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("ps failed: %s", strings.TrimSpace(string(out)))
	}

	output := string(out)

	if params.Filter != "" {
		lines := strings.Split(strings.TrimRight(output, "\n"), "\n")
		header := ""
		if len(lines) > 0 {
			header = lines[0]
		}
		filterLower := strings.ToLower(params.Filter)
		var filtered []string
		for _, line := range lines[1:] {
			if strings.Contains(strings.ToLower(line), filterLower) {
				filtered = append(filtered, line)
			}
		}
		return header + "\n" + strings.Join(filtered, "\n"), nil
	}

	return strings.TrimSpace(output), nil
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
