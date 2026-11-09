# StockVision AI barcode scanner

This guide explains how barcode reading works in the browser, where its code lives, and how the receiving and cashier workflows use a scanned code.

## Scanner behavior

Barcode decoding runs in the **frontend browser** with ZXing. The camera image and optional uploaded barcode image are processed locally; there is no barcode-decoding API request to the backend.

The scanner recognizes these retail formats:

- EAN-13
- EAN-8
- UPC-A
- UPC-E

### Camera flow

1. On Stock receiving, select **Scan Barcode**. On Point of sale, select **Scan Product**.
2. The browser requests camera access. The user must allow permission.
3. The scanner opens a live video stream using `navigator.mediaDevices.getUserMedia`. It requests an ideal resolution of 1920 × 1080; the browser and camera may choose a different supported resolution.
4. If available, the scanner requests continuous autofocus. The camera selector, zoom slider, and light/torch button appear only when supported by the camera.
5. ZXing repeatedly decodes a crop from the center of the video, aligned with the visible scan guide. It tries again about every 180 milliseconds until it finds a barcode.
6. When a code is detected, the app displays it and stops the camera stream. Select **Use barcode** to confirm the result, or **Close scanner** to cancel.
7. Camera access requires a secure browser context: `localhost`/`127.0.0.1` during local development, or HTTPS when hosted. Browser permission and camera availability are required.

### Upload-image flow

Select **Upload image** in the scanner dialog to test from a JPG, PNG, or WebP barcode image. ZXing first tries the image directly. If needed, the browser retries rotated, enlarged, grayscale/high-contrast versions. The image is processed locally and is **not uploaded to the application server**. Select **Use barcode** after a code is detected.

### Manual-entry flow

The receiving and POS screens also have a barcode text field. Manual entry is separate from the camera scanner:

- **Stock receiving:** enter a barcode and select **Find product**. The frontend calls `GET /api/products/barcode/{barcode}`. An existing product is shown; an unknown barcode opens the registration form. Stock changes only after the user enters a quantity and confirms **Add Stock**.
- **Point of sale:** enter a barcode and select **Add** or press Enter. The frontend finds it in the loaded product list, checks available stock, and adds one unit to the cart. Inventory is reduced only after the cashier confirms the sale.

Scanning or looking up a code never increases or decreases inventory by itself.

## Source files

| File | Responsibility |
|---|---|
| [`frontend/src/components/BarcodeScanner.tsx`](./frontend/src/components/BarcodeScanner.tsx) | Reusable scanner dialog: ZXing formats/hints, live camera lifecycle, video-frame crop decoding, camera controls, barcode-image decoding, detected-code confirmation, and cleanup. |
| [`frontend/src/App.tsx`](./frontend/src/App.tsx) | Opens the scanner from receiving and POS, receives the confirmed barcode, performs product lookup or cart addition, and enforces the respective workflow. |
| [`frontend/src/api.ts`](./frontend/src/api.ts) | Typed `productByBarcode` request used by stock receiving. |
| [`frontend/src/App.css`](./frontend/src/App.css) | Scanner modal, camera preview, scan guide, camera controls, and responsive styling. |
| [`frontend/package.json`](./frontend/package.json) | Declares `@zxing/browser` and `@zxing/library`, the browser barcode-decoding libraries. |
| [`frontend/vite.config.js`](./frontend/vite.config.js) | Proxies `/api` requests to FastAPI during local development; decoding itself happens in the browser. |
| [`backend/app/routers/entries.py`](./backend/app/routers/entries.py) | Backend product-by-barcode lookup used after scanning on the receiving screen. |

The reusable scanner receives two callbacks: `onDetected(barcode)` when the user confirms a detected code, and `onClose()` when the dialog is dismissed. Its caller decides what to do with that code.

## Scanning tips and troubleshooting

- Center the entire barcode, including the blank margins at either end, in the on-screen guide.
- Keep the code steady and horizontal, use even lighting, avoid glare, and move closer until the bars are sharp.
- If the camera does not open, allow camera permission in browser site settings and reopen the scanner. Confirm that another application is not exclusively using the camera.
- If the wrong camera is active, select another listed camera. Zoom and light controls are hardware-dependent.
- If live scanning cannot read the code, use **Upload image** with a sharp photo or type the barcode in the manual-entry field.
- To test the camera itself, open the app in a browser on the machine with the camera and test with a printed retail barcode. Automated backend tests do not test physical camera hardware.

## Dependencies and checks

From `frontend`, install packages and run the existing checks:

```powershell
npm install
npm run typecheck
npm run build
```

For camera testing, run the backend and frontend using the setup instructions in the [main README](./README.md), open the local Vite URL, and test from Stock receiving or POS.
