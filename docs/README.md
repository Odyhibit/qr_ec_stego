# QR Code Steganography - Web Tool

This is a web-based interface for the QR Code Steganography tool. It provides an easy-to-use interface for encoding and decoding hidden messages in QR codes.

## Features

### Encode
- Generate QR codes with visible decoy messages
- Advanced QR options (version, ECC level, mask pattern)
- Download generated QR codes

### Decode
- Upload QR code images
- Decode visible messages using jsQR library

### Compare
- Upload two QR codes for comparison
- Visual difference highlighting
- Pixel-by-pixel analysis
- Check if QR codes have the same visible message


### Current Implementation

The web tool provides:
-  QR code generation using `qrcodegen` (Nayuki) library
-  QR code decoding using `jsQR` library
-  **Full steganography extraction** (padding and ECC secrets)
-  **In-browser stego encoding (versions 1-10)**
-  Visual comparison of QR codes

### Steganography Support

**Extraction (Decoding)**:  **Fully supported in JavaScript**
- Extract padding secrets from QR codes
- Extract ECC secrets from QR codes

**Encoding**:  In-browser for versions 1-10 (padding or ECC)


## Libraries Used

- **Tailwind CSS**: UI styling and dark mode
- **qrcodegen (Nayuki)**: QR code generation with codeword access
- **jsQR**: QR code decoding (by cozmo)





## File Structure

```
docs/
├── index.html          # Main HTML file
├── README.md           # This file
├── js/
│   ├── app.js          # Main application logic + UI
│   ├── qr-parser.js    # QR code structure parser
│   └── stego.js        # Stego encode/decode helpers
└── examples/
    ├── challenge1.png  # Example QR with padding secret
    └── challenge2.png  # Example QR with ECC secret
```

