#!/usr/bin/env python3
"""
padding_stego_8bit_v3.py
------------------------
- Embed an 8-bit secret in the **padding** of a QR (Byte mode).
- Optionally embed another secret in **ECC bytes** (k bytes per block).
- Supports versions 1..40, ECC L/M/Q/H, masks 0..7.
- Decode auto-detects version/ECC/mask; no secret length required.
- **Capacity planner** reports whether a given decoy/secret fits and suggests the
  smallest (version, ECC) that satisfies:
    • pad_secret_bytes + overhead_bytes fits in padding, and
    • ecc_secret_bytes fits in k_per_block * num_blocks (with k_per_block ≤ t = floor(ECC_per_block/2)).
"""
import argparse
from typing import List, Tuple, Optional
from PIL import Image
from pyzbar.pyzbar import decode as zbar_decode
from qrcodegen import QrCode


# ----------------------------- Utilities ---------------------------------

def pack_bits_to_bytes(bits: List[int]) -> bytearray:
    out = bytearray((len(bits) + 7) // 8)
    for i, b in enumerate(bits):
        out[i >> 3] |= (b & 1) << (7 - (i & 7))
    return out


def detect_scale_and_version(img: Image.Image, border_guess: int = 4) -> Tuple[int, int, int]:
    W, H = img.size
    if W != H:
        raise ValueError("Image is not square")
    candidates = []
    for scale in range(1, 201):
        if W % scale != 0:
            continue
        modules_total = W // scale
        size = modules_total - 2 * border_guess
        if 21 <= size <= 177 and (size - 17) % 4 == 0:
            version = (size - 17) // 4
            candidates.append((scale, modules_total, version))
    if not candidates:
        raise ValueError("Could not infer module scale/version. Try specifying --border.")
    scale, modules_total, version = max(candidates, key=lambda t: t[0])
    return scale, modules_total, version


def load_module_matrix(path: str, version: int, border: int = 4) -> List[List[bool]]:
    img = Image.open(path).convert("L")
    W, _ = img.size
    size = version * 4 + 17
    total = size + 2 * border
    scale = W // total
    off = border * scale
    mid = scale // 2
    M = [[False] * size for _ in range(size)]
    for y in range(size):
        for x in range(size):
            px = off + x * scale + mid
            py = off + y * scale + mid
            M[y][x] = img.getpixel((px, py)) < 128
    # show_boolean_matrix(M)
    return M


def make_function_map(version):
    n = version * 4 + 17  # e.g., 33 for v4
    F = [[False] * n for _ in range(n)]

    # --- Finder + full 1-pixel separators ---
    def mark_finder(x0, y0):
        for dy in range(7):
            for dx in range(7):
                F[y0 + dy][x0 + dx] = True
        for dy in range(-1, 8):
            for dx in range(-1, 8):
                if dy in (-1, 7) or dx in (-1, 7):  # separator border
                    yy, xx = y0 + dy, x0 + dx
                    if 0 <= yy < n and 0 <= xx < n:
                        F[yy][xx] = True

    mark_finder(0, 0)
    mark_finder(n - 7, 0)
    mark_finder(0, n - 7)

    # --- Timing patterns ---
    for i in range(8, n - 8):
        F[6][i] = True
        F[i][6] = True

    # --- Alignment patterns ---
    # For version 4 the nominal center list is [6, 26]
    align_centers = alignment_centers(version)
    for cy in align_centers:
        for cx in align_centers:
            # Skip those overlapping the finder/separator areas:
            if (cx, cy) in [(6, 6), (6, n - 7), (n - 7, 6)]:
                continue
            # Mark 5x5 alignment pattern centered at (cx, cy)
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    yy, xx = cy + dy, cx + dx
                    if 0 <= yy < n and 0 <= xx < n:
                        F[yy][xx] = True

    # --- Format information areas ---
    for i in range(8):
        F[8][i] = True
        F[i][8] = True
        F[8][n - 1 - i] = True
        F[n - 1 - i][8] = True
    F[8][8] = True  # format info module

    # --- Dark module ---
    F[n - 8][8] = True
    # show_boolean_matrix(F)

    return F


def show_boolean_matrix(matrix):
    for i, outer in enumerate(matrix):
        print()
        for inner in matrix[i]:
            if inner:
                print("█", end="")
            else:
                print(" ", end="")
    print()


def mask_formula(mask_id: int, x: int, y: int) -> bool:
    if mask_id == 0:   return (x + y) % 2 == 0
    if mask_id == 1:   return y % 2 == 0
    if mask_id == 2:   return x % 3 == 0
    if mask_id == 3:   return (x + y) % 3 == 0
    if mask_id == 4:   return ((y // 2) + (x // 3)) % 2 == 0
    if mask_id == 5:   return ((x * y) % 2 + (x * y) % 3) == 0
    if mask_id == 6:   return (((x * y) % 2) + ((x * y) % 3)) % 2 == 0
    if mask_id == 7:   return (((x + y) % 2) + ((x * y) % 3)) % 2 == 0
    return False


def zigzag_coords(version: int, F: List[List[bool]]):
    n = version * 4 + 17
    coords = []
    up = True
    x = n - 1
    y = n - 1
    while x > 0:
        if x == 6:
            x -= 1
        for _ in range(n):
            for dx in (0, 1):
                xx = x - dx
                if not F[y][xx]:
                    coords.append((y, xx))
            y += -1 if up else 1
            if y < 0 or y >= n:
                up = not up
                y += 1 if not up else -1
                break
        x -= 2
    # print("Zigzag coords:", len(coords), "version count", QrCode._get_num_raw_data_modules(version))
    # print(coords[:10])
    return coords


def extract_interleaved_bits(M, version, ecc, mask_id: int) -> List[int]:
    n = version * 4 + 17
    F = make_function_map(version)
    dem = [[M[y][x] ^ mask_formula(mask_id, x, y) for x in range(n)] for y in range(n)]
    total_bits = QrCode._get_num_data_codewords(version, ecc) * 8
    coords = zigzag_coords(version, F)
    # print(f"total bits{QrCode._get_num_data_codewords(version,ecc)*8}")
    return [1 if dem[y][x] else 0 for (y, x) in coords[:total_bits]]


def deinterleave_data(interleaved_bytes: bytes, version: int, ecc) -> bytearray:
    """
    Deinterleave data codewords that were interleaved by qrcodegen.

    Note: qrcodegen adds a padding byte (0x00) to short blocks during ECC calculation,
    but skips this byte during interleaving. We need to account for this.
    """
    D = QrCode._get_num_data_codewords(version, ecc)
    B = QrCode._NUM_ERROR_CORRECTION_BLOCKS[ecc.ordinal][version]
    blockecclen = QrCode._ECC_CODEWORDS_PER_BLOCK[ecc.ordinal][version]
    rawcodewords = QrCode._get_num_raw_data_modules(version) // 8
    numshortblocks = B - rawcodewords % B
    shortblocklen = rawcodewords // B

    # Calculate data length for each block (before ECC)
    data_lens = []
    for i in range(B):
        if i < numshortblocks:
            # Short block
            data_lens.append(shortblocklen - blockecclen)
        else:
            # Long block
            data_lens.append(shortblocklen - blockecclen + 1)

    # Deinterleave - need to handle the skipped padding byte
    blocks = [bytearray() for _ in range(B)]
    pos = 0

    # The interleaving in qrcodegen skips position (shortblocklen - blockecclen) for short blocks
    skip_pos = shortblocklen - blockecclen

    max_block_data_len = max(data_lens)
    for i in range(max_block_data_len):
        for j in range(B):
            if i < data_lens[j]:
                # Check if this is the padding byte position that was skipped
                if i == skip_pos and j < numshortblocks:
                    # This byte was not in the interleaved stream, it was skipped
                    # qrcodegen added 0x00 here, but we don't need it in our data
                    pass
                else:
                    blocks[j].append(interleaved_bytes[pos])
                    pos += 1

    return bytearray().join(blocks)


def byte_mode_char_count_bits(version: int) -> int:
    return 8 if version <= 9 else 16


def read_header_mode_and_count(data_bytes: bytes, version: int) -> Tuple[int, int]:
    bits = []
    for i in range(min(20, len(data_bytes) * 8)):
        bits.append((data_bytes[i >> 3] >> (7 - (i & 7))) & 1)
    mode = 0
    for i in range(4):
        mode = (mode << 1) | bits[i]
    cc_bits = byte_mode_char_count_bits(version)
    count = 0
    for i in range(4, 4 + cc_bits):
        count = (count << 1) | bits[i]
    return mode, count


def alignment_centers(version: int):
    # Returns the list of center coordinates for alignment patterns (spec-compliant).
    if version == 1:
        return []
    first = 6
    last = 4 * version + 10  # = size-7 where size = 4*version + 17
    num = version // 7 + 2
    if num == 2:
        return [first, last]
    step = (last - first) // (num - 1)
    return [first + i * step for i in range(num)]


# --------------------------- Capacity planner ----------------------------

ECC_LEVELS = [("L", QrCode.Ecc.LOW), ("M", QrCode.Ecc.MEDIUM),
              ("Q", QrCode.Ecc.QUARTILE), ("H", QrCode.Ecc.HIGH)]


def qr_capacity(decoy_len: int, version: int, ecc, overhead_bytes: int = 2) -> Tuple[int, int, int, int]:
    data_cw = QrCode._get_num_data_codewords(version, ecc)
    capacity_bits = data_cw * 8
    used = 4 + byte_mode_char_count_bits(version) + 8 * decoy_len
    term = min(4, capacity_bits - used)
    after_term = used + term
    pad_start = after_term + ((-after_term) % 8)
    pad_bytes_capacity = (capacity_bits - pad_start) // 8

    raw_modules = QrCode._get_num_raw_data_modules(version)
    total_codewords = raw_modules // 8
    total_ecc_bytes = total_codewords - data_cw
    blocks = QrCode._NUM_ERROR_CORRECTION_BLOCKS[ecc.ordinal][version]
    ecc_per_block = total_ecc_bytes // blocks

    return pad_bytes_capacity, blocks, ecc_per_block, total_ecc_bytes


def plan_min_settings(decoy_len: int, pad_secret_len: int, ecc_secret_len: int,
                      overhead_bytes: int = 2, k_per_block: Optional[int] = None,
                      safety_margin: int = 2) -> Optional[Tuple[int, str, dict]]:
    for version in range(1, 41):
        for name, ecc in ECC_LEVELS:
            pad_bytes_capacity, blocks, ecc_per_block, total_ecc = qr_capacity(decoy_len, version, ecc, overhead_bytes)
            need_pad = pad_secret_len + overhead_bytes
            fits_pad = pad_bytes_capacity >= need_pad

            t = ecc_per_block // 2
            use_per_block = (t - safety_margin) if k_per_block is None else k_per_block
            if use_per_block > t:
                fits_ecc = False
            else:
                fits_ecc = (use_per_block * blocks) >= ecc_secret_len

            if fits_pad and fits_ecc:
                details = dict(pad_capacity=pad_bytes_capacity,
                               blocks=blocks,
                               ecc_per_block=ecc_per_block,
                               ecc_total=total_ecc,
                               t=t,
                               use_per_block=use_per_block,
                               ecc_capacity=use_per_block * blocks)
                return version, name, details
    return None


# ------------------------------- ENCODE ----------------------------------

def build_datacodewords(decoy: bytes, version: int, ecc, secret_bytes: bytes = b"") -> bytearray:
    """Build QR data codewords with decoy message and optional secret in padding."""
    data_cw = QrCode._get_num_data_codewords(version, ecc)
    capacity_bits = data_cw * 8

    bits = []
    bits += [0, 1, 0, 0]  # Byte mode
    cc_bits = byte_mode_char_count_bits(version)
    count = len(decoy)
    for i in range(cc_bits):
        bits.append((count >> (cc_bits - 1 - i)) & 1)
    for b in decoy:
        for i in range(8):
            bits.append((b >> (7 - i)) & 1)

    term = min(4, capacity_bits - len(bits))
    bits += [0] * term
    while len(bits) % 8 != 0:
        bits.append(0)

    # Calculate padding start
    pad_start = len(bits)

    # If we have a secret, embed it in padding with 2-byte length prefix
    if secret_bytes:
        secret_len = len(secret_bytes)
        length_prefix = bytes([secret_len >> 8, secret_len & 0xFF])
        full_secret = length_prefix + secret_bytes

        # Add secret bytes
        for byte in full_secret:
            for i in range(8):
                bits.append((byte >> (7 - i)) & 1)

    # Fill rest with standard padding
    pad_seq = [0xEC, 0x11]
    pi = 0
    while len(bits) + 8 <= capacity_bits:
        byte = pad_seq[pi % 2]
        for i in range(8):
            bits.append((byte >> (7 - i)) & 1)
        pi += 1

    return pack_bits_to_bytes(bits[:capacity_bits])


def embed_padding_secret(qr: QrCode, decoy_len: int, secret_bytes: bytes) -> QrCode:
    """Embed secret into padding bytes by modifying QR code modules directly."""
    version = qr._version
    ecc = qr._errcorlvl
    mask = qr._mask

    # Calculate where padding starts
    data_cw = QrCode._get_num_data_codewords(version, ecc)
    capacity_bits = data_cw * 8
    cc_bits = byte_mode_char_count_bits(version)
    used = 4 + cc_bits + 8 * decoy_len
    term = min(4, capacity_bits - used)
    after_term = used + term
    pad_start = after_term + ((-after_term) % 8)

    # Check capacity
    pad_capacity_bits = capacity_bits - pad_start
    if (len(secret_bytes) + 2) * 8 > pad_capacity_bits:
        raise ValueError(f"Secret too long for pad capacity: need {len(secret_bytes) + 2} bytes, have {pad_capacity_bits // 8}")

    # Extract data codewords from QR code modules
    n = version * 4 + 17
    F = make_function_map(version)
    coords = zigzag_coords(version, F)

    # Read bits from modules (unmask them first)
    bits = []
    for y, x in coords[:capacity_bits]:
        # Unmask the module to get the raw bit
        bit = qr._modules[y][x] ^ mask_formula(mask, x, y)
        bits.append(1 if bit else 0)

    # Convert to bytes
    data_bytes = bytearray(pack_bits_to_bytes(bits))

    # Prepare secret with 2-byte length prefix
    secret_len = len(secret_bytes)
    length_prefix = bytes([secret_len >> 8, secret_len & 0xFF])
    full_secret = length_prefix + secret_bytes

    # Overwrite padding area with secret
    for i, sb in enumerate(full_secret):
        byte_idx = (pad_start // 8) + i
        if byte_idx < len(data_bytes):
            data_bytes[byte_idx] = sb

    # Convert back to bits
    new_bits = []
    for byte in data_bytes:
        for i in range(8):
            new_bits.append((byte >> (7 - i)) & 1)

    # Write bits back to modules (with masking)
    # Copy the original modules
    new_modules = [row[:] for row in qr._modules]
    for idx, (y, x) in enumerate(coords[:capacity_bits]):
        if idx < len(new_bits):
            # Apply mask to get the final module value
            new_modules[y][x] = bool(new_bits[idx] ^ mask_formula(mask, x, y))

    # Create a shallow copy of the QR code and replace its modules
    # We don't want to call QrCode constructor because it will regenerate everything
    import copy
    new_qr = copy.copy(qr)
    new_qr._modules = new_modules

    return new_qr


def embed_ecc_secret(qr: QrCode, secret_bytes: bytes, k_per_block: int,
                     num_blocks: int, ecc_per_block: int) -> QrCode:
    """Embed secret into ECC bytes by modifying QR code modules directly."""
    version = qr._version
    ecc = qr._errcorlvl
    mask = qr._mask

    # Extract all codewords from the QR code modules
    n = version * 4 + 17
    F = make_function_map(version)
    coords = zigzag_coords(version, F)

    # Read bits from modules (unmask them first)
    raw_modules = QrCode._get_num_raw_data_modules(version)
    total_codewords = raw_modules // 8

    bits = []
    for y, x in coords[:total_codewords * 8]:
        # Unmask the module to get the raw bit
        bit = qr._modules[y][x] ^ mask_formula(mask, x, y)
        bits.append(1 if bit else 0)

    # Convert to bytes
    all_cw = bytearray(pack_bits_to_bytes(bits))

    # Deinterleave to get ECC blocks
    D = QrCode._get_num_data_codewords(version, ecc)
    B = num_blocks
    small = D // B
    large = small + 1
    num_large = D % B

    # Skip data codewords, extract and modify ECC codewords
    ecc_blocks = [bytearray() for _ in range(B)]
    pos = D
    for i in range(ecc_per_block):
        for j in range(B):
            if pos < len(all_cw):
                ecc_blocks[j].append(all_cw[pos])
                pos += 1

    # Prepare secret with 2-byte length prefix
    secret_len = len(secret_bytes)
    length_prefix = bytes([secret_len >> 8, secret_len & 0xFF])
    full_secret = length_prefix + secret_bytes

    # Distribute secret across ECC blocks (overwrite first k bytes of each block)
    secret_idx = 0
    for block_idx in range(B):
        for byte_idx in range(k_per_block):
            if secret_idx < len(full_secret) and byte_idx < len(ecc_blocks[block_idx]):
                ecc_blocks[block_idx][byte_idx] = full_secret[secret_idx]
                secret_idx += 1

    # Reinterleave ECC blocks back into all_cw
    pos = D
    for i in range(ecc_per_block):
        for j in range(B):
            if i < len(ecc_blocks[j]):
                all_cw[pos] = ecc_blocks[j][i]
                pos += 1

    # Convert back to bits
    new_bits = []
    for byte in all_cw:
        for i in range(8):
            new_bits.append((byte >> (7 - i)) & 1)

    # Write bits back to modules (with masking)
    # Copy the original modules
    new_modules = [row[:] for row in qr._modules]
    for idx, (y, x) in enumerate(coords[:total_codewords * 8]):
        if idx < len(new_bits):
            # Apply mask to get the final module value
            new_modules[y][x] = bool(new_bits[idx] ^ mask_formula(mask, x, y))

    # Create a shallow copy of the QR code and replace its modules
    # We don't want to call QrCode constructor because it will regenerate everything
    import copy
    new_qr = copy.copy(qr)
    new_qr._modules = new_modules

    return new_qr


def create_stego_qr(decoy: str, secret: str, version: int = 4,
                    ecc_level: str = "H", mask: int = 0, out_path="qr_stego.png",
                    check_only: bool = False, ecc_secret: str = "", k_per_block: Optional[int] = None,
                    safety_margin: int = 2):
    ecc_map = {"L": QrCode.Ecc.LOW, "M": QrCode.Ecc.MEDIUM, "Q": QrCode.Ecc.QUARTILE, "H": QrCode.Ecc.HIGH}
    ecc = ecc_map[ecc_level.upper()]

    pad_bytes_capacity, blocks, ecc_per_block, total_ecc = qr_capacity(len(decoy), version, ecc)
    need_pad = len(secret.encode("utf-8")) + 2
    if need_pad > pad_bytes_capacity:
        print(
            f"Not enough pad capacity on {version}-{ecc_level}. Need {need_pad} bytes (incl. 2B overhead), have {pad_bytes_capacity}.")
        return

    # Check ECC secret capacity
    ecc_secret_bytes = ecc_secret.encode("utf-8") if ecc_secret else b""
    t = ecc_per_block // 2
    use_per_block = (t - safety_margin) if k_per_block is None else k_per_block
    ecc_capacity = use_per_block * blocks

    if ecc_secret_bytes and use_per_block > t:
        print(f"k_per_block={use_per_block} exceeds t={t}, QR may not scan correctly")
        return

    if len(ecc_secret_bytes) + 2 > ecc_capacity:
        print(f"Not enough ECC capacity. Need {len(ecc_secret_bytes) + 2} bytes (incl. 2B overhead), have {ecc_capacity}.")
        return

    if check_only:
        print(
            f"{version}-{ecc_level} OK for padding secret ({need_pad} ≤ {pad_bytes_capacity}). ECC: {blocks} blocks × {ecc_per_block} bytes.")
        if ecc_secret_bytes:
            print(f"ECC stego capacity: {ecc_capacity} bytes (using {use_per_block} bytes per block, t={t})")
        return

    # Create QR code with decoy message and padding secret embedded
    secret_bytes = secret.encode("utf-8")
    datacw = build_datacodewords(decoy.encode("utf-8"), version, ecc, secret_bytes)
    qr = QrCode(version, ecc, datacw, mask)

    # Apply ECC steganography if requested
    # Note: This will break the QR code's ability to scan correctly
    if ecc_secret_bytes:
        qr = embed_ecc_secret(qr, ecc_secret_bytes, use_per_block, blocks, ecc_per_block)

    size = qr.get_size()
    border = 4
    scale = 8
    img = Image.new("1", ((size + border * 2) * scale, (size + border * 2) * scale), "white")
    for y in range(size):
        for x in range(size):
            if qr.get_module(x, y):
                for dy in range(scale):
                    for dx in range(scale):
                        img.putpixel(((x + border) * scale + dx, (y + border) * scale + dy), 0)
    img.save(out_path)
    msg = f"Saved stego QR -> {out_path} [{version}-{ecc_level}, mask={mask}]"
    if ecc_secret_bytes:
        msg += f" + ECC stego ({len(ecc_secret_bytes)} bytes)"
    print(msg)


# ------------------------------- DECODE ----------------------------------

def scan_decoy_text(path: str) -> str:
    res = zbar_decode(Image.open(path))
    return res[0].data.decode("utf-8", errors="replace") if res else ""


def extract_padding_secret(M, version: int, ecc, mask_id: int, decoy_len: int) -> Optional[bytes]:
    """Extract secret from padding bytes at module level."""
    # Extract interleaved data bits from modules
    n = version * 4 + 17
    F = make_function_map(version)
    dem = [[M[y][x] ^ mask_formula(mask_id, x, y) for x in range(n)] for y in range(n)]
    coords = zigzag_coords(version, F)

    # Extract data codeword bits (interleaved)
    data_cw = QrCode._get_num_data_codewords(version, ecc)
    capacity_bits = data_cw * 8
    data_bits_interleaved = [1 if dem[y][x] else 0 for (y, x) in coords[:capacity_bits]]
    data_bytes_interleaved = pack_bits_to_bytes(data_bits_interleaved)

    # Deinterleave to get original data codewords
    data_bytes = deinterleave_data(data_bytes_interleaved, version, ecc)

    # Calculate where padding starts
    cc_bits = byte_mode_char_count_bits(version)
    used = 4 + cc_bits + 8 * decoy_len
    term = min(4, capacity_bits - used)
    after_term = used + term
    pad_start = after_term + ((-after_term) % 8)

    pad_capacity_bits = capacity_bits - pad_start
    if pad_capacity_bits < 16:  # Need at least 2 bytes for length prefix
        return None

    # Extract padding bytes
    pad_byte_start = pad_start // 8
    pad_byte_count = pad_capacity_bits // 8

    # Read length prefix
    if pad_byte_start + 2 > len(data_bytes):
        return None

    secret_len = (data_bytes[pad_byte_start] << 8) | data_bytes[pad_byte_start + 1]

    # Validate length
    if secret_len == 0 or secret_len + 2 > pad_byte_count:
        return None

    # Extract secret
    secret_start = pad_byte_start + 2
    secret_end = secret_start + secret_len
    if secret_end > len(data_bytes):
        return None

    return bytes(data_bytes[secret_start:secret_end])


def extract_ecc_secret(M, version: int, ecc, mask_id: int, k_per_block: int) -> Optional[bytes]:
    """Extract secret from ECC bytes."""
    # Extract all bits including ECC
    raw_modules = QrCode._get_num_raw_data_modules(version)
    total_codewords = raw_modules // 8
    D = QrCode._get_num_data_codewords(version, ecc)

    n = version * 4 + 17
    F = make_function_map(version)
    dem = [[M[y][x] ^ mask_formula(mask_id, x, y) for x in range(n)] for y in range(n)]
    coords = zigzag_coords(version, F)

    # Extract all bits (data + ECC)
    all_bits = [1 if dem[y][x] else 0 for (y, x) in coords[:total_codewords * 8]]
    all_bytes = pack_bits_to_bytes(all_bits)

    # Deinterleave to get ECC blocks
    B = QrCode._NUM_ERROR_CORRECTION_BLOCKS[ecc.ordinal][version]
    small = D // B
    large = small + 1
    num_large = D % B
    data_lens = [large if j < num_large else small for j in range(B)]

    total_ecc_bytes = total_codewords - D
    ecc_per_block = total_ecc_bytes // B

    # Skip data bytes, extract ECC bytes
    pos = D
    ecc_blocks = [bytearray() for _ in range(B)]
    for i in range(ecc_per_block):
        for j in range(B):
            if pos < len(all_bytes):
                ecc_blocks[j].append(all_bytes[pos])
                pos += 1

    # Extract secret from first k_per_block bytes of each block
    secret_bytes = bytearray()
    for block_idx in range(B):
        for byte_idx in range(k_per_block):
            if byte_idx < len(ecc_blocks[block_idx]):
                secret_bytes.append(ecc_blocks[block_idx][byte_idx])

    # Read 2-byte length prefix
    if len(secret_bytes) < 2:
        return None

    secret_len = (secret_bytes[0] << 8) | secret_bytes[1]
    if secret_len + 2 > len(secret_bytes):
        return None

    return bytes(secret_bytes[2:2 + secret_len])


def auto_decode(path: str, border: int = 4, extract_ecc: bool = True,
                k_per_block: Optional[int] = None, safety_margin: int = 2) -> None:
    img = Image.open(path).convert("L")
    scale, modules_total, version = detect_scale_and_version(img, border_guess=border)
    size = version * 4 + 17
    print(f"Detected version={version}, size={size}, scale={scale}, border={border}")

    decoy = scan_decoy_text(path)
    if not decoy:
        print("Warning: pyzbar didn't decode a visible string. We'll still try to extract secrets.")
    else:
        print("Visible decoy:", decoy)

    M = load_module_matrix(path, version, border=border)

    # Try all combinations of ECC level and mask to find the correct one
    # Try in reverse order (H, Q, M, L) to prefer higher error correction
    ecc_levels = [("H", QrCode.Ecc.HIGH), ("Q", QrCode.Ecc.QUARTILE),
                  ("M", QrCode.Ecc.MEDIUM), ("L", QrCode.Ecc.LOW)]
    common_modes = [0, 1, 2, 4, 7, 8]

    candidates = []
    for ecl_name, ecc in ecc_levels:
        for mask_id in range(8):
            try:
                bits = extract_interleaved_bits(M, version, ecc, mask_id)
                inter_bytes = pack_bits_to_bytes(bits)
                data_bytes = deinterleave_data(inter_bytes, version, ecc)
                mode, count = read_header_mode_and_count(data_bytes, version)

                # Check if this is a valid decode
                if mode in common_modes:
                    # Score: exact decoy match is best, then prefer higher ECC
                    score = 0
                    if decoy and count == len(decoy):
                        score = 1000
                    score += ["L", "M", "Q", "H"].index(ecl_name)
                    candidates.append((score, ecl_name, ecc, mask_id, data_bytes, mode, count))
            except:
                continue

    best_match = None
    if candidates:
        # Sort by score (descending) and take the best
        candidates.sort(key=lambda x: x[0], reverse=True)
        _, ecl_name, ecc, mask_id, data_bytes, mode, count = candidates[0]
        best_match = (ecl_name, ecc, mask_id, data_bytes, mode, count)

    if not best_match:
        print("Failed to auto-detect ECC/mask. Trying ECC=H, mask=0 as fallback.")
        ecl_name = "H"
        ecc = QrCode.Ecc.HIGH
        mask_id = 0
        bits = extract_interleaved_bits(M, version, ecc, mask_id)
        inter_bytes = pack_bits_to_bytes(bits)
        data_bytes = deinterleave_data(inter_bytes, version, ecc)
        mode, count = read_header_mode_and_count(data_bytes, version)
    else:
        ecl_name, ecc, mask_id, data_bytes, mode, count = best_match

    print(f"Auto-detected ECC={ecl_name}, mask={mask_id}, mode={mode}, count={count}")

    # Extract padding secret
    try:
        padding_secret = extract_padding_secret(M, version, ecc, mask_id, count if count else 0)
        if padding_secret:
            try:
                secret_text = padding_secret.decode("utf-8")
                print("Recovered padding secret (utf-8):", secret_text)
            except UnicodeDecodeError:
                print("Recovered padding secret (hex):", padding_secret.hex())
                print("Recovered padding secret (latin1):", padding_secret.decode("latin1", errors="replace"))
        else:
            print("No padding secret found")
    except Exception as e:
        print(f"Failed to extract padding secret: {e}")

    # Extract ECC secret if requested
    if extract_ecc:
        _, blocks, ecc_per_block, _ = qr_capacity(count if count else 0, version, ecc)
        t = ecc_per_block // 2
        use_per_block = (t - safety_margin) if k_per_block is None else k_per_block

        try:
            ecc_secret = extract_ecc_secret(M, version, ecc, mask_id, use_per_block)
            if ecc_secret:
                try:
                    ecc_secret_text = ecc_secret.decode("utf-8")
                    print(f"Recovered ECC secret (utf-8, {use_per_block} bytes/block): {ecc_secret_text}")
                except UnicodeDecodeError:
                    print(f"Recovered ECC secret (hex, {use_per_block} bytes/block): {ecc_secret.hex()}")
                    print(f"Recovered ECC secret (latin1): {ecc_secret.decode('latin1', errors='replace')}")
            else:
                print("No ECC secret found (invalid length prefix)")
        except Exception as e:
            print(f"Failed to extract ECC secret: {e}")


# -------------------------------- CLI ------------------------------------

def main():
    import sys
    ap = argparse.ArgumentParser(description="QR padding+ECC stego (8-bit) with capacity planner")
    sub = ap.add_subparsers(dest="cmd")

    enc = sub.add_parser("encode")
    enc.add_argument("--decoy", required=True)
    enc.add_argument("--secret", required=True, help="Secret to hide in padding")
    enc.add_argument("--ecc-secret", default="", help="Second secret to hide in ECC bytes")
    enc.add_argument("--version", type=int, default=4, help="QR version (1..40)")
    enc.add_argument("--ecc", default="H", choices=["L", "M", "Q", "H"], help="Error correction level")
    enc.add_argument("--mask", type=int, default=0, choices=list(range(8)))
    enc.add_argument("--out", default="qr_stego.png")
    enc.add_argument("--check-only", action="store_true", help="Only check capacity, don't write image")
    enc.add_argument("--k-per-block", type=int, default=None,
                     help="ECC bytes to overwrite per block (default: t - safety)")
    enc.add_argument("--safety", type=int, default=2, help="Safety margin: use t - safety if k-per-block not set")

    dec = sub.add_parser("decode")
    dec.add_argument("image")
    dec.add_argument("--border", type=int, default=4)
    dec.add_argument("--no-ecc", action="store_true", help="Don't extract ECC secret")
    dec.add_argument("--k-per-block", type=int, default=None,
                     help="ECC bytes to extract per block (default: t - safety)")
    dec.add_argument("--safety", type=int, default=2, help="Safety margin: use t - safety if k-per-block not set")

    plan = sub.add_parser("plan")
    plan.add_argument("--decoy", required=True, help="Visible decoy string")
    plan.add_argument("--pad-secret-len", type=int, required=True, help="Secret bytes to hide in padding")
    plan.add_argument("--ecc-secret-len", type=int, required=True, help="Secret bytes to hide in ECC bytes")
    plan.add_argument("--overhead", type=int, default=2, help="Overhead bytes to reserve in padding")
    plan.add_argument("--k-per-block", type=int, default=None,
                      help="ECC bytes to overwrite per block (default: t - safety)")
    plan.add_argument("--safety", type=int, default=2, help="Safety margin: use t - safety if k-per-block not set")

    args = ap.parse_args()
    if args.cmd == "encode":
        create_stego_qr(args.decoy, args.secret, version=args.version, ecc_level=args.ecc,
                        mask=args.mask, out_path=args.out, check_only=args.check_only,
                        ecc_secret=args.ecc_secret, k_per_block=args.k_per_block,
                        safety_margin=args.safety)
    elif args.cmd == "decode":
        auto_decode(args.image, border=args.border, extract_ecc=not args.no_ecc,
                    k_per_block=args.k_per_block, safety_margin=args.safety)
    elif args.cmd == "plan":
        res = plan_min_settings(decoy_len=len(args.decoy),
                                pad_secret_len=args.pad_secret_len,
                                ecc_secret_len=args.ecc_secret_len,
                                overhead_bytes=args.overhead,
                                k_per_block=args.k_per_block,
                                safety_margin=args.safety)
        if res is None:
            print("No (version, ECC) up to 40-H fits both constraints with the chosen k-per-block / safety.")
            sys.exit(2)
        version, ecc_name, details = res
        print(f"Minimum setting: version {version}, ECC {ecc_name}")
        print(f"Pad capacity: {details['pad_capacity']} bytes (need {args.pad_secret_len + args.overhead})")
        print(f"ECC: {details['blocks']} blocks × {details['ecc_per_block']} ECC bytes (total {details['ecc_total']})")
        print(f"Per-block correction t={details['t']}; using {details['use_per_block']} per block "
              f"⇒ ECC stego capacity {details['ecc_capacity']} bytes (need {args.ecc_secret_len})")
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
