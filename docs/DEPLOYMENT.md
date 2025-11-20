# Web Tool Deployment Guide

## Local Testing

### Option 1: Python HTTP Server
```bash
cd docs
python3 -m http.server 8000
# Visit http://localhost:8000
```

### Option 2: Direct File Opening
```bash
# Simply open the file in your browser
open docs/index.html  # macOS
# or
start docs/index.html  # Windows
# or
xdg-open docs/index.html  # Linux
```

Note: Some features may require a web server due to browser security restrictions.

## GitHub Pages Deployment

### Step 1: Push to GitHub

```bash
# Initialize git if not already done
git init
git add .
git commit -m "Add QR steganography web tool"

# Create repository on GitHub, then:
git remote add origin https://github.com/yourusername/qr_ec_stego.git
git branch -M main
git push -u origin main
```

### Step 2: Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** → **Pages**
3. Under "Build and deployment":
   - Source: **Deploy from a branch**
   - Branch: **main**
   - Folder: **/docs**
4. Click **Save**

### Step 3: Wait for Deployment

- GitHub will build and deploy your site
- Usually takes 1-2 minutes
- Check the Pages section for the live URL
- Your site will be at: `https://yourusername.github.io/qr_ec_stego/`

### Step 4: Update Links

Update the GitHub repository URL in `docs/index.html`:

```html
<!-- Line ~81 -->
<a href="https://github.com/yourusername/qr_ec_stego" target="_blank">
```

And in the main `README.md`:

```markdown
- **Live Demo**: [GitHub Pages](https://yourusername.github.io/qr_ec_stego/)
- **Repository**: [GitHub](https://github.com/yourusername/qr_ec_stego)
```

## Custom Domain (Optional)

### Step 1: Add CNAME File

Create `docs/CNAME` with your domain:
```
qrstego.yourdomain.com
```

### Step 2: Configure DNS

Add a CNAME record pointing to:
```
yourusername.github.io
```

### Step 3: Update GitHub Settings

- Go to Settings → Pages
- Add your custom domain
- Enable "Enforce HTTPS"

## Verifying Deployment

1. **Check the Live Site**: Visit your GitHub Pages URL
2. **Test Features**:
   - Try generating a QR code in the Encode tab
   - Upload an example image in the Decode tab
   - Compare two QR codes in the Compare tab
3. **Check Browser Console**: Open DevTools (F12) and check for errors

## Troubleshooting

### Issue: Page shows 404

**Solution**:
- Make sure you selected `/docs` folder in GitHub Pages settings
- Wait a few minutes for deployment to complete
- Check that `index.html` exists in the `docs/` folder

### Issue: QR generation not working

**Solution**:
- Check browser console for JavaScript errors
- Make sure external libraries are loading (qrcode, jsQR)
- Try a different browser
- Check internet connection (CDN libraries need to load)

### Issue: Example images not loading

**Solution**:
- Make sure `docs/examples/` folder contains:
  - `challenge1.png`
  - `challenge2.png`
- Check image paths in `app.js`

### Issue: Styles look broken

**Solution**:
- Check that Tailwind CSS is loading from CDN
- Try clearing browser cache
- Check browser console for CSS loading errors

## Performance Optimization

### Current Setup (CDN)
- ✅ Fast deployment
- ✅ No build step needed
- ✅ Always uses latest library versions
- ⚠️ Requires internet connection

### Alternative: Self-Hosted Libraries

If you want the tool to work offline:

1. Download libraries:
   - Tailwind CSS (or compile custom build)
   - qrcode-generator library
   - jsQR library

2. Update script tags in `index.html`:
```html
<!-- Change from CDN to local -->
<script src="js/vendor/qrcode.min.js"></script>
<script src="js/vendor/jsQR.min.js"></script>
```

3. Create a build process if using Tailwind:
```bash
npm install -D tailwindcss
npx tailwindcss -i input.css -o output.css --minify
```

## Security Considerations

### GitHub Pages Limitations

- ✅ Static files only (perfect for this tool)
- ✅ HTTPS by default
- ✅ Free hosting
- ⚠️ Public repositories only (for free tier)
- ⚠️ All processing happens client-side (which is good for privacy!)

### Privacy Features

The web tool:
- ✅ No data sent to servers (all processing is client-side)
- ✅ No tracking or analytics
- ✅ No cookies
- ✅ Works offline (once loaded)

### Content Security

If you want to add CSP headers, use a service like Cloudflare Pages instead of GitHub Pages, or add meta tags:

```html
<meta http-equiv="Content-Security-Policy"
      content="default-src 'self';
               script-src 'self' 'unsafe-inline' cdn.tailwindcss.com cdn.jsdelivr.net;
               style-src 'self' 'unsafe-inline';">
```

## Monitoring

### GitHub Actions (Optional)

Create `.github/workflows/deploy.yml` for automated testing:

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Validate HTML
        run: |
          # Add HTML validation
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs
```

## Updating the Site

```bash
# Make changes to files in docs/
git add docs/
git commit -m "Update web tool"
git push

# GitHub Pages will automatically rebuild (takes ~1-2 minutes)
```

## Backup and Versioning

The entire site is version controlled with git, so:
- Every change is tracked
- Easy to roll back if needed
- No separate backup needed

## Alternative Hosting

### Netlify

1. Create account at netlify.com
2. Drag and drop the `docs/` folder
3. Custom domain and HTTPS included

### Vercel

1. Install Vercel CLI: `npm i -g vercel`
2. Run: `vercel docs/`
3. Follow prompts

### Cloudflare Pages

1. Connect GitHub repository
2. Build settings:
   - Build command: (none)
   - Publish directory: `docs`
3. Deploy

All of these provide:
- Faster CDN
- Better analytics
- More deployment options
- Free tier available

## Support

If you encounter issues:
1. Check the browser console for errors
2. Verify all files are present in `docs/`
3. Test locally first with Python server
4. Check GitHub Pages build logs

---

Your web tool is ready to deploy! 🚀
