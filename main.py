#!/usr/bin/env python3
"""
Example usage of the QR steganography library.

This demonstrates how to create QR codes with hidden messages in both
padding bytes and ECC bytes, and how to extract them.
"""

from padding_ecc_stego_v3_8bit import (
    create_stego_qr,
    auto_decode,
    plan_min_settings
)


def example_padding_only():
    """Example: Hide a secret in padding only."""
    print("=" * 60)
    print("Example 1: Padding-only steganography")
    print("=" * 60)

    decoy = "Hello, World!"
    secret = "Hidden in pad"

    # Create QR code with padding secret (use version 5 for more capacity)
    create_stego_qr(
        decoy=decoy,
        secret=secret,
        version=5,
        ecc_level="H",
        mask=0,
        out_path="example_padding.png"
    )

    print("\nDecoding:")
    try:
        auto_decode("example_padding.png", extract_ecc=False)
    except FileNotFoundError:
        print("Failed to create QR code - check capacity requirements")
    print()


def example_padding_and_ecc():
    """Example: Hide secrets in both padding and ECC."""
    print("=" * 60)
    print("Example 2: Padding + ECC steganography")
    print("=" * 60)

    decoy = "Scan me!"
    padding_secret = "Pad secret"
    ecc_secret = "ECC secret"

    # Create QR code with both secrets
    create_stego_qr(
        decoy=decoy,
        secret=padding_secret,
        ecc_secret=ecc_secret,
        version=5,
        ecc_level="H",
        mask=0,
        out_path="example_dual.png"
    )

    print("\nDecoding:")
    try:
        auto_decode("example_dual.png", extract_ecc=True)
    except FileNotFoundError:
        print("Failed to create QR code - check capacity requirements")
    print()


def example_capacity_planning():
    """Example: Plan capacity for specific requirements."""
    print("=" * 60)
    print("Example 3: Capacity planning")
    print("=" * 60)

    decoy = "Public message"
    pad_secret_len = 30  # bytes
    ecc_secret_len = 20  # bytes

    result = plan_min_settings(
        decoy_len=len(decoy),
        pad_secret_len=pad_secret_len,
        ecc_secret_len=ecc_secret_len,
        overhead_bytes=2,
        safety_margin=2
    )

    if result:
        version, ecc_name, details = result
        print(f"Minimum setting: version {version}, ECC {ecc_name}")
        print(f"Pad capacity: {details['pad_capacity']} bytes (need {pad_secret_len + 2})")
        print(f"ECC: {details['blocks']} blocks × {details['ecc_per_block']} bytes")
        print(f"Per-block correction t={details['t']}; using {details['use_per_block']} per block")
        print(f"ECC stego capacity: {details['ecc_capacity']} bytes (need {ecc_secret_len})")
    else:
        print("No suitable configuration found!")
    print()


if __name__ == "__main__":
    # Run examples
    example_padding_only()
    example_padding_and_ecc()
    example_capacity_planning()

    print("=" * 60)
    print("All examples completed!")
    print("Check the generated PNG files to see the QR codes.")
    print("=" * 60)