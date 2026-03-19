//! Image Crop MCP tool - crop an image to the specified bounding box.
//!
//! Required crates: serde, serde_json, image

use std::env;
use std::path::Path;
use std::process;

use serde::Deserialize;

/// Tool parameters.
#[derive(Deserialize)]
struct Params {
    /// Path to the source image file.
    input_path: String,
    /// Path where the cropped image will be saved.
    output_path: String,
    /// Left edge of the crop box in pixels.
    left: u32,
    /// Top edge of the crop box in pixels.
    top: u32,
    /// Right edge of the crop box in pixels.
    right: u32,
    /// Bottom edge of the crop box in pixels.
    bottom: u32,
}

/// Executes the tool logic.
fn run(params: &Params) -> Result<String, Box<dyn std::error::Error>> {
    if params.left >= params.right || params.top >= params.bottom {
        return Ok(
            "Error: invalid crop box — left must be less than right, top must be less than bottom"
                .to_string(),
        );
    }

    let resolved_input = std::fs::canonicalize(&params.input_path)
        .unwrap_or_else(|_| std::path::absolute(Path::new(&params.input_path))
            .unwrap_or_else(|_| Path::new(&params.input_path).to_path_buf()));

    if !resolved_input.is_file() {
        return Ok(format!(
            "Error: input file not found: {}",
            resolved_input.display()
        ));
    }

    let resolved_output = std::path::absolute(Path::new(&params.output_path))
        .unwrap_or_else(|_| Path::new(&params.output_path).to_path_buf());

    let mut img = image::open(&resolved_input)?;

    let crop_width = params.right - params.left;
    let crop_height = params.bottom - params.top;

    let cropped = img.crop(params.left, params.top, crop_width, crop_height);
    cropped.save(&resolved_output)?;

    Ok(format!(
        "Image cropped to {}x{} and saved to {}",
        crop_width,
        crop_height,
        resolved_output.display()
    ))
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("usage: image_crop <json-params>");
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
