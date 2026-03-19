//! Image Convert MCP tool - convert an image to a different format.
//!
//! Required crates: serde, serde_json, image

use std::env;
use std::path::Path;
use std::process;

use serde::Deserialize;

/// Supported output formats.
const SUPPORTED_FORMATS: &[&str] = &["png", "jpg", "jpeg", "webp", "bmp"];

/// Tool parameters.
#[derive(Deserialize)]
struct Params {
    /// Path to the source image file.
    input_path: String,
    /// Path where the converted image will be saved.
    output_path: String,
    /// Target format: png, jpg, webp, or bmp.
    format: String,
}

/// Map a format string to the image crate's ImageFormat.
fn resolve_format(fmt: &str) -> Result<image::ImageFormat, Box<dyn std::error::Error>> {
    match fmt {
        "jpg" | "jpeg" => Ok(image::ImageFormat::Jpeg),
        "png" => Ok(image::ImageFormat::Png),
        "webp" => Ok(image::ImageFormat::WebP),
        "bmp" => Ok(image::ImageFormat::Bmp),
        _ => Err(format!("Error: unsupported format '{}'. Supported: png, jpg, webp, bmp", fmt).into()),
    }
}

/// Executes the tool logic.
fn run(params: &Params) -> Result<String, Box<dyn std::error::Error>> {
    let fmt_lower = params.format.to_lowercase();
    if !SUPPORTED_FORMATS.contains(&fmt_lower.as_str()) {
        return Ok(format!(
            "Error: unsupported format '{}'. Supported: png, jpg, webp, bmp",
            params.format
        ));
    }

    let resolved_input = std::fs::canonicalize(&params.input_path)
        .unwrap_or_else(|_| std::path::absolute(Path::new(&params.input_path))
            .unwrap_or_else(|_| Path::new(&params.input_path).to_path_buf()));

    if !resolved_input.is_file() {
        return Ok(format!("Error: input file not found: {}", resolved_input.display()));
    }

    let resolved_output = std::path::absolute(Path::new(&params.output_path))
        .unwrap_or_else(|_| Path::new(&params.output_path).to_path_buf());

    let mut img = image::open(&resolved_input)?;
    let pillow_format = resolve_format(&fmt_lower)?;

    // Convert RGBA to RGB for formats that do not support alpha
    if matches!(pillow_format, image::ImageFormat::Jpeg | image::ImageFormat::Bmp) {
        if img.color().has_alpha() {
            img = image::DynamicImage::ImageRgb8(img.to_rgb8());
        }
    }

    img.save_with_format(&resolved_output, pillow_format)?;

    Ok(format!(
        "Image converted to {} and saved to {}",
        fmt_lower,
        resolved_output.display()
    ))
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("usage: image_convert <json-params>");
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
