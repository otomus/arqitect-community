// Package main implements the docker_exec MCP tool.
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
	ContainerID string `json:"container_id"`
	Command     string `json:"command"`
}

// splitCommand splits a command string into arguments, respecting quotes.
// This mirrors Python's shlex.split behavior for common cases.
func splitCommand(command string) []string {
	var args []string
	var current strings.Builder
	inSingle := false
	inDouble := false
	escaped := false

	for _, r := range command {
		if escaped {
			current.WriteRune(r)
			escaped = false
			continue
		}
		if r == '\\' && !inSingle {
			escaped = true
			continue
		}
		if r == '\'' && !inDouble {
			inSingle = !inSingle
			continue
		}
		if r == '"' && !inSingle {
			inDouble = !inDouble
			continue
		}
		if r == ' ' && !inSingle && !inDouble {
			if current.Len() > 0 {
				args = append(args, current.String())
				current.Reset()
			}
			continue
		}
		current.WriteRune(r)
	}
	if current.Len() > 0 {
		args = append(args, current.String())
	}
	return args
}

// Run executes a command inside a running Docker container.
func Run(params Params) (string, error) {
	cmdArgs := append([]string{"exec", params.ContainerID}, splitCommand(params.Command)...)
	cmd := exec.Command("docker", cmdArgs...)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("docker exec failed: %s", strings.TrimSpace(string(out)))
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
