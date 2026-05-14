#!/usr/bin/env python3
"""
padding_stego_8bit_v3.py
------------------------
- Embed an 8-bit secret in the **padding** of a QR (Byte mode).
- Optionally embed another secret in **ECC bytes** via Gauss-Jordan elimination.
- Supports versions 1..40, ECC L/M/Q/H, masks 0..7.
- Decode auto-detects version/ECC/mask; no secret length required.
- Both padding and ECC secrets use a 1-byte length prefix for reliable extraction.
- GJ approach produces 100% valid QRs — ECC is legitimately recomputed from
  modified data bytes rather than being overwritten directly.
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


# ─────────────────────── Reed-Solomon (via qrcodegen) ─────────────────────────

_rs_divisor_cache: dict = {}


def _reed_solomon(data: list, nc: int) -> list:
    if nc not in _rs_divisor_cache:
        _rs_divisor_cache[nc] = QrCode._reed_solomon_compute_divisor(nc)
    return QrCode._reed_solomon_compute_remainder(data, _rs_divisor_cache[nc])


# ─────────────────────── Gauss-Jordan block solver ────────────────────────────

class GJBlock:
    """Port of the JS GJBlock / Python ecc_payload_stego GJBlock.
    Builds a constraint matrix where row i encodes how flipping data bit i
    propagates into the full codeword (data + ECC) via Reed-Solomon.
    Uses the same RS polynomial as qrcodegen so the solved data bytes produce
    the desired ECC when qrcodegen recomputes it.
    """

    def __init__(self, data: list, n_ecc: int):
        self.nd = len(data)
        self.nc = n_ecc
        self.b = list(data) + _reed_solomon(data, n_ecc)

        self._active = []
        for i in range(self.nd * 8):
            row = [0] * self.nd
            row[i >> 3] = 1 << (7 - (i & 7))
            self._active.append(row + _reed_solomon(row, n_ecc))
        self._used: list = []

    def _can_set(self, bit_in_data: int, value: int) -> bool:
        byte_idx = bit_in_data >> 3
        mask = 1 << (7 - (bit_in_data & 7))
        pi = next((j for j, r in enumerate(self._active) if r[byte_idx] & mask), -1)
        if pi == -1:
            return False
        if pi != 0:
            self._active[0], self._active[pi] = self._active[pi], self._active[0]
        targ = self._active[0]
        for j in range(1, len(self._active)):
            if self._active[j][byte_idx] & mask:
                for k in range(len(targ)):
                    self._active[j][k] ^= targ[k]
        for row in self._used:
            if row[byte_idx] & mask:
                for k in range(len(targ)):
                    row[k] ^= targ[k]
        if bool(self.b[byte_idx] & mask) != bool(value):
            for k in range(len(self.b)):
                self.b[k] ^= targ[k]
        self._used.append(targ)
        self._active.pop(0)
        return True

    def lock_bit(self, bit: int) -> None:
        self._can_set(bit, (self.b[bit >> 3] >> (7 - (bit & 7))) & 1)

    def set_ecc_bit(self, ecc_byte: int, bit_in_byte: int, value: int) -> bool:
        cw_idx = self.nd + ecc_byte
        mask = 1 << (7 - bit_in_byte)
        pi = next((j for j, r in enumerate(self._active) if r[cw_idx] & mask), -1)
        if pi == -1:
            return False
        if pi != 0:
            self._active[0], self._active[pi] = self._active[pi], self._active[0]
        targ = self._active[0]
        for j in range(1, len(self._active)):
            if self._active[j][cw_idx] & mask:
                for k in range(len(targ)):
                    self._active[j][k] ^= targ[k]
        for row in self._used:
            if row[cw_idx] & mask:
                for k in range(len(targ)):
                    row[k] ^= targ[k]
        if bool(self.b[cw_idx] & mask) != bool(value):
            for k in range(len(self.b)):
                self.b[k] ^= targ[k]
        self._used.append(targ)
        self._active.pop(0)
        return True

    @property
    def data_bytes(self) -> list:
        return self.b[:self.nd]


def _block_layout(version: int, ecc) -> Tuple[List[int], int]:
    """Returns (data_block_lens, ecc_per_block)."""
    D = QrCode._get_num_data_codewords(version, ecc)
    raw = QrCode._get_num_raw_data_modules(version) // 8
    B = QrCode._NUM_ERROR_CORRECTION_BLOCKS[ecc.ordinal][version]
    ecc_per_block = (raw - D) // B
    num_long = D % B
    num_short = B - num_long
    short_len = D // B
    return [short_len] * num_short + [short_len + 1] * num_long, ecc_per_block


def _pad_start_bits(decoy_len: int, version: int, ecc) -> int:
    D = QrCode._get_num_data_codewords(version, ecc)
    capacity_bits = D * 8
    cc_bits = byte_mode_char_count_bits(version)
    used = 4 + cc_bits + 8 * decoy_len
    term = min(4, capacity_bits - used)
    after_term = used + term
    return after_term + ((-after_term) % 8)


def calc_ecc_capacity(data_block_lens: List[int], lock_bytes: int, ecc_per_block: int) -> int:
    """GJ-accessible ECC bytes: each block contributes min(free_bytes, ecc_per_block)."""
    total = 0
    seq_offset = 0
    for blk_len in data_block_lens:
        lock_in_block = max(0, min(lock_bytes - seq_offset, blk_len))
        free_in_block = blk_len - lock_in_block
        total += min(free_in_block, ecc_per_block)
        seq_offset += blk_len
    return total


def embed_ecc_secret_gj(version: int, ecc, ecc_secret_bytes: bytes,
                         lock_bytes: int, data_codewords: bytearray) -> bytearray:
    """Modify data codewords so qrcodegen produces the desired ECC bytes.
    Uses Gauss-Jordan elimination — the QR remains 100% valid.
    Payload layout: [len(secret), secret_bytes] written sequentially starting
    from ECC byte 0 of block 0, matching the JS encoder exactly.
    """
    data_block_lens, ecc_per_block = _block_layout(version, ecc)

    if len(ecc_secret_bytes) > 255:
        raise ValueError("ECC secret too long for 1-byte length prefix (max 255 bytes).")
    ecc_payload = bytes([len(ecc_secret_bytes)]) + ecc_secret_bytes

    seq_offset = 0
    secret_offset = 0
    solved: list = []

    for blk_len in data_block_lens:
        blk_data = list(data_codewords[seq_offset: seq_offset + blk_len])
        lock_in_block = max(0, min(lock_bytes - seq_offset, blk_len))
        free_in_block = blk_len - lock_in_block
        block_ecc_bytes = min(free_in_block, ecc_per_block)
        payload_in_block = min(block_ecc_bytes, len(ecc_payload) - secret_offset)

        if payload_in_block > 0:
            gj = GJBlock(blk_data, ecc_per_block)
            for bit in range(lock_in_block * 8):
                gj.lock_bit(bit)
            failures = 0
            for byte_idx in range(payload_in_block):
                b = ecc_payload[secret_offset + byte_idx]
                for bit_idx in range(8):
                    if not gj.set_ecc_bit(byte_idx, bit_idx, (b >> (7 - bit_idx)) & 1):
                        failures += 1
            if failures:
                print(f"Warning: GJBlock: {failures} ECC bits could not be set")
            secret_offset += payload_in_block
            solved.extend(gj.data_bytes)
        else:
            solved.extend(blk_data)

        seq_offset += blk_len

    return bytearray(solved)


def extract_ecc_secret_gj(M: List[List[bool]], version: int, ecc, mask_id: int,
                           decoy_len: int) -> Optional[bytes]:
    """Extract ECC secret written by embed_ecc_secret_gj.

    Mirrors the encoder exactly: compute lock_bytes from the decoy header and any
    padding secret found in the data codewords, then collect only the driven ECC
    bytes (blockEccBytes = min(freeInBlock, eccPerBlock)) from each block in order.
    This correctly handles the case where block 0 is fully or partially locked.
    """
    raw = QrCode._get_num_raw_data_modules(version)
    total_cw = raw // 8
    D = QrCode._get_num_data_codewords(version, ecc)
    B = QrCode._NUM_ERROR_CORRECTION_BLOCKS[ecc.ordinal][version]
    ecc_per_block = (total_cw - D) // B

    n = version * 4 + 17
    F = make_function_map(version)
    dem = [[M[y][x] ^ mask_formula(mask_id, x, y) for x in range(n)] for y in range(n)]
    coords = zigzag_coords(version, F)

    all_bits = [1 if dem[y][x] else 0 for (y, x) in coords[:total_cw * 8]]
    all_bytes = bytearray(pack_bits_to_bytes(all_bits))

    # Read data codewords to detect padding secret length
    data_bits_interleaved = [1 if dem[y][x] else 0 for (y, x) in coords[:D * 8]]
    data_cw = deinterleave_data(bytearray(pack_bits_to_bytes(data_bits_interleaved)), version, ecc)

    pad_start = _pad_start_bits(decoy_len, version, ecc)
    pad_byte_start = pad_start // 8
    pad_bytes_capacity = (D * 8 - pad_start) // 8

    pad_secret_len = 0
    if pad_byte_start < len(data_cw):
        len_byte = data_cw[pad_byte_start]
        if len_byte not in (0xEC, 0x11) and 0 < len_byte <= pad_bytes_capacity - 1:
            pad_secret_len = len_byte

    lock_bytes = pad_byte_start + (1 + pad_secret_len if pad_secret_len > 0 else 0)

    # Deinterleave ECC into per-block arrays
    data_block_lens, _ = _block_layout(version, ecc)
    ecc_blocks = [bytearray() for _ in range(B)]
    pos = D
    for i in range(ecc_per_block):
        for j in range(B):
            if pos < len(all_bytes):
                ecc_blocks[j].append(all_bytes[pos])
                pos += 1

    # Collect only the driven ECC bytes from each block (same slice as encoder wrote)
    payload = bytearray()
    seq_offset = 0
    for blk_idx, blk_len in enumerate(data_block_lens):
        lock_in_block = max(0, min(lock_bytes - seq_offset, blk_len))
        free_in_block = blk_len - lock_in_block
        block_ecc_bytes = min(free_in_block, ecc_per_block)
        payload.extend(ecc_blocks[blk_idx][:block_ecc_bytes])
        seq_offset += blk_len

    if len(payload) < 1:
        return None
    secret_len = payload[0]
    if secret_len == 0 or 1 + secret_len > len(payload):
        return None
    candidate = bytes(payload[1: 1 + secret_len])
    try:
        candidate.decode('utf-8')
    except UnicodeDecodeError:
        return None
    if any(b < 0x20 and b not in (0x09, 0x0A, 0x0D) for b in candidate):
        return None
    return candidate


# --------------------------- Capacity planner ----------------------------

ECC_LEVELS = [("L", QrCode.Ecc.LOW), ("M", QrCode.Ecc.MEDIUM),
              ("Q", QrCode.Ecc.QUARTILE), ("H", QrCode.Ecc.HIGH)]


def qr_capacity(decoy_len: int, version: int, ecc, overhead_bytes: int = 1) -> Tuple[int, int, int, int]:
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
                      overhead_bytes: int = 1) -> Optional[Tuple[int, str, dict]]:
    for version in range(1, 41):
        for name, ecc in ECC_LEVELS:
            pad_bytes_capacity, blocks, ecc_per_block, total_ecc = qr_capacity(decoy_len, version, ecc, overhead_bytes)
            need_pad = pad_secret_len + overhead_bytes
            if pad_bytes_capacity < need_pad:
                continue

            data_block_lens, epb = _block_layout(version, ecc)
            pad_start = _pad_start_bits(decoy_len, version, ecc)
            lock_bytes = pad_start // 8 + (overhead_bytes + pad_secret_len if pad_secret_len else 0)
            ecc_cap = calc_ecc_capacity(data_block_lens, lock_bytes, epb)

            # +1 for length prefix byte
            if ecc_secret_len + 1 > ecc_cap:
                continue

            details = dict(pad_capacity=pad_bytes_capacity,
                           blocks=blocks,
                           ecc_per_block=ecc_per_block,
                           ecc_total=total_ecc,
                           ecc_capacity=ecc_cap)
            return version, name, details
    return None


# ------------------------------- ENCODE ----------------------------------

def build_datacodewords(decoy: bytes, version: int, ecc, secret_bytes: bytes = b"") -> bytearray:
    """Build QR data codewords with decoy message and optional secret in padding."""
    data_cw = QrCode._get_num_data_codewords(version, ecc)
    capacity_bits = data_cw * 8
    if len(secret_bytes) > 255:
        raise ValueError("Secret too long for 1-byte length prefix (max 255 bytes).")

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

    # If we have a secret, embed it in padding with 1-byte length prefix
    if secret_bytes:
        secret_len = len(secret_bytes)
        length_prefix = bytes([secret_len & 0xFF])
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
    if len(secret_bytes) > 255:
        raise ValueError("Secret too long for 1-byte length prefix (max 255 bytes).")

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
    if (len(secret_bytes) + 1) * 8 > pad_capacity_bits:
        raise ValueError(f"Secret too long for pad capacity: need {len(secret_bytes) + 1} bytes, have {pad_capacity_bits // 8}")

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

    # Prepare secret with 1-byte length prefix
    secret_len = len(secret_bytes)
    length_prefix = bytes([secret_len & 0xFF])
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




def create_stego_qr(decoy: str, secret: str, version: int = 4,
                    ecc_level: str = "H", mask: int = 0, out_path="qr_stego.png",
                    check_only: bool = False, ecc_secret: str = ""):
    ecc_map = {"L": QrCode.Ecc.LOW, "M": QrCode.Ecc.MEDIUM, "Q": QrCode.Ecc.QUARTILE, "H": QrCode.Ecc.HIGH}
    ecc = ecc_map[ecc_level.upper()]

    decoy_bytes = decoy.encode("utf-8")
    secret_bytes = secret.encode("utf-8") if secret else b""
    ecc_secret_bytes = ecc_secret.encode("utf-8") if ecc_secret else b""

    pad_bytes_capacity, blocks, ecc_per_block, total_ecc = qr_capacity(len(decoy_bytes), version, ecc)
    need_pad = len(secret_bytes) + 1 if secret_bytes else 0
    if need_pad > pad_bytes_capacity:
        print(f"Not enough pad capacity on {version}-{ecc_level}. "
              f"Need {need_pad} bytes (incl. 1B overhead), have {pad_bytes_capacity}.")
        return

    data_block_lens, epb = _block_layout(version, ecc)
    pad_start = _pad_start_bits(len(decoy_bytes), version, ecc)
    lock_bytes = pad_start // 8 + (1 + len(secret_bytes) if secret_bytes else 0)
    ecc_cap = calc_ecc_capacity(data_block_lens, lock_bytes, epb)

    if len(ecc_secret_bytes) > 255:
        print("ECC secret too long for 1-byte length prefix (max 255 bytes).")
        return
    if len(ecc_secret_bytes) + 1 > ecc_cap:
        print(f"Not enough ECC capacity. Need {len(ecc_secret_bytes) + 1} bytes "
              f"(incl. 1B length prefix), have {ecc_cap}.")
        return

    if check_only:
        print(f"{version}-{ecc_level} OK — pad: {need_pad} ≤ {pad_bytes_capacity} bytes; "
              f"ECC: {blocks} blocks × {ecc_per_block} bytes, GJ capacity {ecc_cap} bytes.")
        return

    # Build data codewords (decoy + optional padding secret)
    datacw = build_datacodewords(decoy_bytes, version, ecc, secret_bytes)

    # Apply ECC steganography via GJ if requested
    if ecc_secret_bytes:
        datacw = embed_ecc_secret_gj(version, ecc, ecc_secret_bytes, lock_bytes, datacw)

    qr = QrCode(version, ecc, bytearray(datacw), mask)

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
        msg += f" + ECC stego ({len(ecc_secret_bytes)} bytes, GJ)"
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
    if pad_capacity_bits < 8:  # Need at least 1 byte for length prefix
        return None

    # Extract padding bytes
    pad_byte_start = pad_start // 8
    pad_byte_count = pad_capacity_bits // 8

    # Read length prefix
    if pad_byte_start + 1 > len(data_bytes):
        return None

    secret_len = data_bytes[pad_byte_start]

    # Validate length
    if secret_len == 0 or secret_len + 1 > pad_byte_count:
        return None

    # Extract secret
    secret_start = pad_byte_start + 1
    secret_end = secret_start + secret_len
    if secret_end > len(data_bytes):
        return None

    return bytes(data_bytes[secret_start:secret_end])




def auto_decode(path: str, border: int = 4, extract_ecc: bool = True) -> None:
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
        try:
            ecc_secret = extract_ecc_secret_gj(M, version, ecc, mask_id, count if count else 0)
            if ecc_secret:
                try:
                    print(f"Recovered ECC secret (utf-8): {ecc_secret.decode('utf-8')}")
                except UnicodeDecodeError:
                    print(f"Recovered ECC secret (hex): {ecc_secret.hex()}")
            else:
                print("No ECC secret found")
        except Exception as e:
            print(f"Failed to extract ECC secret: {e}")


# -------------------------------- CLI ------------------------------------

def main():
    import sys
    ap = argparse.ArgumentParser(description="QR padding+ECC stego (8-bit) with capacity planner")
    sub = ap.add_subparsers(dest="cmd")

    enc = sub.add_parser("encode")
    enc.add_argument("--decoy", required=True)
    enc.add_argument("--secret", default="", help="Secret to hide in padding")
    enc.add_argument("--ecc-secret", default="", help="Second secret to hide in ECC bytes (GJ method)")
    enc.add_argument("--version", type=int, default=4, help="QR version (1..40)")
    enc.add_argument("--ecc", default="H", choices=["L", "M", "Q", "H"], help="Error correction level")
    enc.add_argument("--mask", type=int, default=0, choices=list(range(8)))
    enc.add_argument("--out", default="qr_stego.png")
    enc.add_argument("--check-only", action="store_true", help="Only check capacity, don't write image")

    dec = sub.add_parser("decode")
    dec.add_argument("image")
    dec.add_argument("--border", type=int, default=4)
    dec.add_argument("--no-ecc", action="store_true", help="Don't extract ECC secret")

    plan = sub.add_parser("plan")
    plan.add_argument("--decoy", required=True, help="Visible decoy string")
    plan.add_argument("--pad-secret-len", type=int, required=True, help="Secret bytes to hide in padding")
    plan.add_argument("--ecc-secret-len", type=int, required=True, help="Secret bytes to hide in ECC bytes")
    plan.add_argument("--overhead", type=int, default=1, help="Overhead bytes to reserve in padding")

    args = ap.parse_args()
    if args.cmd == "encode":
        create_stego_qr(args.decoy, args.secret, version=args.version, ecc_level=args.ecc,
                        mask=args.mask, out_path=args.out, check_only=args.check_only,
                        ecc_secret=args.ecc_secret)
    elif args.cmd == "decode":
        auto_decode(args.image, border=args.border, extract_ecc=not args.no_ecc)
    elif args.cmd == "plan":
        res = plan_min_settings(decoy_len=len(args.decoy),
                                pad_secret_len=args.pad_secret_len,
                                ecc_secret_len=args.ecc_secret_len,
                                overhead_bytes=args.overhead)
        if res is None:
            print("No (version, ECC) up to 40-H fits both constraints.")
            sys.exit(2)
        version, ecc_name, details = res
        print(f"Minimum setting: version {version}, ECC {ecc_name}")
        print(f"Pad capacity: {details['pad_capacity']} bytes (need {args.pad_secret_len + args.overhead})")
        print(f"ECC: {details['blocks']} blocks × {details['ecc_per_block']} ECC bytes (total {details['ecc_total']})")
        print(f"GJ ECC stego capacity: {details['ecc_capacity']} bytes (need {args.ecc_secret_len + 1} incl. prefix)")
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
