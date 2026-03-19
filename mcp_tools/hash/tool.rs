//! Hash MCP tool - compute or verify cryptographic hashes.
//!
//! Required crates: serde, serde_json, sha2, md-5, hmac, sha1

use std::env;
use std::process;

use serde::Deserialize;

/// Supported hash algorithm names.
const SUPPORTED_ALGORITHMS: &[&str] = &["md5", "sha1", "sha256", "sha512"];

/// Tool parameters.
#[derive(Deserialize)]
struct Params {
    /// String to hash.
    input: String,
    /// Hash algorithm: md5, sha1, sha256, or sha512.
    algorithm: String,
    /// Operation to perform: compute or verify.
    operation: String,
    /// Expected hash for verification (required for verify).
    #[serde(default)]
    hash: String,
}

/// Compute the hex digest of the input using the specified algorithm.
fn compute(input: &str, algorithm: &str) -> Result<String, Box<dyn std::error::Error>> {
    use sha2::{Sha256, Sha512, Digest};

    let algo = algorithm.to_lowercase();
    if !SUPPORTED_ALGORITHMS.contains(&algo.as_str()) {
        return Err(format!(
            "Unsupported algorithm: {}. Use one of: {}",
            algorithm,
            SUPPORTED_ALGORITHMS.join(", ")
        ).into());
    }

    let digest = match algo.as_str() {
        "md5" => {
            use md5::Md5;
            let mut hasher = Md5::new();
            hasher.update(input.as_bytes());
            format!("{:x}", hasher.finalize())
        }
        "sha1" => {
            use sha1::Sha1;
            let mut hasher = Sha1::new();
            hasher.update(input.as_bytes());
            format!("{:x}", hasher.finalize())
        }
        "sha256" => {
            let mut hasher = Sha256::new();
            hasher.update(input.as_bytes());
            format!("{:x}", hasher.finalize())
        }
        "sha512" => {
            let mut hasher = Sha512::new();
            hasher.update(input.as_bytes());
            format!("{:x}", hasher.finalize())
        }
        _ => unreachable!(),
    };

    Ok(digest)
}

/// Verify that the hash of input matches the expected hash using constant-time comparison.
fn verify(input: &str, algorithm: &str, expected_hash: &str) -> Result<String, Box<dyn std::error::Error>> {
    let computed = compute(input, algorithm)?;
    let expected_lower = expected_hash.to_lowercase();

    // Constant-time comparison: compare all bytes regardless of mismatch position
    let matches = constant_time_eq(computed.as_bytes(), expected_lower.as_bytes());

    let result = serde_json::json!({
        "matches": matches,
        "computed": computed,
        "expected": expected_lower,
    });
    Ok(serde_json::to_string(&result)?)
}

/// Constant-time byte comparison to prevent timing attacks.
fn constant_time_eq(a: &[u8], b: &[u8]) -> bool {
    if a.len() != b.len() {
        return false;
    }
    let mut diff: u8 = 0;
    for (x, y) in a.iter().zip(b.iter()) {
        diff |= x ^ y;
    }
    diff == 0
}

/// Executes the tool logic.
fn run(params: &Params) -> Result<String, Box<dyn std::error::Error>> {
    match params.operation.as_str() {
        "compute" => compute(&params.input, &params.algorithm),
        "verify" => verify(&params.input, &params.algorithm, &params.hash),
        other => Err(format!("Invalid operation '{}'. Must be 'compute' or 'verify'.", other).into()),
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("usage: hash <json-params>");
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
