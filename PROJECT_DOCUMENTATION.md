# Project Documentation: SILENT

## 1. Overview

SILENT is a multi-medium steganography application built in Python. The project combines steganographic embedding, optional password-based encryption, expiration-aware payload handling, and both web and CLI interfaces.

The current top-level project contains the active implementation used by:

- `main.py` for launching the web application
- `cli.py` for command-line operations
- `web_app/app.py` for Flask routes
- `steganography/*.py` for the core hiding and extraction logic

## 2. Application architecture

The codebase is organized into three main layers:

### Presentation layer

- `web_app/app.py`
- `web_app/templates/`
- `web_app/static/`

This layer handles login, file uploads, API responses, result downloads, and browser-based interaction.

### Interface layer

- `main.py`
- `cli.py`

This layer provides entry points for end users. `main.py` launches the Flask app and opens the browser. `cli.py` exposes terminal commands for hide, extract, info, and multi-layer operations.

### Core steganography layer

- `steganography/text_stego.py`
- `steganography/image_stego.py`
- `steganography/audio_stego.py`
- `steganography/video_stego.py`
- `steganography/multi_layer_stego.py`
- `steganography/utils.py`

This layer contains the algorithms for embedding, extracting, encrypting, decrypting, and handling metadata.

## 3. Module breakdown

### 3.1 `text_stego.py`

Purpose:
- Hide secret text inside visible text using zero-width Unicode characters

Key behavior:
- Uses zero-width characters to represent binary data
- Inserts the hidden payload into the cover text near the first sentence break or midpoint
- Supports optional password-based encryption
- Supports optional expiration headers
- Can return a decoy message when decryption fails and decoy mode is enabled

### 3.2 `image_stego.py`

Purpose:
- Hide and extract text, files, and images in still-image carriers

Key behavior:
- Converts image content to arrays using Pillow and NumPy
- Embeds text or file bits into pixel LSBs
- Uses a delimiter and simple metadata headers for extraction
- Supports image-in-image hiding through 4-bit channel substitution

Important note:
- Reliable carriers are lossless formats such as PNG, BMP, TIFF, and TIF

### 3.3 `audio_stego.py`

Purpose:
- Hide and extract text, files, and audio in sound carriers

Key behavior:
- Uses `pydub` to normalize audio input into 16-bit PCM sample arrays
- Embeds text and file content in sample LSBs
- Supports audio-in-audio hiding through 4-bit substitution
- Writes output as WAV to preserve embedded data more safely

Important note:
- Non-WAV inputs may require FFmpeg to be installed and available in `PATH`

### 3.4 `video_stego.py`

Purpose:
- Hide and extract text, files, and videos in frame-based carriers

Key behavior:
- Uses OpenCV for frame I/O
- Embeds data into frame pixel LSBs
- Adds metadata headers for text and file extraction
- Supports video-in-video hiding with 4-bit per-channel substitution
- Includes bit-shift-tolerant extraction logic by searching multiple alignments

Important note:
- Codec support depends on the local OpenCV and FFmpeg environment
- AVI output is generally preferred for embedding reliability

### 3.5 `multi_layer_stego.py`

Purpose:
- Coordinate recursive hide and extract workflows across media types

Key behavior:
- Accepts a list of layer configurations
- Uses module-specific handlers per layer
- Prefers file-based intermediate layers where possible to reduce corruption risk
- Supports auto-extraction when nested outputs are themselves stego carriers

### 3.6 `utils.py`

Purpose:
- Provide shared binary, encryption, expiration, and file helper functions

Key behavior:
- Binary conversion helpers for text and raw bytes
- Password-derived key generation using PBKDF2
- `Fernet` encryption and decryption for messages and files
- Expiration header creation and checking
- Decoy message generation
- Optional destructive wipe helper

## 4. Web application flow

### Authentication

- User credentials are read from `users.json`
- Flask sessions track login state
- Unauthenticated users are redirected to `/login`

### Main processing endpoint

The `/process` route handles:

- text hide/extract without uploaded carrier files for text mode
- text hide/extract inside image, audio, and video carriers
- file or media hiding in supported carriers
- smart extraction that tries text first, then file extraction, then specialized media extraction

### Multi-layer endpoint

The `/multilayer` route handles:

- two-layer hide operations from the web interface
- automatic extraction through nested layers when possible

### History and downloads

- `history.json` stores recent operations
- `/download/<filename>` serves generated files
- `/cleanup` resets the uploads directory

## 5. CLI flow

`cli.py` provides these command groups:

- `hide`
- `extract`
- `info`
- `multilayer`

The CLI instantiates image, audio, video, and multi-layer handlers directly and prints progress to the terminal.

## 6. Security model in the current implementation

Implemented:

- Optional encryption for text and file payloads
- Expiration-aware messages
- Decoy-message mode
- Password handling per layer in multi-layer flows

Practical caveats:

- Some media-in-media hiding modes use 4-bit substitution rather than fully lossless file embedding
- The wipe helper is intentionally destructive and can corrupt the whole carrier file
- Hard-coded Flask secret keys and plaintext `users.json` credentials are acceptable for a student/local project but should be changed for production use

## 7. Dependencies

Main packages from `requirements.txt`:

- `Flask`
- `cryptography`
- `pycryptodome`
- `Pillow`
- `numpy`
- `opencv-python`
- `pydub`
- `customtkinter`

Operational notes:

- Audio conversion is more reliable with FFmpeg installed
- Video codec availability depends on the local OpenCV build

## 8. Known repository note

The repository also contains a nested `silent-steganography-application/` directory that appears to be another copy of the project. For documentation and maintenance, the top-level workspace files should be treated as the active source unless the team intentionally switches to the nested copy.
