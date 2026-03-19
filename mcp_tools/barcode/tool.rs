//! Barcode MCP tool - generate or read barcodes.
//!
//! Required crates: serde, serde_json, barcoders, image, rxing

use std::env;
use std::fs;
use std::path::Path;
use std::process;

use serde::Deserialize;

/// Supported barcode types.
const SUPPORTED_BARCODE_TYPES: &[&str] = &["code128", "ean13", "upc"];

/// Tool parameters.
#[derive(Deserialize)]
struct Params {
    /// Operation: 'generate' or 'read'.
    operation: String,
    /// Data to encode (required for generate).
    #[serde(default)]
    content: String,
    /// Output path (generate) or input path (read).
    #[serde(default)]
    image_path: String,
    /// Barcode format: code128, ean13, upc. Defaults to code128.
    #[serde(rename = "type", default = "default_barcode_type")]
    barcode_type: String,
}

/// Default barcode type.
fn default_barcode_type() -> String {
    "code128".to_string()
}

/// Strip common image extensions so we can add our own.
fn strip_image_extension(path: &str) -> &str {
    for ext in &[".png", ".svg", ".jpg", ".jpeg"] {
        if path.to_lowercase().ends_with(ext) {
            return &path[..path.len() - ext.len()];
        }
    }
    path
}

/// Generate a barcode image using the barcoders crate.
fn generate(data: &str, output_path: &str, barcode_type: &str) -> Result<String, Box<dyn std::error::Error>> {
    use barcoders::sym::code128::Code128;
    use barcoders::sym::ean13::EAN13;

    if data.trim().is_empty() {
        return Err("Data cannot be empty".into());
    }

    if !SUPPORTED_BARCODE_TYPES.contains(&barcode_type) {
        return Err(format!(
            "Unsupported barcode type: {}. Supported types: {}",
            barcode_type,
            SUPPORTED_BARCODE_TYPES.join(", ")
        ).into());
    }

    // Ensure output directory exists
    let output_dir = Path::new(output_path).parent();
    if let Some(dir) = output_dir {
        if !dir.as_os_str().is_empty() {
            fs::create_dir_all(dir)?;
        }
    }

    let encoded: Vec<u8> = match barcode_type {
        "code128" => {
            Code128::new(data)
                .map_err(|e| format!("Code128 encoding error: {}", e))?
                .encode()
        }
        "ean13" => {
            EAN13::new(data)
                .map_err(|e| format!("EAN13 encoding error: {}", e))?
                .encode()
        }
        "upc" => {
            // UPC-A is essentially EAN13 with a leading 0
            let padded = if data.len() < 13 {
                format!("{:0>13}", data)
            } else {
                data.to_string()
            };
            EAN13::new(&padded)
                .map_err(|e| format!("UPC encoding error: {}", e))?
                .encode()
        }
        _ => return Err(format!("Unsupported barcode type: {}", barcode_type).into()),
    };

    // Render the barcode as a PNG image
    let base_path = strip_image_extension(output_path);
    let final_path = format!("{}.png", base_path);

    let bar_height = 100u32;
    let bar_width = 2u32;
    let img_width = (encoded.len() as u32) * bar_width;
    let img_height = bar_height;

    let mut imgbuf = image::GrayImage::new(img_width, img_height);

    for (i, &bit) in encoded.iter().enumerate() {
        let color = if bit == 1 { 0u8 } else { 255u8 };
        for bw in 0..bar_width {
            let x = (i as u32) * bar_width + bw;
            for y in 0..img_height {
                imgbuf.put_pixel(x, y, image::Luma([color]));
            }
        }
    }

    imgbuf.save(&final_path)?;

    Ok(format!("Barcode saved to {}", final_path))
}

/// Read and decode a barcode from an image file using rxing.
fn read(image_path: &str) -> Result<String, Box<dyn std::error::Error>> {
    if !Path::new(image_path).is_file() {
        return Err(format!("Image file not found: {}", image_path).into());
    }

    let results = rxing::helpers::detect_multiple_in_file(image_path)
        .map_err(|e| format!("No barcode found in image: {} ({})", image_path, e))?;

    if results.is_empty() {
        return Err(format!("No barcode found in image: {}", image_path).into());
    }

    let entries: Vec<String> = results
        .iter()
        .map(|r| format!("[{}] {}", r.getBarcodeFormat(), r.getText()))
        .collect();

    Ok(entries.join("\n"))
}

/// Executes the tool logic.
fn run(params: &Params) -> Result<String, Box<dyn std::error::Error>> {
    match params.operation.as_str() {
        "generate" => generate(&params.content, &params.image_path, &params.barcode_type),
        "read" => read(&params.image_path),
        other => Err(format!("Invalid operation '{}'. Must be 'generate' or 'read'.", other).into()),
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("usage: barcode <json-params>");
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
