# SILENT Features

This document lists the features implemented in the current codebase and calls out the practical limits that matter when using or documenting the project.

## Core capabilities

### Text steganography

- Hides secret text inside normal-looking cover text with zero-width characters
- Supports optional password protection
- Supports optional expiration headers for time-limited messages
- Supports decoy-message output when decryption fails and decoy mode is enabled

### Image steganography

- Hides text in image pixels using LSB embedding
- Hides arbitrary files in images with a metadata header
- Hides one image inside another image using 4-bit channel substitution
- Extracts hidden text, files, or embedded images
- Best suited for lossless formats such as PNG, BMP, and TIFF

### Audio steganography

- Hides text in audio samples using LSB embedding
- Hides arbitrary files in audio using a metadata header
- Hides one audio signal inside another using 4-bit sample substitution
- Extracts hidden text, files, or embedded audio
- Accepts multiple audio input formats through `pydub`, but saves stego output as WAV

### Video steganography

- Hides text across video frames using LSB embedding
- Hides arbitrary files in video with a metadata header
- Hides one video inside another using per-channel 4-bit substitution
- Extracts text, files, or embedded video from stego videos
- Uses bit-shift tolerant extraction logic for improved recovery
- Prefers AVI-based output during embedding for better fidelity

### Multi-layer workflow

- CLI supports multi-layer hide and extract flows
- Web app supports two-step layered hide and auto-extraction
- Intermediate file-based layers use `hide_file` and `extract_file` where available to reduce data loss

## Security-related features

- Password-derived encryption with PBKDF2 and `Fernet`
- Expiration header support through the "Dead-Man Switch" behavior
- Optional decoy message generation on failed decryption
- Optional destructive wipe helper used by some expiration or failed-access paths

## Web application features

- Flask-based login flow using `users.json`
- Upload-based processing for text, image, audio, video, and multi-layer operations
- Download endpoints for generated outputs
- Operation history stored in `history.json`
- Cleanup endpoint for clearing uploaded working files

## CLI features

- `hide`, `extract`, and `info` commands for image, audio, and video
- `multilayer hide` and `multilayer extract` commands
- Optional output file saving for extracted text
- Simple terminal progress display

## Current limitations

- Lossy formats can damage hidden data, especially for image and video steganography
- Audio and video support may depend on FFmpeg/OpenCV codec availability on the local machine
- Some destructive wipe paths overwrite the carrier file rather than surgically clearing only hidden bits
- The documentation previously described some behaviors more broadly than the implementation; this file reflects the code in the current workspace
- The repository includes a nested duplicate project folder, which can cause confusion about which copy is active
