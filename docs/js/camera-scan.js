// Live camera QR scanning for the Decode tab.
//
// Pipeline per frame:
//   1. jsQR finds the QR and gives us its version + the four outer corners.
//   2. We build a projective transform (unit square -> the four corners) and sample
//      the centre of every module straight from the camera frame, so perspective,
//      rotation and scale are all undone. jsQR's error correction is NOT used for
//      this: the stego payload lives in bytes that error correction would "fix".
//   3. Several consecutive frames must agree on the module grid (noise rejection).
//   4. The agreed grid is redrawn as a clean, axis-aligned PNG-style canvas (the same
//      format the encoder emits) and handed to the normal decoder.

const QRCameraScanner = {
    // Consecutive identical grids required before accepting.
    STABLE_FRAMES: 4,
    // If frames never agree exactly, accept a majority vote after this many detections.
    MAX_FRAMES_BEFORE_VOTE: 40,
    VOTE_WINDOW: 8,
    SCAN_INTERVAL_MS: 90,

    _state: null,

    // ── Geometry ─────────────────────────────────────────────────────────────

    /** Heckbert's unit-square -> quad projective map. Corners: TL, TR, BR, BL. */
    squareToQuad(tl, tr, br, bl) {
        const dx1 = tr.x - br.x, dx2 = bl.x - br.x, dx3 = tl.x - tr.x + br.x - bl.x;
        const dy1 = tr.y - br.y, dy2 = bl.y - br.y, dy3 = tl.y - tr.y + br.y - bl.y;
        let a, b, d, e, g, h;
        if (Math.abs(dx3) < 1e-9 && Math.abs(dy3) < 1e-9) {
            g = 0; h = 0;
            a = tr.x - tl.x; b = bl.x - tl.x;
            d = tr.y - tl.y; e = bl.y - tl.y;
        } else {
            const den = dx1 * dy2 - dx2 * dy1;
            g = (dx3 * dy2 - dx2 * dy3) / den;
            h = (dx1 * dy3 - dx3 * dy1) / den;
            a = tr.x - tl.x + g * tr.x; b = bl.x - tl.x + h * bl.x;
            d = tr.y - tl.y + g * tr.y; e = bl.y - tl.y + h * bl.y;
        }
        const c = tl.x, f = tl.y;
        return (u, v) => {
            const w = g * u + h * v + 1;
            return { x: (a * u + b * v + c) / w, y: (d * u + e * v + f) / w };
        };
    },

    // ── Sampling ─────────────────────────────────────────────────────────────

    /**
     * Sample an N x N module grid from a frame. Returns { modules, finderScore }
     * where modules[y][x] === true means a dark module.
     */
    sampleModules(imageData, loc, version) {
        const N = version * 4 + 17;
        const { data, width, height } = imageData;
        const map = this.squareToQuad(
            loc.topLeftCorner, loc.topRightCorner, loc.bottomRightCorner, loc.bottomLeftCorner);

        const gray = (px, py) => {
            const x = Math.min(width - 1, Math.max(0, Math.round(px)));
            const y = Math.min(height - 1, Math.max(0, Math.round(py)));
            const i = (y * width + x) * 4;
            return 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
        };

        // Average the centre plus four points a quarter-module away: robust to sensor
        // noise and small corner errors, still entirely inside the module.
        const offs = [[0, 0], [-0.25, -0.25], [0.25, -0.25], [-0.25, 0.25], [0.25, 0.25]];
        const lum = new Float32Array(N * N);
        for (let y = 0; y < N; y++) {
            for (let x = 0; x < N; x++) {
                let sum = 0;
                for (const [ox, oy] of offs) {
                    const p = map((x + 0.5 + ox) / N, (y + 0.5 + oy) / N);
                    sum += gray(p.x, p.y);
                }
                lum[y * N + x] = sum / offs.length;
            }
        }

        const threshold = this.otsu(lum);
        const modules = [];
        for (let y = 0; y < N; y++) {
            modules[y] = [];
            for (let x = 0; x < N; x++) modules[y][x] = lum[y * N + x] < threshold;
        }
        return { modules, finderScore: this.finderScore(modules) };
    },

    /** Otsu threshold over luminance samples. */
    otsu(values) {
        const hist = new Array(256).fill(0);
        for (const v of values) hist[Math.min(255, Math.max(0, Math.round(v)))]++;
        const total = values.length;
        let sumAll = 0;
        for (let i = 0; i < 256; i++) sumAll += i * hist[i];
        let wB = 0, sumB = 0, best = -1, thr = 128;
        for (let t = 0; t < 256; t++) {
            wB += hist[t];
            if (!wB) continue;
            const wF = total - wB;
            if (!wF) break;
            sumB += t * hist[t];
            const mB = sumB / wB, mF = (sumAll - sumB) / wF;
            const between = wB * wF * (mB - mF) * (mB - mF);
            if (between > best) { best = between; thr = t; }
        }
        return thr + 0.5;
    },

    /** Fraction of the three 7x7 finder patterns that match the ideal pattern. */
    finderScore(m) {
        const N = m.length;
        const ideal = (x, y) => {
            const r = Math.max(Math.abs(x - 3), Math.abs(y - 3));
            return r !== 2; // ring pattern: dark, light, dark core (r=0..1 dark, 2 light, 3 dark)
        };
        let ok = 0, tot = 0;
        for (const [ox, oy] of [[0, 0], [N - 7, 0], [0, N - 7]]) {
            for (let y = 0; y < 7; y++) {
                for (let x = 0; x < 7; x++) {
                    tot++;
                    if (m[oy + y][ox + x] === ideal(x, y)) ok++;
                }
            }
        }
        return ok / tot;
    },

    // ── Helpers ──────────────────────────────────────────────────────────────

    gridKey(modules) {
        return modules.map(r => r.map(v => (v ? '1' : '0')).join('')).join('');
    },

    majority(grids) {
        const N = grids[0].length;
        return Array.from({ length: N }, (_, y) =>
            Array.from({ length: N }, (_, x) =>
                grids.reduce((n, g) => n + (g[y][x] ? 1 : 0), 0) * 2 > grids.length));
    },

    /** Clean, axis-aligned image of a module grid (same as the encoder's output). */
    renderRectified(modules) {
        return drawModules(modules, 8, 4);
    },

    // ── Live loop ────────────────────────────────────────────────────────────

    /**
     * start({ video, overlay, onStatus, onResult })
     *   onStatus(text, kind)           progress messages (kind: 'info' | 'ok' | 'warn')
     *   onResult({ canvas, decoy, version, approximate })  called once, then scanning stops
     * Returns a stop() function.
     */
    start({ video, overlay, onStatus, onResult }) {
        const work = document.createElement('canvas');
        const wctx = work.getContext('2d', { willReadFrequently: true });
        const octx = overlay.getContext('2d');

        const st = this._state = {
            running: true, timer: null,
            decoy: null, version: null,
            recent: [],          // recent grids, newest last
            sameRun: 0,          // consecutive identical grids
            lastKey: null,
            detections: 0
        };

        const resetTracking = () => {
            st.recent = []; st.sameRun = 0; st.lastKey = null; st.detections = 0;
        };

        const drawQuad = (loc, color) => {
            octx.clearRect(0, 0, overlay.width, overlay.height);
            if (!loc) return;
            octx.lineWidth = Math.max(3, overlay.width / 200);
            octx.strokeStyle = color;
            octx.beginPath();
            const pts = [loc.topLeftCorner, loc.topRightCorner, loc.bottomRightCorner, loc.bottomLeftCorner];
            pts.forEach((p, i) => (i ? octx.lineTo(p.x, p.y) : octx.moveTo(p.x, p.y)));
            octx.closePath();
            octx.stroke();
        };

        const finish = (modules, approximate) => {
            st.running = false;
            drawQuad(null);
            onResult({
                canvas: this.renderRectified(modules),
                decoy: st.decoy,
                version: st.version,
                approximate
            });
        };

        const tick = () => {
            if (!st.running) return;
            st.timer = setTimeout(tick, this.SCAN_INTERVAL_MS);

            if (video.readyState < 2 || !video.videoWidth) return;
            if (work.width !== video.videoWidth) {
                work.width = overlay.width = video.videoWidth;
                work.height = overlay.height = video.videoHeight;
            }
            wctx.drawImage(video, 0, 0);
            const frame = wctx.getImageData(0, 0, work.width, work.height);

            let code = null;
            try {
                code = jsQR(frame.data, frame.width, frame.height, { inversionAttempts: 'dontInvert' });
            } catch (e) { /* treat as not found */ }

            if (!code || !code.version || code.version > 10) {
                drawQuad(null);
                if (code && code.version > 10) {
                    onStatus(`QR version ${code.version} is larger than the decoder supports (max 10).`, 'warn');
                } else {
                    onStatus('Point the camera at a QR code…', 'info');
                }
                resetTracking();
                return;
            }

            const loc = code.location;
            const { modules, finderScore } = this.sampleModules(frame, loc, code.version);

            if (finderScore < 0.9) {
                drawQuad(loc, '#f59e0b');
                onStatus('Corners look off. Hold the code flatter or move closer.', 'warn');
                resetTracking();
                return;
            }

            // A different code (or version) came into view: start over.
            if (code.data !== st.decoy || code.version !== st.version) {
                resetTracking();
                st.decoy = code.data;
                st.version = code.version;
            }

            st.detections++;
            st.recent.push(modules);
            if (st.recent.length > this.VOTE_WINDOW) st.recent.shift();

            const key = this.gridKey(modules);
            st.sameRun = key === st.lastKey ? st.sameRun + 1 : 1;
            st.lastKey = key;

            drawQuad(loc, '#22c55e');

            if (st.sameRun >= this.STABLE_FRAMES) {
                finish(modules, false);
                return;
            }
            if (st.detections >= this.MAX_FRAMES_BEFORE_VOTE && st.recent.length >= this.VOTE_WINDOW) {
                finish(this.majority(st.recent), true);
                return;
            }
            onStatus(`QR found (v${code.version}). Hold steady… ${st.sameRun}/${this.STABLE_FRAMES}`, 'ok');
        };

        st.timer = setTimeout(tick, this.SCAN_INTERVAL_MS);
        return () => this.stop();
    },

    stop() {
        if (this._state) {
            this._state.running = false;
            clearTimeout(this._state.timer);
            this._state = null;
        }
    }
};
