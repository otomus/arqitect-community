// Package main implements the git_status MCP tool.
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
	Token string `json:"token"`
	Path  string `json:"path,omitempty"`
}

// Run gets the working tree status of a Git repository.
func Run(params Params) (string, error) {
	if params.Token == "" {
		return "", fmt.Errorf("Git token is required for authentication")
	}

	path := params.Path
	if path == "" {
		path = "."
	}

	// Verify the path is a valid git repository
	checkCmd := exec.Command("git", "-C", path, "rev-parse", "--git-dir")
	if out, err := checkCmd.CombinedOutput(); err != nil {
		return "", fmt.Errorf("'%s' is not a valid Git repository: %s", path, strings.TrimSpace(string(out)))
	}

	cmd := exec.Command("git", "-C", path, "status", "--porcelain")
	out, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("git status failed: %s", strings.TrimSpace(string(out)))
	}

	output := strings.TrimSpace(string(out))
	if output == "" {
		return "Working tree is clean", nil
	}

	return output, nil
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
