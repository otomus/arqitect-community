//! File Grep MCP tool - search for a text pattern inside files.
//!
//! Required crates: serde, serde_json, regex, walkdir, glob

use std::env;
use std::fs;
use std::io::{BufRead, BufReader};
use std::path::Path;
use std::process;

use serde::Deserialize;

/// Maximum number of matches to return before truncating.
const MAX_RESULTS: usize = 100;

/// Tool parameters.
#[derive(Deserialize)]
struct Params {
    /// Text or regex pattern to search for.
    pattern: String,
    /// File or directory to search in.
    #[serde(default = "default_path")]
    path: String,
    /// File glob filter (e.g. "*.py").
    #[serde(default = "default_glob")]
    glob: String,
}

/// Default path value.
fn default_path() -> String {
    ".".to_string()
}

/// Default glob value.
fn default_glob() -> String {
    "*".to_string()
}

/// A single grep match.
#[derive(serde::Serialize)]
struct Match {
    file: String,
    line: usize,
    text: String,
}

/// Check if a filename matches a glob pattern using simple fnmatch-style matching.
fn fnmatch(name: &str, pattern: &str) -> bool {
    glob::Pattern::new(pattern)
        .map(|p| p.matches(name))
        .unwrap_or(false)
}

/// Executes the tool logic.
fn run(params: &Params) -> Result<String, Box<dyn std::error::Error>> {
    let resolved = std::path::absolute(Path::new(&params.path))
        .unwrap_or_else(|_| Path::new(&params.path).to_path_buf());

    let compiled = regex::Regex::new(&params.pattern)?;
    let mut results: Vec<Match> = Vec::new();

    let files: Vec<std::path::PathBuf> = if resolved.is_file() {
        vec![resolved.clone()]
    } else {
        let mut collected = Vec::new();
        for entry in walkdir::WalkDir::new(&resolved)
            .into_iter()
            .filter_map(|e| e.ok())
        {
            if entry.file_type().is_file() {
                let fname = entry.file_name().to_string_lossy();
                if fnmatch(&fname, &params.glob) {
                    collected.push(entry.into_path());
                }
            }
        }
        collected
    };

    for fpath in &files {
        let file = match fs::File::open(fpath) {
            Ok(f) => f,
            Err(_) => continue,
        };
        let reader = BufReader::new(file);

        for (line_num, line_result) in reader.lines().enumerate() {
            let line = match line_result {
                Ok(l) => l,
                Err(_) => continue,
            };
            if compiled.is_match(&line) {
                let text = line.trim_end().to_string();
                results.push(Match {
                    file: fpath.to_string_lossy().to_string(),
                    line: line_num + 1,
                    text,
                });
                if results.len() >= MAX_RESULTS {
                    let output = serde_json::json!({
                        "truncated": true,
                        "count": results.len(),
                        "matches": results,
                    });
                    return Ok(serde_json::to_string_pretty(&output)?);
                }
            }
        }
    }

    let output = serde_json::json!({
        "count": results.len(),
        "matches": results,
    });
    Ok(serde_json::to_string_pretty(&output)?)
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("usage: file_grep <json-params>");
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
