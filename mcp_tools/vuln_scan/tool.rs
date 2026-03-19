//! Vuln Scan MCP tool - scan files for common security vulnerabilities.
//!
//! Required crates: serde, serde_json, regex, walkdir

use std::env;
use std::fs;
use std::io::{BufRead, BufReader};
use std::path::Path;
use std::process;

use serde::Deserialize;

/// Maximum file size to scan (1 MB).
const MAX_FILE_SIZE: u64 = 1_000_000;

/// A secret pattern definition: (regex, human-readable name).
struct SecretPattern {
    pattern: &'static str,
    name: &'static str,
}

/// Known secret patterns to scan for.
const SECRET_PATTERNS: &[SecretPattern] = &[
    SecretPattern { pattern: r"(?i)(api[_\-]?key|apikey)\s*[:=]\s*['\"`]([^'\"\s`]{8,})", name: "API Key" },
    SecretPattern { pattern: r"(?i)(secret|password|passwd|pwd)\s*[:=]\s*['\"`]([^'\"\s`]{6,})", name: "Password/Secret" },
    SecretPattern { pattern: r"(?i)(aws_access_key_id)\s*[:=]\s*['\"`]?(AKIA[A-Z0-9]{16})", name: "AWS Access Key" },
    SecretPattern { pattern: r"(?i)(private[_\-]?key)\s*[:=]", name: "Private Key Reference" },
    SecretPattern { pattern: r"-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----", name: "Private Key File" },
    SecretPattern { pattern: r"ghp_[A-Za-z0-9_]{36}", name: "GitHub Personal Access Token" },
    SecretPattern { pattern: r"sk-[A-Za-z0-9]{32,}", name: "OpenAI/Stripe Secret Key" },
];

/// Tool parameters.
#[derive(Deserialize)]
struct Params {
    /// File or directory to scan.
    path: String,
    /// Scan type: secrets, code, dependencies.
    #[serde(rename = "type", default = "default_scan_type")]
    scan_type: String,
}

/// Default scan type value.
fn default_scan_type() -> String {
    "secrets".to_string()
}

/// A single finding from the scan.
#[derive(serde::Serialize)]
struct Finding {
    file: String,
    line: usize,
    #[serde(rename = "type")]
    finding_type: String,
    snippet: String,
}

/// Collect all files to scan from a path (file or directory).
fn collect_files(resolved: &Path) -> Result<Vec<std::path::PathBuf>, Box<dyn std::error::Error>> {
    if resolved.is_file() {
        return Ok(vec![resolved.to_path_buf()]);
    }
    if resolved.is_dir() {
        let mut files = Vec::new();
        for entry in walkdir::WalkDir::new(resolved).into_iter().filter_map(|e| e.ok()) {
            if entry.file_type().is_file() {
                files.push(entry.into_path());
            }
        }
        return Ok(files);
    }
    Err(format!("Path not found: {}", resolved.display()).into())
}

/// Scan a single file for secret patterns.
fn scan_file(
    fpath: &Path,
    compiled_patterns: &[(regex::Regex, &str)],
    findings: &mut Vec<Finding>,
) {
    let metadata = match fs::metadata(fpath) {
        Ok(m) => m,
        Err(_) => return,
    };
    if metadata.len() > MAX_FILE_SIZE {
        return;
    }

    let file = match fs::File::open(fpath) {
        Ok(f) => f,
        Err(_) => return,
    };
    let reader = BufReader::new(file);

    for (line_num, line_result) in reader.lines().enumerate() {
        let line = match line_result {
            Ok(l) => l,
            Err(_) => continue,
        };
        for (re, name) in compiled_patterns {
            if re.is_match(&line) {
                let snippet: String = line.trim().chars().take(100).collect();
                findings.push(Finding {
                    file: fpath.to_string_lossy().to_string(),
                    line: line_num + 1,
                    finding_type: name.to_string(),
                    snippet,
                });
            }
        }
    }
}

/// Executes the tool logic.
fn run(params: &Params) -> Result<String, Box<dyn std::error::Error>> {
    let resolved = fs::canonicalize(&params.path)
        .or_else(|_| {
            let abs = std::path::absolute(Path::new(&params.path))
                .unwrap_or_else(|_| Path::new(&params.path).to_path_buf());
            if abs.exists() { Ok(abs) } else { Err(std::io::Error::new(std::io::ErrorKind::NotFound, format!("Path not found: {}", params.path))) }
        })?;

    let compiled_patterns: Vec<(regex::Regex, &str)> = SECRET_PATTERNS
        .iter()
        .filter_map(|sp| {
            regex::Regex::new(sp.pattern).ok().map(|re| (re, sp.name))
        })
        .collect();

    let files = collect_files(&resolved)?;
    let mut findings = Vec::new();

    for fpath in &files {
        scan_file(fpath, &compiled_patterns, &mut findings);
    }

    let result = serde_json::json!({
        "scan_type": params.scan_type,
        "path": resolved.to_string_lossy(),
        "finding_count": findings.len(),
        "findings": findings,
    });

    Ok(serde_json::to_string_pretty(&result)?)
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("usage: vuln_scan <json-params>");
        process::exit(1);
    }
    let params: Params = serde_json::from_str(&args[1]).unwrap_or_else(|e| {
        eprintln!("invalid params: {}", e);
        process::exit(1);
    });
    match run(&params) {
        Ok(result) => print!("{}", result),
        Err(e) => {
            eprintln!("error: {}", e);
            process::exit(1);
        }
    }
}
