# Project Documentation: SILENT (Secure Information Layering Engine)

## 📄 Abstract

**SILENT** (Secure Information Layering Engine for Non-Traceable Transmission) is a comprehensive web-based steganography application designed to address the growing need for secure, covert communication in the digital age. While traditional encryption safeguards the *content* of a message, it inevitably flags the communication as sensitive. Steganography, conversely, conceals the *existence* of the message entirely.

This project implements advanced steganographic algorithms to embed secret data (text or files) into a diverse range of carrier media, including **Text** (using Zero-Width Characters), **Images** (LSB substitution), **Audio** (LSB encoding), and **Video** (Frame-based embedding). Beyond core hiding capabilities, SILENT integrates robust security measures such as **AES-256 encryption** and a novel **"Dead-Man Switch"** mechanism, which ensures data is rendered inaccessible after a specified expiration time. All features are presented through a modern, responsive **Glassmorphism Web Interface**, making advanced security tools accessible to non-technical users while providing powerful capabilities for security professionals.

---

## 🛑 Existing System

The current landscape of steganography tools is fragmented and often user-unfriendly. Existing systems typically suffer from the following limitations:

1.  **Single-Media Limitation**: Most available tools specialize in only one medium (usually images or audio). Users requiring versatility must install and learn multiple distinct applications.
2.  **Lack of integrated Encryption**: Many steganography tools hide data in plaintext. Once the carrier file is analyzed and the hidden data detected, the secret is immediately compromised.
3.  **Command-Line Dependency**: Powerful steganography tools (like Steghide or OpenStego) often rely heavily on Command Line Interfaces (CLI), creating a high barrier to entry for average users.
4.  **Absence of Advanced Security Features**: Standard tools lack "fail-safe" mechanisms. If a password is forced or stolen, the data is yielded. There are no provisions for decoy data or time-based self-destruction.
5.  **No Recursive Hiding**: Existing systems generally perform a single layer of hiding (Data → Carrier). They lack automated support for "Multi-Layer" steganography (e.g., hiding text in an image, then hiding that image in an audio file), which exponentially increases the difficulty of steganalysis.

---

## ✅ Proposed System

**SILENT** proposes a unified, all-in-one platform that integrates multiple steganography domains into a single, secure ecosystem. The system introduces several key advancements:

1.  **Universal Media Support**:
    *   **Text Steganography**: Uses invisible Zero-Width Characters to hide messages within normal text (e.g., emails, chats) without altering the visual appearance.
    *   **Image Steganography**: Implements Least Significant Bit (LSB) algorithms for lossless formats (PNG, BMP) to hide data without perceptual distortion.
    *   **Audio & Video Steganography**: Extends hiding capabilities to dynamic media like WAV audio and AVI video files using frame/sample manipulation.

2.  **Multi-Layer Architecture**:
    *   The proposed system features a dedicated **Multi-Layer Module** that automates recursive hiding (e.g., Layer 1: Secret Text inside Image; Layer 2: That Image inside Video). This "Russian Doll" approach makes detection significantly harder for forensic analysis.

3.  **Enhanced Security Framework**:
    *   **AES-256 Encryption**: All data is encrypted *before* embedding, ensuring that extraction without the correct key yields only random noise.
    *   **Dead-Man Switch**: A time-based expiration feature. Users can set a validity period (e.g., 24 hours); if extraction is attempted after this window, the system validates the timestamp and refuses to decrypt constraints, effectively "destroying" the message.
    *   **Decoy Mode**: Option to generate fake/decoy messages if an incorrect password is entered, misleading potential attackers.

4.  **Modern User Experience**:
    *   The system replaces complex CLIs with a **Premium Web Interface** featuring a Cyber-Grid Glassmorphism design.
    *   Includes **Real-Time Previews**, **Operation History Tracking**, and **Drag-and-Drop** support, streamlining the workflow for efficiency and ease of use.

---

## 🧩 System Modules

The project is structured into distinct functional modules, each handling specific aspects of the steganographic process:

### 1. 🔡 Text Steganography Module
*   **Purpose**: Hiding secret text within a visible "cover" text string.
*   **Mechanism**: Utilizes Unicode **Zero-Width Characters** (Zero-Width Joiner [U+200D], Zero-Width Non-Joiner [U+200C], etc.). These characters render invisibly in standard text editors and browsers but carry binary data.
*   **Capacity**: High (relative to the cover length) without affecting visual layout.
*   **Use Case**: Concealing messages in emails, code comments, or chat logs.

### 2. 🖼️ Image Steganography Module
*   **Purpose**: Embedding text or small files within image containers.
*   **Mechanism**: **Least Significant Bit (LSB)** substitution. The module modifies the last bit of the RGB color channels of pixels to store data. Since the change is minimal (±1 in color value), it is undetectable to the human eye.
*   **Supported Formats**: Lossless formats like **PNG** and **BMP** to prevent compression artifacts from destroying hidden data.

### 3. 🎵 Audio Steganography Module
*   **Purpose**: Hiding data within audio streams.
*   **Mechanism**: Modifies the LSB of audio samples in **WAV** files. Similar to images, this slight alteration in amplitude is inaudible to human hearing.
*   **Features**: Supports custom frequency selection to strictly target non-perceptible ranges.

### 4. 🎬 Video Steganography Module
*   **Purpose**: Embedding large amounts of data across video frames.
*   **Mechanism**: Frame-by-frame LSB injection. The video is treated as a sequence of images; data is distributed across frames, allowing for larger payloads than static images.
*   **Output**: Generates **AVI** files to maintain frame integrity without aggressive compression.

### 5. 🧱 Multi-Layer Steganography Module
*   **Purpose**: Advanced recursive hiding for maximum security.
*   **Mechanism**:
    *   **Inner Layer**: Encrypts and hides the secret payload into a *Carrier A* (e.g., Text into Image).
    *   **Outer Layer**: Takes *Carrier A* and hides it into *Carrier B* (e.g., that Image into Video).
*   **Extraction**: Requires "unpeeling" layers in reverse order with multiple keys.

### 6. 🔐 Cryptography & Security Module
*   **Purpose**: Ensuring data confidentiality and integrity.
*   **Algorithms**:
    *   **AES-256 (Fernet)**: Industrial-grade symmetric encryption.
    *   **PBKDF2-HMAC-SHA256**: Key derivation with 480,000 iterations to prevent brute-force attacks.
*   **Dead-Man Switch Logic**: Checks current server time against the embedded expiration timestamp during extraction. If expired, decryption keys are withheld.

### 7. 💻 Web Interface Module
*   **Purpose**: Providing an intuitive user interaction layer.
*   **Stack**: **Flask (Python)** backend serving **HTML5/CSS3/JavaScript** frontend.
*   **Design**: Implements a "Glassmorphism" aesthetic with blur effects, translucent panels, and a Cyber-Grid background.
*   **Features**:
    *   **Drag-and-Drop API**: Simplified file handling.
    *   **History Manager**: Uses LocalStorage to track recent operations.
    *   **Async Processing**: Handles large files without freezing the UI.
