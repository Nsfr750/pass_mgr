# Database Setup Guide

This guide will help you set up a new database and import your Chrome passwords.

## Prerequisites

1. Python 3.7 or higher
2. Required Python packages (install with `pip install -r requirements.txt`)
3. Chrome passwords exported to CSV (see instructions below)

## Step 1: Create a New Database

Run the following command to create a new database with the correct schema:

```bash
python scripts/create_new_database.py
```

This will:
- Create a backup of your existing database (if any)
- Create a new database with the correct schema
- Print the location of the new database

## Step 2: Export Chrome Passwords

1. Open Chrome and go to `chrome://settings/passwords`
2. Click the three dots (⋮) next to "Saved Passwords"
3. Select "Export passwords..."
4. Save the file as `chrome_passwords.csv` in your Downloads folder

## Step 3: Import Chrome Passwords

Run the import script:

```bash
python scripts/import_chrome_passwords.py
```

If your Chrome passwords CSV is not in the default location, you can specify the path:

```bash
python scripts/import_chrome_passwords.py /path/to/your/chrome_passwords.csv
```

## Step 4: Verify the Import

After importing, you can run the main application to verify that your passwords were imported correctly:

```bash
python main.py
```

## Troubleshooting

### Common Issues

1. **Database not found**: Make sure you ran `create_new_database.py` first
2. **Import errors**: Check that the CSV file is in the correct format
3. **Permission issues**: Make sure the script has permission to read the CSV file and write to the database

### Getting Help

If you encounter any issues, please check the following:
- The database file exists at `data/passwords.db`
- The CSV file is not corrupted
- You have the latest version of the code

For additional help, please open an issue on GitHub.

## Security Note

- Always keep your database and master password secure
- Delete the Chrome passwords CSV file after importing
- Use a strong master password
- Regularly back up your database
