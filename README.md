# QR Code Steganography

Hide secret messages in QR codes using padding bytes and error correction codes. This tool demonstrates steganographic techniques where QR codes can carry hidden data while still scanning normally.

## Features

- **Dual Hiding Locations**: Hide data in padding bytes OR error correction codes (ECC)
- **Maintains Functionality**: QR codes scan normally and display the decoy message
- **Web Interface**: Browser-based tool for demos and visualization
- **Python Tool**: Full-featured command-line interface for encoding/decoding

## Quick Start

### Web Tool (Try it now!)

Visit the web interface: [Live Demo](https://odyhibit.github.io/qr_ec_stego/)


## How It Works

### Method 1: Padding Bytes

QR codes pad data to a fixed length. Normally this padding is filled with specific patterns, but we can insert our secret message here instead.


### Method 2: Error Correction Codes

QR codes use Reed-Solomon error correction. We can be clever and alter the Error Correction to be whatever we want by changing the padding codewords. Since we can only guarantee the last block has padding we write our secret message backward. We start with a one byte int to tell us how long the message is.




