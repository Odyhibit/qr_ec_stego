# Update: Full Steganography Extraction Now Working!

## ✅ What's New

The web tool now has **full steganography extraction capabilities**! It can actually extract hidden messages from both padding and ECC bytes.

### New Functionality

1. **QR Structure Parser** (`qr-parser.js`)
   - Parses QR code module grid from images
   - Reads format information (ECC level, mask)
   - Extracts raw data bits following QR zigzag pattern
   - Unm asks data using detected mask pattern
   - Deinterleaves data and ECC codewords

2. **Padding Secret Extraction**
   - Calculates exact padding byte offset based on:
     - Mode bits (4 bits)
     - Character count bits (8 bits for version ≤9)
     - Decoy message length
     - Terminator bits
   - Reads length-prefixed secret from padding region
   - **Works with CTF Challenge 1**

3. **ECC Secret Extraction**
   - Extracts ECC codewords from QR structure
   - Deinterleaves across blocks
   - Reads k bytes per block
   - Combines into length-prefixed message
   - **Works with CTF Challenge 2**

## Testing

The web tool now successfully extracts:

**Challenge 1** (Padding):
- Visible: "SCAN ME!"
- Hidden: `flag{h1dd3n_1n_th3_p4dd1ng_byt3s}`

**Challenge 2** (Both Padding and ECC):
- Visible: "SCAN ME!"
- Padding: `flag{h1dd3n_1n_th3_p4dd1ng_byt3s}`
- ECC: `flag{3cc_bits_c0mpr0m1s3d}`

## How to Test

1. Start local server:
   ```bash
   cd docs
   python3 -m http.server 8000
   ```

2. Open http://localhost:8000

3. Go to "Decode" tab

4. Click "Try an example" → "Challenge 1" or "Challenge 2"

5. Click "Decode QR Code"

6. See the extracted secrets! 🎉

## Technical Implementation

### QR Parsing Process

1. **Module Detection**
   - Finds QR boundaries in image
   - Samples module grid at calculated positions
   - Converts to boolean matrix (black/white)

2. **Format Reading**
   - Reads format bits from specific locations
   - Decodes ECC level and mask pattern
   - Uses for data extraction

3. **Data Extraction**
   - Follows QR zigzag reading pattern
   - Skips function patterns (finders, timing, etc.)
   - Applies mask formula to unmask data
   - Converts bits to bytes (codewords)

4. **Deinterleaving**
   - Separates interleaved codewords
   - Distributes across blocks
   - Concatenates blocks in order

5. **Secret Extraction**
   - **Padding**: Calculates offset, reads length prefix, extracts message
   - **ECC**: Extracts k bytes per block, reads length prefix, extracts message

## Limitations

### What Works

✅ QR versions 5-7 (can be extended)
✅ ECC level H (most common for steganography)
✅ Mask patterns 0-7
✅ Padding extraction
✅ ECC extraction with configurable k-per-block
✅ UTF-8 text secrets

### Current Limitations

- Version detection is simplified (assumes clean QR image)
- Format information decoding is simplified
- Deinterleaving doesn't handle the padding byte skip (works for most cases)
- Only supports byte mode messages
- Requires relatively clean, high-contrast images

### Compared to Python Tool

The JavaScript implementation:
- ✅ **Can extract secrets** from properly formatted QR codes
- ✅ **Works with CTF challenges**
- ⚠️ May be less robust with damaged/low-quality images
- ⚠️ Doesn't validate Reed-Solomon ECC codes
- ⚠️ Simplified format/version detection

For **encoding** steganography, still use the Python tool.

## Browser Console

The tool logs helpful debugging information to the browser console:
- Parsed QR structure
- Extraction attempts
- Any errors encountered

Open DevTools (F12) → Console to see detailed logs.

## Files Changed

- `docs/js/qr-parser.js` - **NEW**: Full QR structure parser
- `docs/js/stego.js` - Updated to use QR parser
- `docs/index.html` - Added qr-parser.js script

## Next Steps

Optional enhancements:
1. Support more QR versions (1-40)
2. Handle short/long block differences in deinterleaving
3. Add Reed-Solomon validation
4. Better error handling for damaged QR codes
5. Support other QR modes (numeric, alphanumeric)

---

**Bottom Line**: The web tool now actually works for steganography extraction! Test it with the built-in examples. 🚀
