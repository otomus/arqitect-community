// Package main implements the process_kill MCP tool.
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"sort"
	"strings"
	"syscall"
)

// supportedSignals maps signal names to their syscall values.
var supportedSignals = map[string]syscall.Signal{
	"TERM": syscall.SIGTERM,
	"KILL": syscall.SIGKILL,
	"HUP":  syscall.SIGHUP,
	"INT":  syscall.SIGINT,
	"USR1": syscall.SIGUSR1,
	"USR2": syscall.SIGUSR2,
}

// Params holds the tool parameters.
type Params struct {
	PID    int    `json:"pid"`
	Signal string `json:"signal,omitempty"`
}

// Run sends a signal to a process identified by PID.
func Run(params Params) (string, error) {
	sigName := params.Signal
	if sigName == "" {
		sigName = "TERM"
	}
	sigName = strings.ToUpper(sigName)

	sig, ok := supportedSignals[sigName]
	if !ok {
		names := make([]string, 0, len(supportedSignals))
		for k := range supportedSignals {
			names = append(names, k)
		}
		sort.Strings(names)
		return "", fmt.Errorf("Unsupported signal '%s'. Supported signals: %s", params.Signal, strings.Join(names, ", "))
	}

	proc, err := os.FindProcess(params.PID)
	if err != nil {
		return "", fmt.Errorf("no process with PID %d: %v", params.PID, err)
	}

	if err := proc.Signal(sig); err != nil {
		return "", fmt.Errorf("failed to signal process %d: %v", params.PID, err)
	}

	return fmt.Sprintf("Signal %s sent to process %d", sigName, params.PID), nil
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
