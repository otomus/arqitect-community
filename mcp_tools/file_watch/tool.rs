//! File Watch MCP tool - snapshot the current state of a file or directory.
//!
//! Required crates: serde, serde_json, chrono

use std::collections::BTreeMap;
use std::env;
use std::fs;
use std::path::Path;
use std::process;

use serde::Deserialize;

/// Tool parameters.
#[derive(Deserialize)]
struct Params {
    /// File or directory to watch.
    path: String,
}

/// Format a system time as an ISO 8601 UTC timestamp.
fn format_mtime(metadata: &fs::Metadata) -> String {
    use std::time::UNIX_EPOCH;
    let mtime = metadata.modified().unwrap_or(UNIX_EPOCH);
    let duration = mtime.duration_since(UNIX_EPOCH).unwrap_or_default();
    let secs = duration.as_secs() as i64;

    let dt = chrono::DateTime::from_timestamp(secs, 0)
        .unwrap_or_else(|| chrono::DateTime::from_timestamp(0, 0).unwrap());
    dt.to_rfc3339_opts(chrono::SecondsFormat::AutoSi, true)
}

/// Executes the tool logic.
fn run(params: &Params) -> Result<String, Box<dyn std::error::Error>> {
    let resolved = fs::canonicalize(&params.path)
        .map_err(|_| format!("Path not found: {}", std::path::absolute(Path::new(&params.path))
            .unwrap_or_else(|_| Path::new(&params.path).to_path_buf())
            .display()))?;

    if !resolved.exists() {
        return Err(format!("Path not found: {}", resolved.display()).into());
    }

    if resolved.is_file() {
        let meta = fs::metadata(&resolved)?;
        let result = serde_json::json!({
            "path": resolved.to_string_lossy(),
            "type": "file",
            "size": meta.len(),
            "modified": format_mtime(&meta),
        });
        return Ok(serde_json::to_string_pretty(&result)?);
    }

    // Directory: list entries sorted by name
    let mut entries = BTreeMap::new();
    let mut dir_entries: Vec<_> = fs::read_dir(&resolved)?
        .filter_map(|e| e.ok())
        .collect();
    dir_entries.sort_by_key(|e| e.file_name());

    for entry in dir_entries {
        let name = entry.file_name().to_string_lossy().to_string();
        let meta = entry.metadata()?;
        let entry_type = if meta.is_dir() { "directory" } else { "file" };
        entries.insert(name, serde_json::json!({
            "type": entry_type,
            "size": meta.len(),
            "modified": format_mtime(&meta),
        }));
    }

    let result = serde_json::json!({
        "path": resolved.to_string_lossy(),
        "type": "directory",
        "entries": entries,
    });
    Ok(serde_json::to_string_pretty(&result)?)
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("usage: file_watch <json-params>");
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
