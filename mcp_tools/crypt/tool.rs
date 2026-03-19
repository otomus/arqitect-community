//! Crypt MCP tool - encrypt or decrypt text using a symmetric key.
//!
//! Uses XOR-based stream cipher with HMAC-SHA256 authentication,
//! matching the Python implementation exactly.
//!
//! Required crates: serde, serde_json, sha2, hmac, base64, rand

use std::env;
use std::process;

use serde::Deserialize;

/// Tool parameters.
#[derive(Deserialize)]
struct Params {
    /// Plaintext to encrypt, or base64 ciphertext to decrypt.
    text: String,
    /// Passphrase used for key derivation.
    key: String,
    /// Operation: 'encrypt' or 'decrypt'.
    operation: String,
}

/// Derive a 32-byte key from a passphrase using SHA-256.
fn derive_key(key: &str) -> Vec<u8> {
    use sha2::{Sha256, Digest};
    let mut hasher = Sha256::new();
    hasher.update(key.as_bytes());
    hasher.finalize().to_vec()
}

/// Compute HMAC-SHA256 of the given data with the given key.
fn hmac_sha256(key: &[u8], data: &[u8]) -> Vec<u8> {
    use hmac::{Hmac, Mac};
    use sha2::Sha256;
    type HmacSha256 = Hmac<Sha256>;

    let mut mac = HmacSha256::new_from_slice(key)
        .expect("HMAC can take key of any size");
    mac.update(data);
    mac.finalize().into_bytes().to_vec()
}

/// Build the XOR key stream from derived key and IV, repeated to cover the needed length.
fn build_key_stream(derived: &[u8], iv: &[u8], length: usize) -> Vec<u8> {
    let combined: Vec<u8> = [derived, iv].concat();
    let repeats = (length / combined.len()) + 1;
    let mut stream = Vec::with_capacity(combined.len() * repeats);
    for _ in 0..repeats {
        stream.extend_from_slice(&combined);
    }
    stream.truncate(length);
    stream
}

/// Encrypt text with XOR-based stream cipher and HMAC authentication.
fn encrypt(text: &str, key: &str) -> Result<String, Box<dyn std::error::Error>> {
    use base64::Engine;
    use base64::engine::general_purpose::STANDARD;

    let derived = derive_key(key);

    // Generate 16 random bytes for IV
    let mut iv = [0u8; 16];
    getrandom::getrandom(&mut iv)?;

    let plaintext = text.as_bytes();
    let pad_len = 16 - (plaintext.len() % 16);
    let mut padded = plaintext.to_vec();
    padded.extend(std::iter::repeat(pad_len as u8).take(pad_len));

    let key_stream = build_key_stream(&derived, &iv, padded.len());
    let encrypted: Vec<u8> = padded.iter().zip(key_stream.iter()).map(|(a, b)| a ^ b).collect();

    let mut mac_input = iv.to_vec();
    mac_input.extend_from_slice(&encrypted);
    let mac = hmac_sha256(&derived, &mac_input);

    let mut payload = iv.to_vec();
    payload.extend_from_slice(&encrypted);
    payload.extend_from_slice(&mac);

    Ok(STANDARD.encode(&payload))
}

/// Decrypt text encrypted with the encrypt operation.
fn decrypt(ciphertext: &str, key: &str) -> Result<String, Box<dyn std::error::Error>> {
    use base64::Engine;
    use base64::engine::general_purpose::STANDARD;

    let derived = derive_key(key);
    let raw = STANDARD.decode(ciphertext)?;

    if raw.len() < 48 {
        return Err("Decryption failed: data too short".into());
    }

    let iv = &raw[..16];
    let mac_received = &raw[raw.len() - 32..];
    let encrypted = &raw[16..raw.len() - 32];

    let mut mac_input = iv.to_vec();
    mac_input.extend_from_slice(encrypted);
    let mac_computed = hmac_sha256(&derived, &mac_input);

    // Constant-time comparison
    if mac_received.len() != mac_computed.len()
        || mac_received.iter().zip(mac_computed.iter()).fold(0u8, |acc, (a, b)| acc | (a ^ b)) != 0
    {
        return Err("Decryption failed: invalid key or corrupted data".into());
    }

    let key_stream = build_key_stream(&derived, iv, encrypted.len());
    let decrypted: Vec<u8> = encrypted.iter().zip(key_stream.iter()).map(|(a, b)| a ^ b).collect();

    let pad_len = *decrypted.last().ok_or("Decryption failed: empty result")? as usize;
    if pad_len > decrypted.len() || pad_len == 0 {
        return Err("Decryption failed: invalid padding".into());
    }
    let plaintext = &decrypted[..decrypted.len() - pad_len];

    Ok(String::from_utf8(plaintext.to_vec())?)
}

/// Executes the tool logic.
fn run(params: &Params) -> Result<String, Box<dyn std::error::Error>> {
    match params.operation.as_str() {
        "encrypt" => encrypt(&params.text, &params.key),
        "decrypt" => decrypt(&params.text, &params.key),
        other => Err(format!("Invalid operation '{}'. Must be 'encrypt' or 'decrypt'.", other).into()),
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("usage: crypt <json-params>");
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
