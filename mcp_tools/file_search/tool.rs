//! File Search MCP tool - search for files matching a glob pattern.
//!
//! Required crates: serde, serde_json, glob

use std::env;
use std::path::Path;
use std::process;

use serde::Deserialize;

/// Tool parameters.
#[derive(Deserialize)]
struct Params {
    /// Glob pattern (e.g. "**/*.py").
    pattern: String,
    /// Root directory to search from.
    #[serde(default = "default_path")]
    path: String,
}

/// Default path value.
fn default_path() -> String {
    ".".to_string()
}

/// Executes the tool logic.
fn run(params: &Params) -> Result<String, Box<dyn std::error::Error>> {
    let resolved = std::path::absolute(Path::new(&params.path))
        .unwrap_or_else(|_| Path::new(&params.path).to_path_buf());

    let full_pattern = resolved.join(&params.pattern);
    let pattern_str = full_pattern.to_string_lossy();

    let mut matches: Vec<String> = glob::glob(&pattern_str)?
        .filter_map(|entry| entry.ok())
        .map(|p| p.to_string_lossy().to_string())
        .collect();

    matches.sort();

    let result = serde_json::json!({
        "pattern": params.pattern,
        "root": resolved.to_string_lossy(),
        "count": matches.len(),
        "matches": matches,
    });

    Ok(serde_json::to_string_pretty(&result)?)
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("usage: file_search <json-params>");
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
