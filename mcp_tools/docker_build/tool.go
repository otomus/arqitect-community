// Package main implements the docker_build MCP tool.
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
	Path string `json:"path"`
	Tag  string `json:"tag"`
}

// Run executes the docker build command.
func Run(params Params) (string, error) {
	cmd := exec.Command("docker", "build", "-t", params.Tag, params.Path)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("docker build failed: %s", strings.TrimSpace(string(out)))
	}
	return strings.TrimSpace(string(out)), nil
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
