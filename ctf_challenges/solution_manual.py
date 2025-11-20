#!/usr/bin/env python3
"""
Manual Solution: Step-by-step extraction without using the auto_decode function.

This shows the full process of extracting secrets from both padding and ECC bytes.
"""

import sys
sys.path.insert(0, '..')

from PIL import Image
from qrcodegen import QrCode
from padding_ecc_stego_v3_8bit import (
    detect_scale_and_version,
    load_module_matrix,
    make_function_map,
    mask_formula,
    zigzag_coords,
    pack_bits_to_bytes,
    deinterleave_data,
    byte_mode_char_count_bits
)


def extract_padding_manual(image_path):
    """Manually extract padding secret from QR code."""
    print("=" * 70)
    print("MANUAL SOLUTION - CHALLENGE 1: Padding Secret Extraction")
    print("=" * 70)
    print()

    # Step 1: Load and analyze the QR code
    print("Step 1: Load QR code image")
    img = Image.open(image_path)
    scale, modules_total, version = detect_scale_and_version(img, border_guess=4)
    print(f"  Version: {version}")
    print(f"  Module size: {version * 4 + 17}")
    print(f"  Scale: {scale}")
    print()

    # Step 2: Extract module matrix
    print("Step 2: Extract module matrix (black/white pixels -> boolean grid)")
    M = load_module_matrix(image_path, version, border=4)
    print(f"  Module matrix: {len(M)}x{len(M[0])}")
    print()

    # Step 3: Try different ECC levels and masks
    print("Step 3: Determine ECC level and mask pattern")
    ecc = QrCode.Ecc.HIGH  # We'll assume H for this example
    mask_id = 0
    print(f"  Using ECC=H, mask={mask_id}")
    print()

    # Step 4: Extract data bits in zigzag order
    print("Step 4: Extract data bits from modules (zigzag pattern)")
    n = version * 4 + 17
    F = make_function_map(version)
    coords = zigzag_coords(version, F)

    # Get data capacity
    data_cw = QrCode._get_num_data_codewords(version, ecc)
    capacity_bits = data_cw * 8
    print(f"  Data capacity: {data_cw} bytes ({capacity_bits} bits)")

    # Extract and unmask
    dem = [[M[y][x] ^ mask_formula(mask_id, x, y) for x in range(n)] for y in range(n)]
    data_bits_interleaved = [1 if dem[y][x] else 0 for (y, x) in coords[:capacity_bits]]
    data_bytes_interleaved = pack_bits_to_bytes(data_bits_interleaved)
    print(f"  Extracted {len(data_bytes_interleaved)} interleaved bytes")
    print()

    # Step 5: Deinterleave
    print("Step 5: Deinterleave data blocks")
    data_bytes = deinterleave_data(data_bytes_interleaved, version, ecc)
    print(f"  Deinterleaved data: {data_bytes[:20].hex()}...")
    print()

    # Step 6: Parse QR header
    print("Step 6: Parse QR code header")
    # Read bits from the data
    bits = []
    for byte in data_bytes:
        for i in range(8):
            bits.append((byte >> (7 - i)) & 1)

    # Mode (4 bits)
    mode = 0
    for i in range(4):
        mode = (mode << 1) | bits[i]

    # Character count (8 or 16 bits depending on version)
    cc_bits = byte_mode_char_count_bits(version)
    count = 0
    for i in range(4, 4 + cc_bits):
        count = (count << 1) | bits[i]

    print(f"  Mode: {mode} (4 = Byte mode)")
    print(f"  Character count: {count}")
    print()

    # Step 7: Calculate padding start
    print("Step 7: Locate padding area")
    used = 4 + cc_bits + 8 * count
    term = min(4, capacity_bits - used)
    after_term = used + term
    pad_start = after_term + ((-after_term) % 8)
    pad_byte_start = pad_start // 8

    print(f"  Data + header: {used} bits")
    print(f"  Terminator: {term} bits")
    print(f"  Padding starts at: bit {pad_start} (byte {pad_byte_start})")
    print()

    # Step 8: Extract secret
    print("Step 8: Extract secret from padding")
    secret_len = (data_bytes[pad_byte_start] << 8) | data_bytes[pad_byte_start + 1]
    print(f"  Secret length (from header): {secret_len} bytes")

    secret_start = pad_byte_start + 2
    secret_bytes = data_bytes[secret_start:secret_start + secret_len]

    print(f"  Secret (hex): {secret_bytes.hex()}")
    print(f"  Secret (text): {secret_bytes.decode('utf-8')}")
    print()

    return secret_bytes.decode('utf-8')


def extract_ecc_manual(image_path, k_per_block=8):
    """Manually extract ECC secret from QR code."""
    print("=" * 70)
    print("MANUAL SOLUTION - CHALLENGE 2: ECC Secret Extraction")
    print("=" * 70)
    print()

    # Steps 1-3: Same as padding extraction
    print("Step 1-3: Load QR and determine parameters")
    img = Image.open(image_path)
    scale, modules_total, version = detect_scale_and_version(img, border_guess=4)
    M = load_module_matrix(image_path, version, border=4)
    ecc = QrCode.Ecc.HIGH
    mask_id = 0
    print(f"  Version: {version}, ECC: H, Mask: {mask_id}")
    print()

    # Step 4: Extract ALL bits (data + ECC)
    print("Step 4: Extract all codewords (data + ECC)")
    n = version * 4 + 17
    F = make_function_map(version)
    coords = zigzag_coords(version, F)

    raw_modules = QrCode._get_num_raw_data_modules(version)
    total_codewords = raw_modules // 8
    data_cw = QrCode._get_num_data_codewords(version, ecc)
    ecc_cw = total_codewords - data_cw

    print(f"  Total codewords: {total_codewords}")
    print(f"  Data codewords: {data_cw}")
    print(f"  ECC codewords: {ecc_cw}")

    dem = [[M[y][x] ^ mask_formula(mask_id, x, y) for x in range(n)] for y in range(n)]
    all_bits = [1 if dem[y][x] else 0 for (y, x) in coords[:total_codewords * 8]]
    all_bytes = pack_bits_to_bytes(all_bits)
    print()

    # Step 5: Extract ECC portion
    print("Step 5: Extract ECC blocks")
    B = QrCode._NUM_ERROR_CORRECTION_BLOCKS[ecc.ordinal][version]
    blockecclen = QrCode._ECC_CODEWORDS_PER_BLOCK[ecc.ordinal][version]

    print(f"  Number of blocks: {B}")
    print(f"  ECC bytes per block: {blockecclen}")
    print(f"  k_per_block (bytes with secret): {k_per_block}")
    print()

    # Extract interleaved ECC bytes (they come after data bytes)
    ecc_interleaved = all_bytes[data_cw:total_codewords]

    # Deinterleave ECC blocks
    ecc_blocks = [bytearray() for _ in range(B)]
    pos = 0
    for i in range(blockecclen):
        for j in range(B):
            if pos < len(ecc_interleaved):
                ecc_blocks[j].append(ecc_interleaved[pos])
                pos += 1

    print("Step 6: Collect first k bytes from each ECC block")
    secret_bytes = bytearray()
    for block_idx in range(B):
        block_contribution = ecc_blocks[block_idx][:k_per_block]
        secret_bytes.extend(block_contribution)
        print(f"  Block {block_idx}: {block_contribution.hex()}")

    print()

    # Step 7: Parse secret
    print("Step 7: Parse secret")
    secret_len = (secret_bytes[0] << 8) | secret_bytes[1]
    print(f"  Secret length (from header): {secret_len} bytes")

    secret = secret_bytes[2:2 + secret_len]
    print(f"  Secret (hex): {secret.hex()}")
    print(f"  Secret (text): {secret.decode('utf-8')}")
    print()

    return secret.decode('utf-8')


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("FULL MANUAL CTF SOLUTIONS")
    print("=" * 70 + "\n")

    # Solve Challenge 1
    flag1 = extract_padding_manual("challenge1_qr.png")

    print("\n" + "-" * 70 + "\n")

    # Solve Challenge 2
    flag2 = extract_ecc_manual("challenge2_qr.png", k_per_block=8)

    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    print(f"Challenge 1 Flag: {flag1}")
    print(f"Challenge 2 Flag: {flag2}")
    print("=" * 70 + "\n")
