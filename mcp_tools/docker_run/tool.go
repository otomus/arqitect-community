// Package main implements the docker_run MCP tool.
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
	Image  string  `json:"image"`
	Name   string  `json:"name,omitempty"`
	Ports  string  `json:"ports,omitempty"`
	Detach *bool   `json:"detach,omitempty"`
}

// Run starts a Docker container from the given image.
func Run(params Params) (string, error) {
	args := []string{"run"}

	// Default to detached mode (matches Python default of True)
	detach := true
	if params.Detach != nil {
		detach = *params.Detach
	}
	if detach {
		args = append(args, "-d")
	}

	if params.Name != "" {
		args = append(args, "--name", params.Name)
	}

	if params.Ports != "" {
		args = append(args, "-p", params.Ports)
	}

	args = append(args, params.Image)

	cmd := exec.Command("docker", args...)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("docker run failed: %s", strings.TrimSpace(string(out)))
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
