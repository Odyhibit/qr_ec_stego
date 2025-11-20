// QR Code Steganography Decoder Module

const QRStego = {
    /**
     * Decode a QR code and extract hidden messages
     */
    async decode(options) {
        const {
            image,
            extractPadding = true,
            extractECC = true,
            kPerBlock = 8
        } = options;

        // Get image data from the image
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = image.width;
        canvas.height = image.height;
        ctx.drawImage(image, 0, 0);
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);

        // Decode visible message using jsQR
        let decoy = null;
        try {
            if (typeof jsQR !== 'undefined') {
                const code = jsQR(imageData.data, imageData.width, imageData.height);
                if (code) {
                    decoy = code.data;
                }
            }
        } catch (e) {
            console.warn('jsQR decode failed:', e);
        }

        // Parse QR structure for steganography using our custom parser
        let qrData = null;
        try {
            qrData = QRParser.parse(imageData);
            console.log('QR structure parsed:', qrData);
        } catch (e) {
            console.error('QR parsing failed:', e);
            // Fall back to basic info
            qrData = {
                version: 5,
                size: 37,
                eccLevel: 'H',
                mask: 0,
                dataCodewords: [],
                eccCodewords: [],
                eccSpec: null
            };
        }

        const result = {
            decoy: decoy || '(could not decode)',
            version: qrData.version,
            size: qrData.size,
            eccLevel: qrData.eccLevel,
            mask: qrData.mask,
            paddingSecret: null,
            eccSecret: null,
            kPerBlock
        };

        // Extract padding secret
        if (extractPadding && qrData && qrData.dataCodewords && qrData.dataCodewords.length > 0) {
            try {
                result.paddingSecret = QRParser.extractPaddingSecret(qrData.dataCodewords, qrData.version);
                if (!result.paddingSecret) {
                    result.paddingSecret = '';
                }
            } catch (e) {
                console.error('Padding extraction failed:', e);
                result.paddingSecret = '';
            }
        }

        // Extract ECC secret
        if (extractECC && qrData && qrData.eccCodewords && qrData.eccCodewords.length > 0) {
            try {
                const numBlocks = qrData.eccSpec ? qrData.eccSpec.blocks : 4;
                const eccPerBlock = qrData.eccSpec ? qrData.eccSpec.eccPerBlock : 22;
                result.eccSecret = QRParser.extractECCSecret(qrData.eccCodewords, kPerBlock, numBlocks, eccPerBlock);
                if (!result.eccSecret) {
                    result.eccSecret = '';
                }
            } catch (e) {
                console.error('ECC extraction failed:', e);
                result.eccSecret = '';
            }
        }

        return result;
    },

    /**
     * Compare two QR code images
     */
    async compare(img1, img2) {
        const canvas1 = document.createElement('canvas');
        const canvas2 = document.createElement('canvas');
        const ctx1 = canvas1.getContext('2d');
        const ctx2 = canvas2.getContext('2d');

        // Ensure both canvases are the same size
        const width = Math.min(img1.width, img2.width);
        const height = Math.min(img1.height, img2.height);

        canvas1.width = canvas2.width = width;
        canvas1.height = canvas2.height = height;

        ctx1.drawImage(img1, 0, 0, width, height);
        ctx2.drawImage(img2, 0, 0, width, height);

        const data1 = ctx1.getImageData(0, 0, width, height);
        const data2 = ctx2.getImageData(0, 0, width, height);

        // Create difference image
        const diffCanvas = document.createElement('canvas');
        diffCanvas.width = width;
        diffCanvas.height = height;
        const diffCtx = diffCanvas.getContext('2d');
        const diffData = diffCtx.createImageData(width, height);

        let diffPixels = 0;
        const totalPixels = width * height;

        for (let i = 0; i < data1.data.length; i += 4) {
            const r1 = data1.data[i];
            const g1 = data1.data[i + 1];
            const b1 = data1.data[i + 2];

            const r2 = data2.data[i];
            const g2 = data2.data[i + 1];
            const b2 = data2.data[i + 2];

            const isDifferent = r1 !== r2 || g1 !== g2 || b1 !== b2;

            if (isDifferent) {
                diffPixels++;
                // Mark difference in white
                diffData.data[i] = 255;
                diffData.data[i + 1] = 255;
                diffData.data[i + 2] = 255;
                diffData.data[i + 3] = 255;
            } else {
                // Keep same in black
                diffData.data[i] = 0;
                diffData.data[i + 1] = 0;
                diffData.data[i + 2] = 0;
                diffData.data[i + 3] = 255;
            }
        }

        diffCtx.putImageData(diffData, 0, 0);
        const diffImageURL = diffCanvas.toDataURL('image/png');

        // Try to decode both QR codes to see if they have the same message
        let sameDecoy = false;
        try {
            const result1 = await this.decode({ image: img1, extractPadding: false, extractECC: false });
            const result2 = await this.decode({ image: img2, extractPadding: false, extractECC: false });
            sameDecoy = result1.decoy === result2.decoy;
        } catch (e) {
            console.warn('Could not decode QR codes for comparison');
        }

        return {
            diffPixels,
            totalPixels,
            diffImageURL,
            sameDecoy
        };
    },

};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = QRStego;
};
