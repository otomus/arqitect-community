// Package main implements the git_clone MCP tool.
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
	Token       string `json:"token"`
	URL         string `json:"url"`
	Destination string `json:"destination,omitempty"`
}

// injectToken injects a token into an HTTPS git URL for authentication.
func injectToken(url, token string) string {
	if strings.HasPrefix(url, "https://") {
		return strings.Replace(url, "https://", "https://"+token+"@", 1)
	}
	return url
}

// deriveRepoName extracts the repository name from a URL.
func deriveRepoName(url string) string {
	trimmed := strings.TrimRight(url, "/")
	parts := strings.Split(trimmed, "/")
	name := parts[len(parts)-1]
	if strings.HasSuffix(name, ".git") {
		name = name[:len(name)-4]
	}
	return name
}

// Run clones a remote Git repository.
func Run(params Params) (string, error) {
	if params.Token == "" {
		return "", fmt.Errorf("Git token is required for authentication")
	}
	if strings.TrimSpace(params.URL) == "" {
		return "", fmt.Errorf("Repository URL is required")
	}

	authenticatedURL := injectToken(params.URL, params.Token)

	destination := params.Destination
	if destination == "" {
		destination = deriveRepoName(params.URL)
	}

	cmd := exec.Command("git", "clone", authenticatedURL, destination)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("Failed to clone repository: %s", strings.TrimSpace(string(out)))
	}

	return fmt.Sprintf("Cloned '%s' into '%s'", params.URL, destination), nil
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
