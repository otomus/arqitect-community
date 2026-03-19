// Package main implements the git_push MCP tool.
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
	Token  string `json:"token"`
	Remote string `json:"remote,omitempty"`
	Branch string `json:"branch,omitempty"`
	Path   string `json:"path,omitempty"`
}

// injectToken injects a token into an HTTPS git URL for authentication.
func injectToken(url, token string) string {
	if strings.HasPrefix(url, "https://") {
		return strings.Replace(url, "https://", "https://"+token+"@", 1)
	}
	return url
}

// getRemoteURL retrieves the URL for a given remote in the repository.
func getRemoteURL(path, remote string) (string, error) {
	cmd := exec.Command("git", "-C", path, "remote", "get-url", remote)
	out, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("failed to get remote URL: %v", err)
	}
	return strings.TrimSpace(string(out)), nil
}

// setRemoteURL sets the URL for a given remote in the repository.
func setRemoteURL(path, remote, url string) error {
	cmd := exec.Command("git", "-C", path, "remote", "set-url", remote, url)
	if out, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to set remote URL: %s", strings.TrimSpace(string(out)))
	}
	return nil
}

// getCurrentBranch returns the current branch name of the repository.
func getCurrentBranch(path string) (string, error) {
	cmd := exec.Command("git", "-C", path, "rev-parse", "--abbrev-ref", "HEAD")
	out, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("failed to get current branch: %v", err)
	}
	return strings.TrimSpace(string(out)), nil
}

// Run pushes commits to a remote repository.
func Run(params Params) (string, error) {
	if params.Token == "" {
		return "", fmt.Errorf("Git token is required for authentication")
	}

	path := params.Path
	if path == "" {
		path = "."
	}

	remote := params.Remote
	if remote == "" {
		remote = "origin"
	}

	// Verify the path is a valid git repository
	checkCmd := exec.Command("git", "-C", path, "rev-parse", "--git-dir")
	if out, err := checkCmd.CombinedOutput(); err != nil {
		return "", fmt.Errorf("'%s' is not a valid Git repository: %s", path, strings.TrimSpace(string(out)))
	}

	originalURL, err := getRemoteURL(path, remote)
	if err != nil {
		return "", err
	}

	authenticatedURL := injectToken(originalURL, params.Token)

	if err := setRemoteURL(path, remote, authenticatedURL); err != nil {
		return "", err
	}
	// Restore original URL when done to avoid leaking tokens in config
	defer setRemoteURL(path, remote, originalURL)

	targetBranch := params.Branch
	if targetBranch == "" {
		targetBranch, err = getCurrentBranch(path)
		if err != nil {
			return "", err
		}
	}

	cmd := exec.Command("git", "-C", path, "push", remote, targetBranch)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("Failed to push: %s", strings.TrimSpace(string(out)))
	}

	return fmt.Sprintf("Pushed '%s' to '%s' successfully", targetBranch, remote), nil
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
