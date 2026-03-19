// Package main implements the cert_check MCP tool.
package main

import (
	"crypto/tls"
	"encoding/json"
	"fmt"
	"net"
	"os"
	"time"
)

// Params holds the tool parameters.
type Params struct {
	Domain string `json:"domain"`
}

// certResult holds the certificate check output.
type certResult struct {
	Domain        string            `json:"domain"`
	Issuer        map[string]string `json:"issuer"`
	Subject       map[string]string `json:"subject"`
	NotBefore     string            `json:"not_before"`
	NotAfter      string            `json:"not_after"`
	DaysRemaining int               `json:"days_remaining"`
	SAN           []string          `json:"san"`
}

// Run checks SSL certificate details for a domain.
func Run(params Params) (string, error) {
	conn, err := net.DialTimeout("tcp", params.Domain+":443", 10*time.Second)
	if err != nil {
		return "", fmt.Errorf("failed to connect to %s:443: %v", params.Domain, err)
	}

	tlsConn := tls.Client(conn, &tls.Config{ServerName: params.Domain})
	defer tlsConn.Close()

	if err := tlsConn.Handshake(); err != nil {
		return "", fmt.Errorf("TLS handshake failed: %v", err)
	}

	certs := tlsConn.ConnectionState().PeerCertificates
	if len(certs) == 0 {
		return "", fmt.Errorf("no certificates returned by %s", params.Domain)
	}

	cert := certs[0]
	daysRemaining := int(time.Until(cert.NotAfter).Hours() / 24)

	issuer := map[string]string{}
	if len(cert.Issuer.Organization) > 0 {
		issuer["organizationName"] = cert.Issuer.Organization[0]
	}
	if len(cert.Issuer.CommonName) > 0 {
		issuer["commonName"] = cert.Issuer.CommonName
	}
	if len(cert.Issuer.Country) > 0 {
		issuer["countryName"] = cert.Issuer.Country[0]
	}

	subject := map[string]string{}
	if len(cert.Subject.Organization) > 0 {
		subject["organizationName"] = cert.Subject.Organization[0]
	}
	if len(cert.Subject.CommonName) > 0 {
		subject["commonName"] = cert.Subject.CommonName
	}

	san := make([]string, len(cert.DNSNames))
	copy(san, cert.DNSNames)

	result := certResult{
		Domain:        params.Domain,
		Issuer:        issuer,
		Subject:       subject,
		NotBefore:     cert.NotBefore.UTC().Format("2006-01-02T15:04:05"),
		NotAfter:      cert.NotAfter.UTC().Format("2006-01-02T15:04:05"),
		DaysRemaining: daysRemaining,
		SAN:           san,
	}

	jsonBytes, err := json.MarshalIndent(result, "", "  ")
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
