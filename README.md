# QR Code Steganography

Hide secret messages in QR codes using padding bytes and error correction codes. This tool demonstrates steganographic techniques where QR codes can carry hidden data while still scanning normally.

## Features

- **Dual Hiding Locations**: Hide data in padding bytes OR error correction codes (ECC)
- **Maintains Functionality**: QR codes scan normally and display the decoy message
- **Web Interface**: Browser-based tool for demos and visualization
- **Python Tool**: Full-featured command-line interface for encoding/decoding

## Quick Start

### Web Tool (Try it now!)

Visit the web interface: [Live Demo](https://joshpbloom.github.io/qr_ec_stego/) 




### Python Tool (Full Features)

```bash
# Install dependencies
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install Pillow qrcode pyzbar

# Create a QR code with hidden message in padding
python padding_ecc_stego_v3_8bit.py encode \
  --decoy "SCAN ME!" \
  --secret "flag{hidden_in_padding}" \
  --version 5 --ecc H \
  --out stego_qr.png

# Extract the hidden message
python padding_ecc_stego_v3_8bit.py decode stego_qr.png --extract-padding

# Create a QR code with hidden message in ECC
python padding_ecc_stego_v3_8bit.py encode \
  --decoy "SCAN ME!" \
  --ecc-secret "flag{hidden_in_ecc}" \
  --version 5 --ecc H \
  --out stego_qr_ecc.png

# Extract from ECC
python padding_ecc_stego_v3_8bit.py decode stego_qr_ecc.png --extract-ecc 
```

## How It Works

### Method 1: Padding Bytes

QR codes pad data to a fixed length. Normally this padding is filled with specific patterns, but we can insert our secret message here instead.


### Method 2: Error Correction Codes

QR codes use Reed-Solomon error correction. We can be clever and alter the Error Correction to be whatever we want by changing the padding codewords.


### Requirements

**Python Tool:**
- Python 3.7+
- Pillow (image processing)
- qrcode (QR generation)
- pyzbar (QR decoding)

**Web Tool:**
- Modern web browser
- No installation needed (uses CDN libraries)


##  Web Tool Details

The web interface (`docs/`) provides:
-  QR code generation with custom parameters
-  QR code decoding (visible message)
-  Visual comparison of two QR codes
- ️ For higher versions/capacity, use the Python encoder

