# CTF Challenge: QR Code Steganography

## Quick Start for Organizers

### Challenge Files

**Challenge 1 (Easy/Medium - 100 points):**
- `challenge1_qr.png` - QR code with padding secret
- `challenge1_description.md` - Challenge description and hints
- Flag: `flag{h1dd3n_1n_th3_p4dd1ng_byt3s}`

**Challenge 2 (Hard - 300 points):**
- `challenge2_qr.png` - QR code with ECC secret
- `challenge2_description.md` - Challenge description and hints
- Flag: `flag{3cc_bits_c0mpr0m1s3d}`

### Solutions

Three solution scripts are provided:

1. **`solution_challenge1.py`** - Simple solution using provided tools
2. **`solution_challenge2.py`** - Simple solution + visual diff analysis
3. **`solution_manual.py`** - Detailed step-by-step manual extraction (educational)

### Testing Solutions

```bash
# Test Challenge 1
cd ctf_challenges
python3 solution_challenge1.py

# Test Challenge 2
python3 solution_challenge2.py

# Run manual solution (shows full process)
python3 solution_manual.py
```

### Deployment

**Option 1: Standalone Challenges**
- Give players only the QR code images
- Provide descriptions as separate text/web pages
- Let them figure out the tools needed

**Option 2: Provide Starter Code**
- Give players the `padding_ecc_stego_v3_8bit.py` file as a "found tool"
- Makes Challenge 1 easier (they can study the code)
- Challenge 2 still requires understanding the tool's parameters

**Option 3: No Tools (Hardest)**
- Only give QR images and challenge descriptions
- Players must research QR structure and write extraction code
- Significantly harder

### Recommended Deployment

For the difficulty levels specified:

**Challenge 1 (Easy/Medium):**
- Provide QR image only
- Give hints about QR padding
- Expected solve time: 30-60 minutes for experienced players
- Players should research QR structure or find existing tools

**Challenge 2 (Hard):**
- Provide both QR images (for visual comparison)
- Mention "error correction" in description
- Expected solve time: 2-4 hours
- Requires deeper understanding of QR structure

### Technical Details

**Challenge 1 Parameters:**
```bash
Version: 5
ECC Level: H
Decoy: "SCAN ME!"
Secret location: Padding bytes
Secret: flag{h1dd3n_1n_th3_p4dd1ng_byt3s}
```

**Challenge 2 Parameters:**
```bash
Version: 5
ECC Level: H
Decoy: "SCAN ME!" (same as Challenge 1)
Secret location: ECC bytes
Secret: flag{3cc_bits_c0mpr0m1s3d}
k_per_block: 8
Blocks: 4
Total ECC capacity used: 32 bytes (out of 88 total ECC bytes)
```

### Interesting Properties

1. **Both QR codes scan correctly** - Even Challenge 2 with compromised ECC
   still scans because we only used 8 out of 11 correctable bytes per block.

2. **Visual diff reveals location** - Comparing the images shows changes in the
   outer regions where ECC is typically stored.

3. **Realistic scenario** - This mimics real-world steganography where the
   carrier (QR code) must remain functional.

### Difficulty Calibration

**To make Challenge 1 easier:**
- Provide the `padding_ecc_stego_v3_8bit.py` tool
- Add hint about deinterleaving
- Reduce to 50 points

**To make Challenge 1 harder:**
- No tools provided
- More cryptic hints
- Increase to 150 points

**To make Challenge 2 easier:**
- Provide the tool with documentation
- Give example of k_per_block parameter
- Reduce to 200 points

**To make Challenge 2 harder:**
- Don't provide Challenge 1 as reference
- No visual diff hint
- Use k_per_block=4 (less ECC compromise, harder to detect)
- Increase to 400 points

### Expected Player Approaches

**Challenge 1:**
1. Scan QR → "SCAN ME!" → seems normal
2. Research QR structure → learn about padding
3. Find/write extraction code
4. Extract padding → find flag

**Challenge 2:**
1. Notice similarity to Challenge 1
2. Visual diff → see changes in ECC region
3. Research Reed-Solomon / QR error correction
4. Understand ECC block structure
5. Extract ECC bytes → deinterleave → find flag

### Hints Release Schedule (Suggested)

**Challenge 1:**
- 0 min: Challenge release
- 30 min: Hint 1 (padding bytes)
- 60 min: Hint 2 (deinterleaving)
- 120 min: Hint 3 (code structure)

**Challenge 2:**
- 0 min: Challenge release
- 60 min: Hint 1 (visual diff)
- 120 min: Hint 2 (ECC compromise)
- 180 min: Hint 3 (block structure)
- 240 min: Hint 4 (k_per_block concept)

### Additional Challenge Ideas

**Challenge 3 (Expert):**
- Combine both: padding AND ECC secrets
- Two flags to find
- Different k_per_block value (not documented)

**Challenge 4 (Forensics):**
- Provide damaged QR with real errors AND steganography
- Players must distinguish real errors from hidden data

**Challenge 5 (Crypto):**
- Secret is encrypted
- Key hidden in Challenge 1's flag
- Decrypt to get final flag

## Files Checklist

- [x] challenge1_qr.png
- [x] challenge2_qr.png
- [x] challenge1_description.md
- [x] challenge2_description.md
- [x] solution_challenge1.py
- [x] solution_challenge2.py
- [x] solution_manual.py
- [x] README_ORGANIZER.md (this file)

## Quick Verification

```bash
# Verify Challenge 1 flag
python3 -c "
import sys
sys.path.insert(0, '..')
from padding_ecc_stego_v3_8bit import auto_decode
auto_decode('challenge1_qr.png', extract_ecc=False)
" | grep "flag{"

# Verify Challenge 2 flag
python3 -c "
import sys
sys.path.insert(0, '..')
from padding_ecc_stego_v3_8bit import auto_decode
auto_decode('challenge2_qr.png', extract_ecc=True, k_per_block=8)
" | grep "flag{"
```
