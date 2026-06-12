# Deploy Xerax Root at xeraxapp.com/root/

The production domain currently returns `404` for `/root/`. The generated upload
bundle is `deploy/xerax-root`.

## Release order

1. Run `companion/build.ps1 -Clean`.
2. Sign `dist/XeraxRootCompanion.exe` with:

   ```powershell
   .\companion\sign.ps1 -Thumbprint YOUR_CERTIFICATE_THUMBPRINT
   ```

3. Run `companion/deploy.ps1`.
4. Upload the contents of `deploy/xerax-root` to the website directory mapped to
   `https://xeraxapp.com/root/`.
5. Ensure the `_headers` rules are applied by Cloudflare Pages or reproduce the
   same headers in the active origin/Worker configuration.
6. Purge only `/root/release.json` and `/root/index.html` from Cloudflare cache.
   Versioned executables may remain immutable.

## Production checks

- `https://xeraxapp.com/root/` returns `200`.
- `https://xeraxapp.com/root/release.json` returns valid JSON and `Cache-Control:
  no-store`.
- The executable URL returns the exact byte count and SHA-256 in `release.json`.
- Windows Authenticode reports a valid Xerax publisher and timestamp.
- The page can connect to `http://127.0.0.1:47721` after entering the pairing code.
- The console reports both `adb` and `fastboot` before device operations begin.
- A physical test device completes detect, validate, flash, reboot, and root
  verification before its product identifier is added as a tested profile.

Do not publish an unsigned preview executable as a production download.
