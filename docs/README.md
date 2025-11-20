# QR Code Steganography - Web Tool

This is a web-based interface for the QR Code Steganography tool. It provides an easy-to-use interface for encoding and decoding hidden messages in QR codes.

## Features

### Encode
- Generate QR codes with visible decoy messages
- Dark mode optimized interface
- Advanced QR options (version, ECC level, mask pattern)
- Download generated QR codes

### Decode
- Upload QR code images
- Decode visible messages using jsQR library
- Try example QR codes from the CTF challenges
- Export analysis reports

### Compare
- Upload two QR codes for comparison
- Visual difference highlighting
- Pixel-by-pixel analysis
- Check if QR codes have the same visible message

## Deployment

This folder is ready for GitHub Pages deployment:

1. Push this repository to GitHub
2. Go to repository Settings → Pages
3. Select "Deploy from a branch"
4. Choose `main` branch and `/docs` folder
5. Your site will be live at `https://yourusername.github.io/qr_ec_stego/`

## Technical Notes

### Current Implementation

The web tool provides:
- ✅ QR code generation using `qrcode-generator` library
- ✅ QR code decoding using `jsQR` library
- ✅ **Full steganography extraction** (padding and ECC secrets)
- ✅ Custom QR structure parser
- ✅ Visual comparison of QR codes
- ✅ Dark mode interface
- ✅ Example QR codes to try
- ✅ Export functionality

### Steganography Support

**Extraction (Decoding)**: ✅ **Fully supported in JavaScript**
- Extract padding secrets from QR codes
- Extract ECC secrets from QR codes
- Works with CTF challenge examples
- Configurable k-per-block for ECC extraction

**Encoding**: Use Python tool
- **Creating QR with secrets**: Use `padding_ecc_stego_v3_8bit.py encode`

The web tool can extract secrets from QR codes created by the Python tool!

The web tool is perfect for:
- Demonstrating the concept
- Decoding QR codes (visible message)
- Comparing QR codes visually
- CTF challenge distribution
- Educational purposes

### Why JavaScript Can't Do Full Steganography

Full steganography requires:
1. Low-level QR code generation with bit-level control
2. Custom Reed-Solomon implementation for ECC manipulation
3. QR data/ECC byte deinterleaving
4. Padding byte extraction from raw codewords

These are complex operations that are better suited to Python with specialized libraries.

## Libraries Used

- **Tailwind CSS**: UI styling and dark mode
- **qrcode-generator**: QR code generation (Kazuhiko Arase's library)
- **jsQR**: QR code decoding (by cozmo)

All libraries are loaded from CDN for simplicity and fast deployment.

## Customization

### Colors

The dark mode theme uses these color variables (in `index.html`):

```javascript
colors: {
    dark: {
        bg: '#0f172a',        // Background
        surface: '#1e293b',    // Card backgrounds
        elevated: '#334155',   // Elevated elements
        border: '#475569',     // Borders
        text: '#e2e8f0',      // Text
        muted: '#94a3b8',     // Muted text
    },
    accent: {
        primary: '#3b82f6',    // Blue
        secondary: '#8b5cf6',  // Purple
        success: '#10b981',    // Green
        warning: '#f59e0b',    // Orange
        danger: '#ef4444',     // Red
    }
}
```

### Repository Link

Update the GitHub link in `index.html` (line ~57):

```html
<a href="https://github.com/yourusername/qr_ec_stego" target="_blank">
```

## File Structure

```
docs/
├── index.html           # Main HTML file
├── README.md           # This file
├── js/
│   ├── app.js          # Main application logic
│   ├── qr-encoder.js   # QR code generation
│   ├── qr-decoder.js   # QR code decoding
│   └── stego.js        # Steganography core module
└── examples/
    ├── challenge1.png  # Example QR with padding secret
    └── challenge2.png  # Example QR with ECC secret
```

## Browser Compatibility

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support (iOS 12+)
- Mobile browsers: ✅ Responsive design

## License

Same as parent project.
