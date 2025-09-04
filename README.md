# Password Manager

A secure password manager with import capabilities from various sources.

## Features

- **Secure Storage**: Store your passwords in an encrypted database
- **Import from Multiple Sources**:
  - LastPass
  - Google Chrome
  - Mozilla Firefox
  - Google Account
- **User-Friendly Interface**: Sortable columns, search, and filtering
- **Secure**: Passwords are encrypted at rest

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/Nsfr750/pass_mgr.git
   cd pass_mgr
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # On Windows
   source venv/bin/activate  # On macOS/Linux
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the application:

```bash
python main.py
```

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

## Donate

If you find this project useful, consider supporting me:

- [PayPal](https://paypal.me/3dmega)
- [Patreon](https://www.patreon.com/Nsfr750)
- Monero: `47Jc6MC47WJVFhiQFYwHyBNQP5BEsjUPG6tc8R37FwcTY8K5Y3LvFzveSXoGiaDQSxDrnCUBJ5WBj6Fgmsfix8VPD4w3gXF`
