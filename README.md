# ![Password Manager](assets/logo.png) Password Manager

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![GitHub release](https://img.shields.io/github/v/release/Nsfr750/pass_mgr)](https://github.com/Nsfr750/pass_mgr/releases)

A secure, open-source password manager with advanced security features and cross-platform support.

## ✨ Features

- 🔒 **Military-Grade Encryption**: AES-256 encryption for your sensitive data
- 🔑 **Master Password Protection**: Single master password to access all your credentials
- 🌐 **Cross-Platform**: Works on Windows, macOS, and Linux
- 🔄 **Password Generator**: Create strong, random passwords with customizable options
- 📋 **Clipboard Management**: Auto-clear clipboard after copying passwords
- 🔍 **Advanced Search**: Quickly find your credentials with powerful search and filtering
- 🏷️ **Categories & Tags**: Organize your passwords with custom categories and tags
- 📂 **Import/Export**: Securely import from and export to various formats
- 🔄 **Auto-Backup**: Automatic backups of your password database
- 📊 **Password Strength Analysis**: Get insights into your password security
- 🌐 **Browser Extension**: Auto-fill and save passwords in Chrome, Firefox, and Opera
- 🎨 **Themes**: Light and dark mode support

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git (optional, for development version)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/Nsfr750/pass_mgr.git
   cd pass_mgr
   ```

2. Create and activate a virtual environment:

   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:

   ```bash
   python main.py
   ```

## 📖 Documentation

- [User Guide](docs/User_Guide.md) - Comprehensive guide to using the Password Manager
- [Project Structure](docs/struct.md) - Overview of the codebase structure

## 🤝 Contributing

Contributions are welcome! Please read our [contributing guidelines](docs/CONTRIBUTING.md) before submitting pull requests.

## 📄 License

This project is licensed under the GPLv3 License - see the [LICENSE](LICENSE) file for details.

## 💖 Support

If you find this project useful, consider supporting its development:

- [GitHub Sponsors](https://github.com/sponsors/Nsfr750)
- [Patreon](https://www.patreon.com/Nsfr750)
- [PayPal](https://paypal.me/3dmega)
- Monero: `47Jc6MC47WJVFhiQFYwHyBNQP5BEsjUPG6tc8R37FwcTY8K5Y3LvFzveSXoGiaDQSxDrnCUBJ5WBj6Fgmsfix8VPD4w3gXF`

## 📬 Contact

- GitHub: [@Nsfr750](https://github.com/Nsfr750)
- Email: [Nsfr750](mailto:nsfr750@yandex.com)
- Discord: [Join our community](https://discord.gg/ryqNeuRYjD)

## Importing Passwords

### From LastPass

1. Export your LastPass data as CSV
2. Go to File > Import > From LastPass
3. Select the exported CSV file

### From Chrome

1. Go to chrome://settings/passwords
2. Click the three dots menu and select "Export passwords"
3. Go to File > Import > From Chrome
4. Select the exported CSV file

### From Firefox

1. Open Firefox and go to about:logins
2. Click the three dots menu and select "Export Logins"
3. Go to File > Import > From Firefox
4. Select the exported JSON file

## Security

- All passwords are encrypted before being stored
- The master password is never stored
- The application uses secure encryption algorithms

## License

GPLv3 - © 2025 Nsfr750 - All rights reserved

## Support

For support, please open an issue on GitHub
