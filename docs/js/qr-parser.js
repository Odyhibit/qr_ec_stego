// QR Code Structure Parser
// Extracts raw data and ECC bytes from QR codes

const QRParser = {
    // QR specifications
    VERSION_INFO: {
        1: {
            size: 21,
            totalCodewords: 26,
            ecBlocks: {
                'L': { blocks: 1, dataPerBlock: 19, eccPerBlock: 7 },
                'M': { blocks: 1, dataPerBlock: 16, eccPerBlock: 10 },
                'Q': { blocks: 1, dataPerBlock: 13, eccPerBlock: 13 },
                'H': { blocks: 1, dataPerBlock: 9, eccPerBlock: 17 }
            }
        },
        2: {
            size: 25,
            totalCodewords: 44,
            ecBlocks: {
                'L': { blocks: 1, dataPerBlock: 34, eccPerBlock: 10 },
                'M': { blocks: 1, dataPerBlock: 28, eccPerBlock: 16 },
                'Q': { blocks: 1, dataPerBlock: 22, eccPerBlock: 22 },
                'H': { blocks: 1, dataPerBlock: 16, eccPerBlock: 28 }
            }
        },
        3: {
            size: 29,
            totalCodewords: 70,
            ecBlocks: {
                'L': { blocks: 1, dataPerBlock: 55, eccPerBlock: 15 },
                'M': { blocks: 1, dataPerBlock: 44, eccPerBlock: 26 },
                'Q': { blocks: 2, dataPerBlock: 17, eccPerBlock: 18 },
                'H': { blocks: 2, dataPerBlock: 13, eccPerBlock: 22 }
            }
        },
        4: {
            size: 33,
            totalCodewords: 100,
            ecBlocks: {
                'L': { blocks: 1, dataPerBlock: 80, eccPerBlock: 20 },
                'M': { blocks: 2, dataPerBlock: 32, eccPerBlock: 18 },
                'Q': { blocks: 2, dataPerBlock: 24, eccPerBlock: 26 },
                'H': { blocks: 4, dataPerBlock: 9, eccPerBlock: 16 }
            }
        },
        5: {
            size: 37,
            totalCodewords: 134,
            ecBlocks: {
                'L': { blocks: 1, dataPerBlock: 108, eccPerBlock: 26 },
                'M': { blocks: 2, dataPerBlock: 43, eccPerBlock: 24 },
                'Q': { blocks: 2, dataPerBlock: 15, eccPerBlock: 18, numShort: 2, dataPerBlock2: 16 },
                'H': { blocks: 4, dataPerBlock: 11, eccPerBlock: 22, numShort: 2, dataPerBlock2: 12 }
            }
        },
        6: {
            size: 41,
            totalCodewords: 172,
            ecBlocks: {
                'L': { blocks: 2, dataPerBlock: 68, eccPerBlock: 18 },
                'M': { blocks: 4, dataPerBlock: 27, eccPerBlock: 16 },
                'Q': { blocks: 4, dataPerBlock: 19, eccPerBlock: 24 },
                'H': { blocks: 4, dataPerBlock: 15, eccPerBlock: 28 }
            }
        },
        7: {
            size: 45,
            totalCodewords: 196,
            ecBlocks: {
                'L': { blocks: 2, dataPerBlock: 78, eccPerBlock: 20 },
                'M': { blocks: 4, dataPerBlock: 31, eccPerBlock: 18 },
                'Q': { blocks: 2, dataPerBlock: 14, eccPerBlock: 18, blocks2: 4, dataPerBlock2: 15, eccPerBlock2: 18 },
                'H': { blocks: 4, dataPerBlock: 13, eccPerBlock: 26, blocks2: 1, dataPerBlock2: 14, eccPerBlock2: 26 }
            }
        },
        8: {
            size: 49,
            totalCodewords: 242,
            ecBlocks: {
                'L': { blocks: 2, dataPerBlock: 97, eccPerBlock: 24 },
                'M': { blocks: 2, dataPerBlock: 38, eccPerBlock: 22, blocks2: 2, dataPerBlock2: 39, eccPerBlock2: 22 },
                'Q': { blocks: 4, dataPerBlock: 18, eccPerBlock: 22, blocks2: 2, dataPerBlock2: 19, eccPerBlock2: 22 },
                'H': { blocks: 4, dataPerBlock: 14, eccPerBlock: 26, blocks2: 2, dataPerBlock2: 15, eccPerBlock2: 26 }
            }
        },
        9: {
            size: 53,
            totalCodewords: 292,
            ecBlocks: {
                'L': { blocks: 2, dataPerBlock: 116, eccPerBlock: 30 },
                'M': { blocks: 3, dataPerBlock: 36, eccPerBlock: 22, blocks2: 2, dataPerBlock2: 37, eccPerBlock2: 22 },
                'Q': { blocks: 4, dataPerBlock: 16, eccPerBlock: 20, blocks2: 4, dataPerBlock2: 17, eccPerBlock2: 20 },
                'H': { blocks: 4, dataPerBlock: 12, eccPerBlock: 24, blocks2: 4, dataPerBlock2: 13, eccPerBlock2: 24 }
            }
        },
        10: {
            size: 57,
            totalCodewords: 346,
            ecBlocks: {
                'L': { blocks: 2, dataPerBlock: 68, eccPerBlock: 18, blocks2: 2, dataPerBlock2: 69, eccPerBlock2: 18 },
                'M': { blocks: 4, dataPerBlock: 43, eccPerBlock: 26, blocks2: 1, dataPerBlock2: 44, eccPerBlock2: 26 },
                'Q': { blocks: 6, dataPerBlock: 19, eccPerBlock: 24, blocks2: 2, dataPerBlock2: 20, eccPerBlock2: 24 },
                'H': { blocks: 6, dataPerBlock: 15, eccPerBlock: 28, blocks2: 2, dataPerBlock2: 16, eccPerBlock2: 28 }
            }
        }
    },

    /**
     * Parse QR code from image and extract all codewords
     */
    parse(imageData) {
        console.log('[Parse] Starting QR parse...');

        // Detect modules from image
        const modules = this.detectModules(imageData);
        if (!modules) {
            throw new Error('Could not detect QR code in image');
        }

        console.log(`[Parse] Detected ${modules.length}×${modules.length} module grid`);

        // Read format information
        const formatInfo = this.readFormatInfo(modules);
        const version = this.detectVersion(modules.length);

        console.log(`[Parse] Version: ${version}, ECC: ${formatInfo.eccLevel}, Mask: ${formatInfo.mask}`);

        // Get version specifications
        const versionSpec = this.VERSION_INFO[version];
        if (!versionSpec) {
            throw new Error(`QR version ${version} not supported`);
        }

        const eccSpec = versionSpec.ecBlocks[formatInfo.eccLevel];
        console.log(`[Parse] Spec: ${eccSpec.blocks} blocks, ${eccSpec.dataPerBlock} data bytes/block, ${eccSpec.eccPerBlock} ECC bytes/block`);

        // Extract raw bits from QR code
        const bits = this.extractDataBits(modules, version, formatInfo.mask);
        console.log(`[Parse] Extracted ${bits.length} bits`);

        // Convert bits to bytes (codewords)
        const codewords = this.bitsToBytes(bits);
        console.log(`[Parse] Converted to ${codewords.length} codewords`);
        console.log(`[Parse] First 20 codewords:`, codewords.slice(0, 20));

        // Calculate total bytes (handle mixed block sizes)
        const numShortBlocks = eccSpec.numShort !== undefined ? eccSpec.numShort : eccSpec.blocks;
        const numLongBlocks = eccSpec.blocks - numShortBlocks;
        const shortDataSize = eccSpec.dataPerBlock;
        const longDataSize = eccSpec.dataPerBlock2 || eccSpec.dataPerBlock;

        const totalDataBytes = numShortBlocks * shortDataSize + numLongBlocks * longDataSize;
        const totalECCBytes = eccSpec.blocks * eccSpec.eccPerBlock;

        // Calculate where data ends in INTERLEAVED stream
        // Phase 1: shortDataSize bytes from all blocks
        const phase1Bytes = shortDataSize * eccSpec.blocks;
        // Phase 2: 1 extra byte from long blocks only
        const phase2Bytes = numLongBlocks * (longDataSize - shortDataSize);
        const interleavedDataEnd = phase1Bytes + phase2Bytes;

        console.log(`[Parse] Splitting: ${totalDataBytes} data bytes (${numShortBlocks}×${shortDataSize} + ${numLongBlocks}×${longDataSize}), ${totalECCBytes} ECC bytes`);
        console.log(`[Parse] Interleaved data ends at position ${interleavedDataEnd}`);

        // Deinterleave data codewords (handling mixed sizes)
        const dataCodewords = this.deinterleaveMixed(
            codewords.slice(0, interleavedDataEnd),
            numShortBlocks,
            shortDataSize,
            numLongBlocks,
            longDataSize
        );

        console.log(`[Parse] Deinterleaved data (${dataCodewords.length} bytes):`, dataCodewords.slice(0, 20));

        // Deinterleave ECC codewords
        const eccCodewords = this.deinterleave(
            codewords.slice(interleavedDataEnd, interleavedDataEnd + totalECCBytes),
            eccSpec.blocks,
            eccSpec.eccPerBlock
        );

        console.log(`[Parse] Deinterleaved ECC:`, eccCodewords.slice(0, 20));

        return {
            version,
            size: modules.length,
            eccLevel: formatInfo.eccLevel,
            mask: formatInfo.mask,
            modules,
            dataCodewords,
            eccCodewords,
            eccSpec
        };
    },

    /**
     * Detect QR modules from image
     */
    detectModules(imageData) {
        const { width, height, data } = imageData;

        // Find QR boundaries
        const bounds = this.findQRBounds(data, width, height);
        if (!bounds) return null;

        const qrWidth = bounds.maxX - bounds.minX + 1;
        const qrHeight = bounds.maxY - bounds.minY + 1;

        // Detect version based on size
        // Try different versions to find best match based on actual pixel count
        let bestSize = 21;
        let bestModuleSize = 1;
        let bestDiff = Infinity;

        for (let v = 1; v <= 10; v++) {
            const size = v * 4 + 17;
            // Try both width and height to estimate module size
            const moduleSizeW = qrWidth / size;
            const moduleSizeH = qrHeight / size;
            const avgModuleSize = (moduleSizeW + moduleSizeH) / 2;

            // Module size should be close to an integer
            const diff = Math.abs(avgModuleSize - Math.round(avgModuleSize));

            if (diff < bestDiff) {
                bestDiff = diff;
                bestSize = size;
                bestModuleSize = Math.round(avgModuleSize);
            }
        }

        const moduleSize = bestModuleSize;
        console.log(`[Module Detection] QR bounds: ${qrWidth}×${qrHeight} pixels, detected ${bestSize}×${bestSize} modules, module size: ${moduleSize}px`);

        // Extract module grid, sampling from the center of each module
        const modules = [];
        for (let y = 0; y < bestSize; y++) {
            modules[y] = [];
            for (let x = 0; x < bestSize; x++) {
                // Sample from center of module
                const px = Math.floor(bounds.minX + (x + 0.5) * moduleSize);
                const py = Math.floor(bounds.minY + (y + 0.5) * moduleSize);

                // Make sure we're within bounds
                if (px >= width || py >= height || px < 0 || py < 0) {
                    modules[y][x] = false;
                    continue;
                }

                const idx = (py * width + px) * 4;
                const brightness = (data[idx] + data[idx + 1] + data[idx + 2]) / 3;
                modules[y][x] = brightness < 128; // true = black module
            }
        }

        return modules;
    },

    /**
     * Find QR code boundaries
     */
    findQRBounds(data, width, height) {
        let minX = width, maxX = 0, minY = height, maxY = 0;
        let found = false;

        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const idx = (y * width + x) * 4;
                const brightness = (data[idx] + data[idx + 1] + data[idx + 2]) / 3;
                if (brightness < 200) {
                    minX = Math.min(minX, x);
                    maxX = Math.max(maxX, x);
                    minY = Math.min(minY, y);
                    maxY = Math.max(maxY, y);
                    found = true;
                }
            }
        }

        return found ? { minX, maxX, minY, maxY } : null;
    },

    /**
     * Detect QR version from module count
     */
    detectVersion(size) {
        return Math.floor((size - 17) / 4);
    },

    /**
     * Read format information from QR code
     */
    readFormatInfo(modules) {
        const size = modules.length;

        // Format info is 15 bits stored around top-left and top-right/bottom-left
        // Reading from location near top-left finder pattern
        const formatBits = [];

        // Read horizontal part (row 8, columns 0-8 skipping 6)
        // Bits 0-5: columns 0-5
        for (let col = 0; col <= 5; col++) {
            formatBits.push(modules[8][col] ? 1 : 0);
        }
        // Skip column 6 (timing pattern)
        // Bits 6-7: columns 7-8
        formatBits.push(modules[8][7] ? 1 : 0);
        formatBits.push(modules[8][8] ? 1 : 0);

        // Read vertical part (column 8, rows 7 down to 0)
        // Bit 8: row 7
        formatBits.push(modules[7][8] ? 1 : 0);
        // Bits 9-14: rows 5 down to 0
        for (let row = 5; row >= 0; row--) {
            formatBits.push(modules[row][8] ? 1 : 0);
        }

        // Decode format info
        const formatValue = this.decodeFormatInfo(formatBits);

        return formatValue;
    },

    /**
     * Decode format information bits
     */
    decodeFormatInfo(bits) {
        // Convert bits to integer (MSB first)
        let formatInt = 0;
        for (let i = 0; i < 15; i++) {
            formatInt = (formatInt << 1) | bits[i];
        }

        // Remove format mask (XOR with 0x5412)
        formatInt ^= 0x5412;

        // Extract data bits (first 5 bits after error correction)
        // BCH error correction could be done here, but for now just use the bits
        const dataBits = (formatInt >> 10) & 0x1F;

        // Decode ECC level and mask
        // Format: bits 4-3 = ECC, bits 2-0 = mask
        const eccBits = (dataBits >> 3) & 0x03;
        const mask = dataBits & 0x07;

        // ECC level mapping: 01=L, 00=M, 11=Q, 10=H
        const eccLevels = ['M', 'L', 'H', 'Q'];  // Index: 00=M, 01=L, 10=H, 11=Q
        const eccLevel = eccLevels[eccBits];

        return { eccLevel, mask };
    },

    /**
     * Extract data bits from QR code following the zigzag pattern
     */
    extractDataBits(modules, version, mask) {
        const size = modules.length;
        const bits = [];

        // QR codes read data in columns from right to left, alternating up/down
        let upward = true;

        for (let col = size - 1; col > 0; col -= 2) {
            if (col === 6) col--; // Skip timing column

            for (let row = 0; row < size; row++) {
                const y = upward ? (size - 1 - row) : row;

                // Read two columns
                for (let c = 0; c < 2; c++) {
                    const x = col - c;

                    // Skip function patterns
                    if (this.isFunctionPattern(x, y, size, version)) continue;

                    // Read bit and unmask
                    let bit = modules[y][x] ? 1 : 0;
                    if (this.shouldUnmask(x, y, mask)) {
                        bit = bit ^ 1;
                    }

                    bits.push(bit);
                }
            }

            upward = !upward;
        }

        return bits;
    },

    /**
     * Check if position is part of a function pattern (finder, timing, alignment, etc.)
     */
    isFunctionPattern(x, y, size, version) {
        // Finder patterns (corners)
        if ((x < 9 && y < 9) ||  // Top-left
            (x < 9 && y >= size - 8) ||  // Bottom-left
            (x >= size - 8 && y < 9)) {  // Top-right
            return true;
        }

        // Timing patterns
        if (x === 6 || y === 6) return true;

        // Dark module
        if (x === 8 && y === size - 8) return true;

        // Alignment patterns
        const alignmentCenters = this.getAlignmentPatternCenters(version);
        for (let cy of alignmentCenters) {
            for (let cx of alignmentCenters) {
                // Skip if overlaps with finder patterns
                if ((cx < 10 && cy < 10) ||
                    (cx < 10 && cy >= size - 9) ||
                    (cx >= size - 9 && cy < 10)) {
                    continue;
                }
                // Check if (x,y) is within 5×5 alignment pattern centered at (cx, cy)
                if (Math.abs(x - cx) <= 2 && Math.abs(y - cy) <= 2) {
                    return true;
                }
            }
        }

        return false;
    },

    /**
     * Get alignment pattern center coordinates for a version
     */
    getAlignmentPatternCenters(version) {
        if (version === 1) return [];
        // Simplified - only handling versions 2-10
        const positions = {
            2: [6, 18],
            3: [6, 22],
            4: [6, 26],
            5: [6, 30],
            6: [6, 34],
            7: [6, 22, 38],
            8: [6, 24, 42],
            9: [6, 26, 46],
            10: [6, 28, 50],
            11: [6, 30, 54],
            12: [6, 32, 58],
            13: [6, 34, 62],
            14: [6, 26, 46, 66],
            15: [6, 26, 48, 70],
            16: [6, 26, 50, 74],
            17: [6, 30, 54, 78],
            18: [6, 30, 56, 82],
            19: [6, 30, 58, 86],
            20: [6, 34, 62, 90],
            21: [6, 28, 50, 72, 94],
            22: [6, 26, 50, 74, 98],
            23: [6, 30, 54, 78, 102],
            24: [6, 28, 54, 80, 106],
            25: [6, 32, 58, 84, 110],
            26: [6, 30, 58, 86, 114],
            27: [6, 34, 62, 90, 118],
            28: [6, 26, 50, 74, 98, 122],
            29: [6, 30, 54, 78, 102, 126],
            30: [6, 26, 52, 78, 104, 130],
            31: [6, 30, 56, 82, 108, 134],
            32: [6, 34, 60, 86, 112, 138],
            33: [6, 30, 58, 86, 114, 142],
            34: [6, 34, 62, 90, 118, 146],
            35: [6, 30, 54, 78, 102, 126, 150],
            36: [6, 24, 50, 76, 102, 128, 154],
            37: [6, 28, 54, 80, 106, 132, 158],
            38: [6, 32, 58, 84, 110, 136, 162],
            39: [6, 26, 54, 82, 110, 138, 166],
            40: [6, 30, 58, 86, 114, 142, 170]
        };
        return positions[version] || [];
    },

    /**
     * Check if position should be unmasked
     */
    shouldUnmask(x, y, mask) {
        switch (mask) {
            case 0: return (x + y) % 2 === 0;
            case 1: return y % 2 === 0;
            case 2: return x % 3 === 0;
            case 3: return (x + y) % 3 === 0;
            case 4: return (Math.floor(y / 2) + Math.floor(x / 3)) % 2 === 0;
            case 5: return ((x * y) % 2) + ((x * y) % 3) === 0;
            case 6: return (((x * y) % 2) + ((x * y) % 3)) % 2 === 0;
            case 7: return (((x + y) % 2) + ((x * y) % 3)) % 2 === 0;
            default: return false;
        }
    },

    /**
     * Convert bits to bytes
     */
    bitsToBytes(bits) {
        const bytes = [];
        for (let i = 0; i < bits.length; i += 8) {
            let byte = 0;
            for (let j = 0; j < 8 && i + j < bits.length; j++) {
                byte = (byte << 1) | bits[i + j];
            }
            bytes.push(byte);
        }
        return bytes;
    },

    /**
     * Deinterleave codewords
     * Interleaved format: B0[0], B1[0], B2[0], B3[0], B0[1], B1[1], ...
     * Output: B0[0], B0[1], ..., B1[0], B1[1], ..., etc.
     */
    deinterleave(codewords, numBlocks, bytesPerBlock) {
        const blocks = Array.from({ length: numBlocks }, () => []);

        // Deinterleave by distributing bytes to blocks
        for (let i = 0; i < bytesPerBlock; i++) {
            for (let block = 0; block < numBlocks; block++) {
                const idx = i * numBlocks + block;
                if (idx < codewords.length) {
                    blocks[block].push(codewords[idx]);
                }
            }
        }

        // Concatenate all blocks
        return blocks.flat();
    },

    /**
     * Deinterleave codewords with mixed block sizes
     * Some blocks are "short" and some are "long" (1 byte longer)
     */
    deinterleaveMixed(codewords, numShort, shortSize, numLong, longSize) {
        const totalBlocks = numShort + numLong;
        const blocks = Array.from({ length: totalBlocks }, () => []);

        // Interleaving pattern:
        // First shortSize bytes: all blocks contribute
        // Last byte: only long blocks contribute

        let pos = 0;

        // Phase 1: All blocks (up to shortSize)
        for (let i = 0; i < shortSize; i++) {
            for (let block = 0; block < totalBlocks; block++) {
                if (pos < codewords.length) {
                    blocks[block].push(codewords[pos++]);
                }
            }
        }

        // Phase 2: Only long blocks (the extra byte)
        if (longSize > shortSize) {
            for (let block = numShort; block < totalBlocks; block++) {
                if (pos < codewords.length) {
                    blocks[block].push(codewords[pos++]);
                }
            }
        }

        // Concatenate all blocks
        return blocks.flat();
    },

    /**
     * Extract padding secret from data codewords
     */
    extractPaddingSecret(dataCodewords, version = 5) {
        console.log(`[Padding] Extracting from ${dataCodewords.length} bytes, version ${version}`);
        console.log(`[Padding] First 15 bytes:`, dataCodewords.slice(0, 15));

        // Calculate where padding starts
        // For byte mode: mode(4 bits) + count(8 bits for v<=9) + data

        const capacityBits = dataCodewords.length * 8;
        const ccBits = version <= 9 ? 8 : 16; // Character count bits

        // Try to read the actual message length from the data
        // First byte has mode in top 4 bits, start of count in bottom 4 bits
        const firstByte = dataCodewords[0];
        const mode = (firstByte >> 4) & 0x0F;

        let decoyLen = 8; // Default for "SCAN ME!"

        // Try to read character count
        if (ccBits === 8) {
            // Count is in bits 4-11 (parts of byte 0 and byte 1)
            const count_msb = firstByte & 0x0F;
            const count_lsb = (dataCodewords[1] >> 4) & 0x0F;
            decoyLen = (count_msb << 4) | count_lsb;
        }

        console.log(`[Padding] Mode: ${mode}, Decoy length: ${decoyLen}`);

        // Calculate bit usage
        const modeBits = 4;
        const usedBits = modeBits + ccBits + (8 * decoyLen);
        const termBits = Math.min(4, capacityBits - usedBits);
        const afterTerm = usedBits + termBits;

        // Pad to byte boundary
        const padStartBit = afterTerm + ((-afterTerm) % 8);
        const padByteStart = Math.floor(padStartBit / 8);

        console.log(`[Padding] Padding starts at byte ${padByteStart}`);
        console.log(`[Padding] Bytes at padding start:`, dataCodewords.slice(padByteStart, padByteStart + 5));

        // Check if we have room for length prefix
        if (padByteStart + 1 > dataCodewords.length) {
            console.log(`[Padding] Not enough room for length prefix`);
            return '';
        }

        // Read length-prefixed secret (1 byte)
        const secretLen = dataCodewords[padByteStart];

        console.log(`[Padding] Secret length from prefix: ${secretLen}`);

        // Validate
        if (secretLen === 0 || secretLen > 255 || padByteStart + 1 + secretLen > dataCodewords.length) {
            console.log(`[Padding] Invalid secret length`);
            return '';
        }

        // Extract secret
        const secret = dataCodewords.slice(padByteStart + 1, padByteStart + 1 + secretLen);
        console.log(`[Padding] Secret bytes:`, secret);
        const secretStr = this.bytesToString(secret);
        console.log(`[Padding] Secret string: "${secretStr}"`);
        return secretStr;
    },

    /**
     * Extract ECC secret from ECC codewords
     */
    extractECCSecret(eccCodewords, kPerBlock, numBlocks, eccPerBlock) {
        // Extract first k bytes from each ECC block
        // eccCodewords is already deinterleaved, so each block has eccPerBlock bytes
        const secretBytes = [];

        console.log(`[ECC] Extracting ${kPerBlock} bytes from ${numBlocks} blocks (${eccPerBlock} bytes each)`);
        console.log(`[ECC] Total ECC codewords: ${eccCodewords.length}`);

        for (let block = 0; block < numBlocks; block++) {
            const blockStart = block * eccPerBlock;  // Each block has eccPerBlock bytes
            console.log(`[ECC] Block ${block} starts at byte ${blockStart}`);
            for (let i = 0; i < kPerBlock && blockStart + i < eccCodewords.length; i++) {
                secretBytes.push(eccCodewords[blockStart + i]);
            }
        }

        console.log(`[ECC] Extracted ${secretBytes.length} secret bytes:`, secretBytes);

        // Check for length-prefixed secret (1 byte)
        if (secretBytes.length >= 1) {
            const length = secretBytes[0];
            console.log(`[ECC] Secret length from prefix: ${length}`);
            if (length > 0 && length < secretBytes.length && length < 255) {
                const secret = secretBytes.slice(1, 1 + length);
                const secretStr = this.bytesToString(secret);
                console.log(`[ECC] Secret string: "${secretStr}"`);
                return secretStr;
            }
        }

        console.log(`[ECC] No valid secret found`);
        return '';
    },

    /**
     * Convert bytes to string
     */
    bytesToString(bytes) {
        try {
            return new TextDecoder('utf-8').decode(new Uint8Array(bytes));
        } catch (e) {
            return String.fromCharCode(...bytes.filter(b => b >= 32 && b < 127));
        }
    }
};
