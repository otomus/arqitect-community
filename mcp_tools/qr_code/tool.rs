//! QR Code MCP tool - generate or read QR codes.
//!
//! Required crates: serde, serde_json, qrcode, image, rxing

use std::env;
use std::fs;
use std::path::Path;
use std::process;

use serde::Deserialize;

/// Tool parameters.
#[derive(Deserialize)]
struct Params {
    /// Operation: 'generate' or 'read'.
    operation: String,
    /// Data to encode into a QR code (required for generate).
    #[serde(default)]
    content: String,
    /// Path for the output image (generate) or input image (read).
    #[serde(default)]
    image_path: String,
}

/// Generate a QR code image and save it to a file.
fn generate(data: &str, output_path: &str) -> Result<String, Box<dyn std::error::Error>> {
    if data.trim().is_empty() {
        return Err("Data cannot be empty".into());
    }

    // Ensure output directory exists
    let output_dir = Path::new(output_path).parent();
    if let Some(dir) = output_dir {
        if !dir.as_os_str().is_empty() {
            fs::create_dir_all(dir)?;
        }
    }

    // Generate QR code with medium error correction, matching Python's ERROR_CORRECT_M
    let qr = qrcode::QrCode::with_error_correction_level(data, qrcode::EcLevel::M)?;

    // Render to image with settings matching the Python version:
    // box_size=10, border=4, black on white
    let img = qr
        .render::<image::Luma<u8>>()
        .quiet_zone(true)
        .module_dimensions(10, 10)
        .build();

    img.save(output_path)?;

    Ok(format!("QR code saved to {}", output_path))
}

/// Read and decode a QR code from an image file using rxing.
fn read(image_path: &str) -> Result<String, Box<dyn std::error::Error>> {
    if !Path::new(image_path).is_file() {
        return Err(format!("Image file not found: {}", image_path).into());
    }

    let results = rxing::helpers::detect_multiple_in_file(image_path)
        .map_err(|e| format!("No QR code found in image: {} ({})", image_path, e))?;

    if results.is_empty() {
        return Err(format!("No QR code found in image: {}", image_path).into());
    }

    let decoded: Vec<String> = results
        .iter()
        .map(|r| r.getText().to_string())
        .collect();

    Ok(decoded.join("\n"))
}

/// Executes the tool logic.
fn run(params: &Params) -> Result<String, Box<dyn std::error::Error>> {
    match params.operation.as_str() {
        "generate" => generate(&params.content, &params.image_path),
        "read" => read(&params.image_path),
        other => Err(format!("Invalid operation '{}'. Must be 'generate' or 'read'.", other).into()),
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("usage: qr_code <json-params>");
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
