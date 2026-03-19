//! Image Resize MCP tool - resize an image to the specified dimensions.
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
    /// Path where the resized image will be saved.
    output_path: String,
    /// Target width in pixels.
    width: u32,
    /// Target height in pixels.
    height: u32,
}

/// Executes the tool logic.
fn run(params: &Params) -> Result<String, Box<dyn std::error::Error>> {
    if params.width == 0 || params.height == 0 {
        return Ok("Error: width and height must be positive integers".to_string());
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

    let img = image::open(&resolved_input)?;
    // Use Lanczos3 filter, equivalent to PIL's LANCZOS
    let resized = img.resize_exact(params.width, params.height, image::imageops::FilterType::Lanczos3);
    resized.save(&resolved_output)?;

    Ok(format!(
        "Image resized to {}x{} and saved to {}",
        params.width,
        params.height,
        resolved_output.display()
    ))
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("usage: image_resize <json-params>");
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
