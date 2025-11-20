# CTF Quick Reference Card

## 🎯 Flags

```
Challenge 1: flag{h1dd3n_1n_th3_p4dd1ng_byt3s}
Challenge 2: flag{3cc_bits_c0mpr0m1s3d}
```

## 🔍 Verify Flags

```bash
cd ctf_challenges

# Challenge 1
python3 solution_challenge1.py | grep flag

# Challenge 2
python3 solution_challenge2.py | grep flag
```

## 💡 Hints to Give (Progressive)

### Challenge 1

**Hint Level 1** (if stuck after 30 min):
> "QR codes pad data to a fixed length. What goes in the padding?"

**Hint Level 2** (if stuck after 1 hour):
> "QR data is interleaved across blocks. You'll need to deinterleave to see the raw data."

**Hint Level 3** (if stuck after 2 hours):
> "Look for a 2-byte length prefix in the padding area. The secret follows immediately after."

### Challenge 2

**Hint Level 1** (if stuck after 1 hour):
> "Compare both QR code images pixel-by-pixel. What regions changed?"

**Hint Level 2** (if stuck after 2 hours):
> "Error correction codes can be modified without breaking the QR. Research Reed-Solomon."

**Hint Level 3** (if stuck after 3 hours):
> "The secret is in the FIRST bytes of each ECC block, not all ECC bytes."

**Hint Level 4** (if stuck after 4 hours):
> "Try k_per_block values between 4 and 11. The secret has a 2-byte length prefix."

## 📊 Expected Player Questions

**Q: "The QR code scans normally, is this a trick?"**
> A: It's supposed to scan normally. The hidden data doesn't interfere with the visible message.

**Q: "Do I need special software?"**
> A: Python and common libraries (PIL, pyzbar) are sufficient. Or write your own parser.

**Q: "Are the challenges related?"**
> A: Yes, they use the same visible message but hide data in different locations.

**Q: "How do I know k_per_block for Challenge 2?"**
> A: Part of the challenge is figuring this out. Try different values (hint: 4-11).

**Q: "Can I have the source code?"**
> A: No, researching QR structure is part of the challenge. (Unless you want to make it easier)

## 🎓 Spoiler-Free Help

If players ask for help without wanting spoilers:

**Challenge 1:**
- Point them to thonky.com QR tutorial
- Suggest they learn about QR data structure
- Recommend they try writing a basic QR parser

**Challenge 2:**
- Point them to Reed-Solomon explainers
- Suggest comparing the two images
- Recommend they understand ECC block structure

## ⚙️ Technical Info (For Debugging)

### Challenge 1
```
Version: 5, ECC: H, Mask: 0
Data capacity: 46 bytes (368 bits)
Padding starts: bit 80 (after 8-byte message + overhead)
Secret: bytes 10-42 (with 2-byte length header)
```

### Challenge 2
```
Version: 5, ECC: H, Mask: 0
Total ECC: 88 bytes across 4 blocks
k_per_block: 8
Secret distributed: 8 bytes × 4 blocks = 32 bytes total
Actual secret: 26 bytes + 2-byte header = 28 bytes used
```

## 🏆 First Blood Hints

If a team is very close but struggling:

**Challenge 1 near-solve:**
> "The secret starts at byte offset 10 in the deinterleaved data"

**Challenge 2 near-solve:**
> "You need exactly 8 bytes from each of the 4 ECC blocks"

## 📞 Emergency Commands

If something breaks or you need to verify:

```bash
# Quick flag check
grep -r "flag{" ctf_challenges/*.py

# Regenerate challenges (if needed)
cd /Users/joshbloom/PycharmProjects/qr_ec_stego
source venv/bin/activate

# Challenge 1
python padding_ecc_stego_v3_8bit.py encode \
  --decoy "SCAN ME!" \
  --secret "flag{h1dd3n_1n_th3_p4dd1ng_byt3s}" \
  --version 5 --ecc H --mask 0 \
  --out ctf_challenges/challenge1_qr.png

# Challenge 2
python padding_ecc_stego_v3_8bit.py encode \
  --decoy "SCAN ME!" \
  --secret "flag{h1dd3n_1n_th3_p4dd1ng_byt3s}" \
  --ecc-secret "flag{3cc_bits_c0mpr0m1s3d}" \
  --version 5 --ecc H --mask 0 \
  --k-per-block 8 --safety 0 \
  --out ctf_challenges/challenge2_qr.png
```

## ✅ Solve Verification

When teams submit flags:

```bash
# Valid submissions
flag{h1dd3n_1n_th3_p4dd1ng_byt3s}
flag{3cc_bits_c0mpr0m1s3d}

# Case sensitive: YES
# Braces required: YES
# Format must be exact
```
