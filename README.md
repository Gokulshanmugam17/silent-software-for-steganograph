# SILENT

SILENT is a Python steganography project for hiding text or files inside text, images, audio, and video. It includes a Flask web interface, a command-line interface, and reusable steganography modules under `steganography/`.

## What the project supports

- Text steganography using zero-width Unicode characters
- Image steganography using LSB techniques on lossless formats
- Audio steganography using LSB techniques on WAV output
- Video steganography using frame-based LSB techniques
- Optional password-based encryption using `cryptography.Fernet`
- Optional message expiration ("Dead-Man Switch")
- Decoy-message behavior on failed password attempts
- Two-layer and CLI-driven multi-layer workflows

## Project structure

```text
SILENT-APP/
|-- main.py
|-- cli.py
|-- requirements.txt
|-- users.json
|-- history.json
|-- steganography/
|   |-- text_stego.py
|   |-- image_stego.py
|   |-- audio_stego.py
|   |-- video_stego.py
|   |-- multi_layer_stego.py
|   `-- utils.py
|-- web_app/
|   |-- app.py
|   |-- templates/
|   `-- static/
|-- README.md
|-- FEATURES.md
|-- PROJECT_DOCUMENTATION.md
`-- NEED_FOR_THE_STUDY.md
```

## Requirements

- Python 3.8+
- `pip`
- FFmpeg recommended for broader audio/video format support

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the web app

Start the Flask app through the launcher:

```bash
python main.py
```

Default URL:

```text
http://127.0.0.1:8080
```

You can also choose a different port:

```bash
python main.py 8081
```

### Login

User accounts are loaded from `users.json`. Update that file to change usernames or passwords for your local environment.

## Run the CLI

Show CLI help:

```bash
python cli.py -h
```

Hide text in an image:

```bash
python cli.py hide image cover.png output.png -t "Secret message" -p "mypassword"
```

Extract text from an image:

```bash
python cli.py extract image output.png -p "mypassword"
```

Get media information:

```bash
python cli.py info video sample.mp4
```

Run a multi-layer hide flow:

```bash
python cli.py multilayer hide --text "Secret" --layers image,video --covers cover.png,cover.mp4 --outputs layer1.png,final.avi --passwords p1,p2
```

## Media notes

- Text mode hides secret data inside visible cover text using zero-width characters.
- Image text and file hiding are most reliable with `.png`, `.bmp`, `.tiff`, or `.tif`.
- Audio processing accepts several formats as input, but stego output is written as `.wav`.
- Video stego output is typically written as `.avi` for better reliability during embedding.
- Lossy compression can damage hidden data. Prefer lossless carriers wherever possible.

## Documentation files

- `README.md`: quick start and usage
- `FEATURES.md`: implemented capabilities and current limitations
- `PROJECT_DOCUMENTATION.md`: module-level technical overview
- `NEED_FOR_THE_STUDY.md`: academic background and problem statement

## Important note about the repository

There is also a nested `silent-steganography-application/` directory that appears to be a second copy of the project. The top-level files in this workspace are the primary documentation source updated here.
