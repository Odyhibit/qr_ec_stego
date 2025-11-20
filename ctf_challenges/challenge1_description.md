# Challenge 1: Hidden Messages (Easy/Medium)

**Points:** 100
**Category:** Steganography
**Author:** CTF Organizer

## Description

We intercepted this QR code during a routine security scan. It looks normal and scans correctly, but our analysts suspect there's more to it than meets the eye.

QR codes need to be padded to a specific length. What if someone hid data in those padding bytes?

**Flag format:** `flag{...}`

## Files
- `challenge1_qr.png` - The suspicious QR code

## Hints

<details>
<summary>Hint 1 (Free)</summary>
QR codes use padding bytes (0xEC and 0x11) to fill unused space. These bytes don't affect the visible message.
</details>

<details>
<summary>Hint 2 (25 points)</summary>
You'll need to extract the raw data codewords from the QR modules. The padding comes after the actual message data.
</details>

<details>
<summary>Hint 3 (50 points)</summary>
QR data is stored in an interleaved format. You'll need to deinterleave before you can see the padding bytes clearly.
</details>

## Resources
- [QR Code Structure Tutorial](https://www.thonky.com/qr-code-tutorial/)
- Python libraries: `pyzbar`, `PIL`, `qrcodegen`
