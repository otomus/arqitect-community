//! Password MCP tool - generate, get, and store passwords.
//!
//! Generate uses cryptographic randomness.
//! Get/store use a JSON vault file at ~/.arqitect_vault.json.
//!
//! Required crates: serde, serde_json, rand, chrono, dirs

use std::collections::HashMap;
use std::env;
use std::fs;
use std::path::PathBuf;
use std::process;

use serde::{Deserialize, Serialize};

/// Valid operations for the password tool.
const VALID_OPERATIONS: &[&str] = &["generate", "get", "store"];

/// Character sets available for password generation.
const CHARSET_ALPHANUMERIC: &str = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
const CHARSET_ASCII: &str = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~";
const CHARSET_DIGITS: &str = "0123456789";
const CHARSET_HEX: &str = "0123456789abcdef";

/// Tool parameters.
#[derive(Deserialize)]
struct Params {
    /// Operation to perform: generate, get, store.
    operation: String,
    /// Entry name / label (used for get, store).
    #[serde(default)]
    name: Option<String>,
    /// Password value to store (used for store).
    #[serde(default)]
    value: Option<String>,
    /// Vault namespace (used for get, store; default 'default').
    #[serde(default)]
    vault: Option<String>,
    /// Password length (used for generate; default 20).
    #[serde(default)]
    length: Option<String>,
    /// Character set: alphanumeric, ascii, digits, hex (used for generate; default ascii).
    #[serde(default)]
    charset: Option<String>,
}

/// A single vault entry.
#[derive(Serialize, Deserialize, Clone)]
struct VaultEntry {
    value: String,
    stored_at: String,
}

/// The vault is a map of namespace -> (name -> entry).
type VaultData = HashMap<String, HashMap<String, VaultEntry>>;

/// Returns the path to the vault file (~/.arqitect_vault.json).
fn vault_path() -> PathBuf {
    let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
    home.join(".arqitect_vault.json")
}

/// Load the vault data from disk (plaintext JSON only in Rust version).
fn load_vault() -> Result<VaultData, Box<dyn std::error::Error>> {
    let path = vault_path();
    if !path.exists() {
        return Ok(HashMap::new());
    }
    let raw = fs::read_to_string(&path)?;
    if raw.trim().is_empty() {
        return Ok(HashMap::new());
    }
    let data: VaultData = serde_json::from_str(&raw)?;
    Ok(data)
}

/// Persist vault data to disk as JSON.
fn save_vault(data: &VaultData) -> Result<(), Box<dyn std::error::Error>> {
    let payload = serde_json::to_string_pretty(data)?;
    fs::write(vault_path(), payload)?;
    Ok(())
}

/// Look up the character set by name.
fn get_charset(name: &str) -> Result<&'static str, Box<dyn std::error::Error>> {
    match name {
        "alphanumeric" => Ok(CHARSET_ALPHANUMERIC),
        "ascii" => Ok(CHARSET_ASCII),
        "digits" => Ok(CHARSET_DIGITS),
        "hex" => Ok(CHARSET_HEX),
        other => Err(format!(
            "Unknown charset: {}. Use one of: alphanumeric, ascii, digits, hex",
            other
        ).into()),
    }
}

/// Generate a cryptographically secure random password.
fn handle_generate(params: &Params) -> Result<String, Box<dyn std::error::Error>> {
    let length_str = params.length.as_deref().unwrap_or("20");
    let length: usize = length_str.parse()?;
    let charset_name = params.charset.as_deref().unwrap_or("ascii");

    let chars = get_charset(charset_name)?;
    if length < 1 || length > 256 {
        return Err("Length must be between 1 and 256".into());
    }

    let chars_bytes = chars.as_bytes();
    let mut password = String::with_capacity(length);
    let mut buf = vec![0u8; length];
    getrandom::getrandom(&mut buf)?;

    for &b in &buf {
        let idx = (b as usize) % chars_bytes.len();
        password.push(chars_bytes[idx] as char);
    }

    let result = serde_json::json!({
        "status": "generated",
        "password": password,
        "length": length,
        "charset": charset_name,
    });
    Ok(serde_json::to_string_pretty(&result)?)
}

/// Retrieve a password from the vault.
fn handle_get(params: &Params) -> Result<String, Box<dyn std::error::Error>> {
    let name = params.name.as_deref()
        .ok_or("name is required for get operation")?;
    if name.is_empty() {
        return Err("name is required for get operation".into());
    }

    let vault_name = params.vault.as_deref().unwrap_or("default");
    let data = load_vault()?;

    let vault_entries = data.get(vault_name)
        .ok_or_else(|| format!("Entry not found: '{}' in vault '{}'", name, vault_name))?;

    let entry = vault_entries.get(name)
        .ok_or_else(|| format!("Entry not found: '{}' in vault '{}'", name, vault_name))?;

    let result = serde_json::json!({
        "status": "found",
        "name": name,
        "vault": vault_name,
        "value": entry.value,
    });
    Ok(serde_json::to_string_pretty(&result)?)
}

/// Store a password in the vault.
fn handle_store(params: &Params) -> Result<String, Box<dyn std::error::Error>> {
    let name = params.name.as_deref()
        .ok_or("name is required for store operation")?;
    if name.is_empty() {
        return Err("name is required for store operation".into());
    }

    let value = params.value.as_deref()
        .ok_or("value is required for store operation")?;
    if value.is_empty() {
        return Err("value is required for store operation".into());
    }

    let vault_name = params.vault.as_deref().unwrap_or("default");
    let mut data = load_vault()?;

    let vault_entries = data.entry(vault_name.to_string()).or_default();

    let now = chrono::Utc::now().to_rfc3339();
    vault_entries.insert(name.to_string(), VaultEntry {
        value: value.to_string(),
        stored_at: now,
    });

    save_vault(&data)?;

    let result = serde_json::json!({
        "status": "stored",
        "name": name,
        "vault": vault_name,
        "encrypted": false,
    });
    Ok(serde_json::to_string_pretty(&result)?)
}

/// Executes the tool logic.
fn run(params: &Params) -> Result<String, Box<dyn std::error::Error>> {
    match params.operation.as_str() {
        "generate" => handle_generate(params),
        "get" => handle_get(params),
        "store" => handle_store(params),
        other => Err(format!(
            "Invalid operation: '{}'. Must be one of: generate, get, store",
            other
        ).into()),
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("usage: password <json-params>");
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
