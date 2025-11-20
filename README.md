# QR Code Steganography

Hide secret messages in QR codes using padding bytes and error correction codes. This tool demonstrates steganographic techniques where QR codes can carry hidden data while still scanning normally.

## 🌟 Features

- **Dual Hiding Locations**: Hide data in padding bytes OR error correction codes (ECC)
- **Maintains Functionality**: QR codes scan normally and display the decoy message
- **CTF Challenges**: Ready-to-use capture-the-flag challenges included
- **Web Interface**: Browser-based tool for demos and visualization
- **Python Tool**: Full-featured command-line interface for encoding/decoding

## 🚀 Quick Start

### Web Tool (Try it now!)

Visit the web interface: [Live Demo](https://joshpbloom.github.io/qr_ec_stego/) (update URL when deployed)

Or run locally:
```bash
# Open docs/index.html in your browser
open docs/index.html
```

The web tool is perfect for:
- Demonstrating the concept
- Decoding QR codes visually
- Comparing QR code differences
- Educational purposes

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
  --k-per-block 8 \
  --out stego_qr_ecc.png

# Extract from ECC
python padding_ecc_stego_v3_8bit.py decode stego_qr_ecc.png \
  --extract-ecc --k-per-block 8
```

## 📚 How It Works

### Method 1: Padding Bytes

QR codes pad data to a fixed length. Normally this padding is filled with specific patterns, but we can insert our secret message here instead.

- ✅ **Pros**: Simple, doesn't affect error correction
- ⚠️ **Cons**: Limited capacity (depends on decoy message length)

### Method 2: Error Correction Codes

QR codes use Reed-Solomon error correction. We can replace some ECC bytes with our secret while maintaining enough error correction for the QR to still scan.

- ✅ **Pros**: More capacity, works with any decoy length
- ⚠️ **Cons**: Reduces error correction capability

## 🎮 CTF Challenges

The `ctf_challenges/` folder contains ready-to-use challenges:

### Challenge 1: Hidden in Plain Sight (100 points)
- QR code appears normal when scanned
- Secret hidden in padding bytes
- **Flag**: `flag{h1dd3n_1n_th3_p4dd1ng_byt3s}`

### Challenge 2: Compromised Integrity (300 points)
- Two QR codes with the same visible message
- Secret hidden in error correction codes
- **Flag**: `flag{3cc_bits_c0mpr0m1s3d}`

See `ctf_challenges/README_ORGANIZER.md` for full documentation.

## 🖥️ Project Structure

```
qr_ec_stego/
├── README.md                          # This file
├── padding_ecc_stego_v3_8bit.py       # Main Python tool
├── docs/                              # Web interface (GitHub Pages)
│   ├── index.html                     # Web UI
│   ├── js/                            # JavaScript modules
│   └── examples/                      # Example QR codes
└── ctf_challenges/                    # CTF challenges
    ├── challenge1_qr.png              # Challenge 1 image
    ├── challenge2_qr.png              # Challenge 2 image
    ├── challenge1_description.md      # Challenge 1 details
    ├── challenge2_description.md      # Challenge 2 details
    ├── solution_challenge1.py         # Solution script 1
    ├── solution_challenge2.py         # Solution script 2
    └── solution_manual.py             # Step-by-step educational solution
```

## 🎯 Use Cases

1. **Security Research**: Study steganography techniques
2. **CTF Competitions**: Use included challenges or create your own
3. **Education**: Teach QR code structure and error correction
4. **Demonstrations**: Web tool for visual explanations
5. **Data Hiding**: Covert communication (educational purposes)

## 🔧 Technical Details

### Requirements

**Python Tool:**
- Python 3.7+
- Pillow (image processing)
- qrcode (QR generation)
- pyzbar (QR decoding)

**Web Tool:**
- Modern web browser
- No installation needed (uses CDN libraries)

### Supported QR Versions

- Versions 1-40 (21×21 to 177×177 modules)
- All ECC levels (L, M, Q, H)
- All mask patterns (0-7)

### Capacity

**Padding Steganography:**
- Depends on decoy message length
- Version 5, ECC H: ~30-40 bytes available

**ECC Steganography:**
- Configurable via `k_per_block` parameter
- Version 5, ECC H, k=8: ~32 bytes available
- More capacity with higher versions

## 📖 Documentation

- **Python Tool**: Run `python padding_ecc_stego_v3_8bit.py --help`
- **Web Tool**: See `docs/README.md`
- **CTF Challenges**: See `ctf_challenges/README_ORGANIZER.md`
- **Quick Reference**: See `ctf_challenges/QUICK_REFERENCE.md`

## 🧪 Testing

```bash
# Run CTF challenge solutions
cd ctf_challenges
python solution_challenge1.py
python solution_challenge2.py
python solution_manual.py
```

## 🌐 Web Tool Details

The web interface (`docs/`) provides:
- ✅ QR code generation with custom parameters
- ✅ QR code decoding (visible message)
- ✅ **Full steganography extraction** (padding and ECC secrets)
- ✅ Visual comparison of two QR codes
- ✅ Dark mode optimized design
- ✅ Export analysis reports
- ⚠️ Note: Steganography encoding still requires Python tool

**New in latest update**: The JavaScript version can now extract hidden messages from QR codes! Try it with the built-in CTF challenge examples.

The web tool is designed for:
- Demonstrations and education
- Steganography extraction (decoding)
- Visual analysis
- CTF challenge distribution
- Quick QR code generation/decoding

## 🚧 Limitations

1. **Web Tool Encoding**: JavaScript version can't encode steganography (use Python tool for creating QR codes with secrets)
2. **Web Tool Extraction**: Works well but may be less robust than Python with damaged images
3. **Error Correction**: Compromising too many ECC bytes makes QR unscannable
4. **Capacity**: Limited by QR version and decoy message length
5. **Detection**: Statistical analysis could detect steganography

## 🤝 Contributing

This is an educational and research project. Contributions welcome!

## ⚖️ License

This project is for educational and security research purposes. Use responsibly and ethically.

## 🔗 Links

- **Live Demo**: [GitHub Pages](https://joshpbloom.github.io/qr_ec_stego/) (update when deployed)
- **Repository**: [GitHub](https://github.com/joshpbloom/qr_ec_stego) (update with actual URL)

## 🎓 Educational Notes

This tool demonstrates:
- QR code internal structure
- Reed-Solomon error correction
- Steganography techniques
- CTF challenge design
- Web-based security tools

**Use for**: Education, CTF competitions, security research
**Not for**: Malicious purposes, evasion of security controls

---

Created for educational purposes | Use responsibly
