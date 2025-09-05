# Password Manager Browser Extension

This extension provides seamless integration between your Password Manager and web browsers, enabling auto-fill and save functionality for login forms.

## Supported Browsers

- Google Chrome
- Mozilla Firefox
- Opera
- Microsoft Edge (Chromium-based)

## Features

- Auto-fill login forms with saved credentials
- Save new logins with a single click
- Secure communication with the Password Manager application
- Cross-browser compatibility

## Installation

### Prerequisites

- Node.js (v14 or later)
- npm or yarn
- Password Manager application installed and running

### Building the Extension

1. Install dependencies:
   ```bash
   npm install
   ```

2. Build the extension for all supported browsers:
   ```bash
   npm run build
   ```

   This will create browser-specific builds in the `build` directory.

### Loading the Extension

#### Google Chrome / Microsoft Edge

1. Open the browser and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in the top-right corner)
3. Click "Load unpacked" and select the `build/chrome` directory

#### Mozilla Firefox

1. Open Firefox and navigate to `about:debugging#/runtime/this-firefox`
2. Click "Load Temporary Add-on"
3. Select the `manifest.json` file from the `build/firefox` directory

#### Opera

1. Open Opera and navigate to `opera://extensions/`
2. Enable "Developer mode" (toggle in the top-left corner)
3. Click "Load unpacked" and select the `build/opera` directory

## Development

### Project Structure

- `background.js` - Background script for extension
- `content.js` - Content script injected into web pages
- `popup/` - Popup UI components
- `icons/` - Extension icons
- `manifest.json` - Extension manifest

### Development Commands

- `npm run build` - Build the extension for all browsers
- `npm run build:chrome` - Build for Chrome only
- `npm run build:firefox` - Build for Firefox only
- `npm run build:opera` - Build for Opera only
- `npm run watch` - Watch for changes and rebuild automatically

## Security

- All communication between the extension and the Password Manager application is encrypted
- Credentials are never stored in the browser's storage
- The extension requires explicit user permission to access form data

## Troubleshooting

### Extension not connecting to the application

1. Ensure the Password Manager application is running
2. Check that the native messaging host is properly installed
3. Verify that the extension has the necessary permissions

### Auto-fill not working on a website

Some websites use custom form implementations that may not be automatically detected. You can report these sites by opening an issue in the repository.

## License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.
