#!/usr/bin/env python3
"""
Solution for Challenge 1: Hidden Messages

This script extracts the hidden message from the padding bytes of a QR code.
"""

import sys
sys.path.insert(0, '..')

from padding_ecc_stego_v3_8bit import auto_decode

def solve_challenge1():
    print("=" * 60)
    print("Challenge 1 Solution: Padding Steganography")
    print("=" * 60)
    print()

    # Decode the QR code
    print("Extracting hidden message from padding bytes...")
    print()
    auto_decode("challenge1_qr.png", extract_ecc=False)

    print()
    print("=" * 60)
    print("Solution complete!")
    print("=" * 60)

if __name__ == "__main__":
    solve_challenge1()
