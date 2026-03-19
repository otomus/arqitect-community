// Package main implements the docker_logs MCP tool.
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
	ContainerID string `json:"container_id"`
	Tail        *int   `json:"tail,omitempty"`
}

// Run retrieves logs from a Docker container.
func Run(params Params) (string, error) {
	args := []string{"logs"}

	if params.Tail != nil {
		args = append(args, "--tail", strconv.Itoa(*params.Tail))
	}

	args = append(args, params.ContainerID)

	cmd := exec.Command("docker", args...)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("docker logs failed: %s", strings.TrimSpace(string(out)))
	}
	// Docker may write to both stdout and stderr; CombinedOutput captures both
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
