# Challenge 2: Compromised Integrity (Hard)

**Points:** 300
**Category:** Steganography / Cryptanalysis
**Author:** CTF Organizer
**Prerequisites:** Challenge 1 (recommended)

## Description

After cracking the first QR code, we found another one that looks almost identical. Both QR codes scan to the same message ("SCAN ME!"), but something feels off...

Our forensics team noticed subtle pixel differences between the two images. Could someone be tampering with the error correction codes?

**Note:** This challenge is a sequel to Challenge 1. You may want to solve that one first.

**Flag format:** `flag{...}`

## Files
- `challenge2_qr.png` - The second suspicious QR code
- `challenge1_qr.png` - The first QR code (for reference)

## Hints

<details>
<summary>Hint 1 (Free)</summary>
Compare both QR codes pixel-by-pixel. Where are the differences located?
</details>

<details>
<summary>Hint 2 (50 points)</summary>
QR codes use Reed-Solomon error correction. The ECC bytes can detect and correct errors... but what if the "errors" aren't really errors?
</details>

<details>
<summary>Hint 3 (100 points)</summary>
The ECC bytes are stored separately from data bytes and are also interleaved across blocks. You'll need to extract and deinterleave the ECC portion specifically.
</details>

<details>
<summary>Hint 4 (150 points)</summary>
The secret is distributed across the first few bytes of EACH error correction block. Look for a 2-byte length prefix at the start.
</details>

## Technical Details

QR codes have this structure:
```
[Data Codewords (interleaved)] + [ECC Codewords (interleaved)]
```

The data section contains the visible message. The ECC section contains Reed-Solomon error correction codes that allow scanners to fix damaged QR codes.

## Resources
- [Reed-Solomon Error Correction](https://en.wikiversity.org/wiki/Reed%E2%80%93Solomon_codes_for_coders)
- [QR Code Error Correction Levels](https://www.qrcode.com/en/about/error_correction.html)
- Image diff tools: `ImageMagick compare`, `PIL.ImageChops`
