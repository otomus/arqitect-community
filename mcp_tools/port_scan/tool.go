// Package main implements the port_scan MCP tool.
package main

import (
	"encoding/json"
	"fmt"
	"net"
	"os"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"
)

// Params holds the tool parameters.
type Params struct {
	Host  string `json:"host"`
	Ports string `json:"ports,omitempty"`
}

// portResult holds the scan result for a single port.
type portResult struct {
	Port   int    `json:"port"`
	Status string `json:"status"`
}

// scanResult holds the complete scan output.
type scanResult struct {
	Host      string       `json:"host"`
	OpenPorts []int        `json:"open_ports"`
	Details   []portResult `json:"details"`
}

// parsePorts parses a port specification string into a sorted unique list of integers.
func parsePorts(portsStr string) ([]int, error) {
	portSet := make(map[int]bool)
	for _, part := range strings.Split(portsStr, ",") {
		part = strings.TrimSpace(part)
		if strings.Contains(part, "-") {
			bounds := strings.SplitN(part, "-", 2)
			start, err := strconv.Atoi(strings.TrimSpace(bounds[0]))
			if err != nil {
				return nil, fmt.Errorf("invalid port: %s", bounds[0])
			}
			end, err := strconv.Atoi(strings.TrimSpace(bounds[1]))
			if err != nil {
				return nil, fmt.Errorf("invalid port: %s", bounds[1])
			}
			for p := start; p <= end; p++ {
				portSet[p] = true
			}
		} else {
			p, err := strconv.Atoi(part)
			if err != nil {
				return nil, fmt.Errorf("invalid port: %s", part)
			}
			portSet[p] = true
		}
	}

	ports := make([]int, 0, len(portSet))
	for p := range portSet {
		ports = append(ports, p)
	}
	sort.Ints(ports)
	return ports, nil
}

// Run scans ports on a host and returns which are open.
func Run(params Params) (string, error) {
	portsStr := params.Ports
	if portsStr == "" {
		portsStr = "22,80,443,8080,8443"
	}

	portList, err := parsePorts(portsStr)
	if err != nil {
		return "", err
	}

	type indexedResult struct {
		index  int
		result portResult
	}

	results := make([]portResult, len(portList))
	var wg sync.WaitGroup
	ch := make(chan indexedResult, len(portList))

	for i, port := range portList {
		wg.Add(1)
		go func(idx, p int) {
			defer wg.Done()
			address := net.JoinHostPort(params.Host, strconv.Itoa(p))
			conn, err := net.DialTimeout("tcp", address, 2*time.Second)
			status := "closed"
			if err == nil {
				status = "open"
				conn.Close()
			}
			ch <- indexedResult{index: idx, result: portResult{Port: p, Status: status}}
		}(i, port)
	}

	wg.Wait()
	close(ch)

	for ir := range ch {
		results[ir.index] = ir.result
	}

	var openPorts []int
	for _, r := range results {
		if r.Status == "open" {
			openPorts = append(openPorts, r.Port)
		}
	}
	if openPorts == nil {
		openPorts = []int{}
	}

	output := scanResult{
		Host:      params.Host,
		OpenPorts: openPorts,
		Details:   results,
	}

	jsonBytes, err := json.MarshalIndent(output, "", "  ")
	if err != nil {
		return "", fmt.Errorf("failed to marshal results: %v", err)
	}
	return string(jsonBytes), nil
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
