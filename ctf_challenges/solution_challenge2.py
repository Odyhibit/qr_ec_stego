#!/usr/bin/env python3
"""
Solution for Challenge 2: Compromised Integrity

This script extracts the hidden message from the ECC bytes of a QR code.
"""

import sys
sys.path.insert(0, '..')

from padding_ecc_stego_v3_8bit import auto_decode

def solve_challenge2():
    print("=" * 60)
    print("Challenge 2 Solution: ECC Steganography")
    print("=" * 60)
    print()

    # First, let's compare with challenge1 to see the differences
    print("Step 1: Comparing QR codes...")
    from PIL import Image, ImageChops

    img1 = Image.open("challenge1_qr.png")
    img2 = Image.open("challenge2_qr.png")

    diff = ImageChops.difference(img1, img2)
    diff.save("diff_analysis.png")

    # Count different pixels
    diff_pixels = sum(1 for p in diff.getdata() if p != 0)
    total_pixels = diff.size[0] * diff.size[1]

    print(f"  Different pixels: {diff_pixels} / {total_pixels}")
    print(f"  Percentage changed: {100*diff_pixels/total_pixels:.2f}%")
    print(f"  Saved diff to: diff_analysis.png")
    print()

    # Decode the QR code with ECC extraction
    print("Step 2: Extracting hidden message from ECC bytes...")
    print()

    # We need to specify k_per_block=8 (same as encoding)
    auto_decode("challenge2_qr.png", extract_ecc=True, k_per_block=8)

    print()
    print("=" * 60)
    print("Solution complete!")
    print("=" * 60)

if __name__ == "__main__":
    solve_challenge2()
