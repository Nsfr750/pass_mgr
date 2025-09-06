import sys
import sqlite3
import base64
import logging
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a key from a password using PBKDF2."""
    logger.debug(f"Deriving key with salt (first 16 bytes): {salt[:16].hex()}")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 256 bits
        salt=salt,
        iterations=600000,
    )
    key = kdf.derive(password.encode('utf-8'))
    logger.debug(f"Derived key (first 16 bytes): {key[:16].hex()}")
    return key

def decrypt_data(encrypted_data: bytes, nonce: bytes, key: bytes) -> str:
    """Decrypt data using AES-GCM."""
    logger.debug(f"Decrypting data - Length: {len(encrypted_data)}, Nonce: {nonce.hex()}")
    try:
        aesgcm = AESGCM(key)
        decrypted = aesgcm.decrypt(nonce[:12], encrypted_data, None)
        logger.debug(f"Successfully decrypted data, length: {len(decrypted)}")
        return decrypted.decode('utf-8')
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        logger.debug(f"Encrypted data (hex): {encrypted_data.hex()}")
        logger.debug(f"Nonce (hex): {nonce.hex()}")
        raise

def test_decrypt():
    db_path = Path("X:/GitHub/pass_mgr/data/passwords.db")
    
    try:
        logger.info(f"Connecting to database at {db_path}")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()
        
        # Get the salt from metadata
        logger.debug("Fetching salt from metadata")
        cursor.execute("SELECT value FROM metadata WHERE key = 'password_salt'")
        salt_result = cursor.fetchone()
        if not salt_result:
            logger.error("No salt found in the database")
            return
            
        salt = salt_result[0]
        if isinstance(salt, str):
            salt = base64.b64decode(salt)
        
        logger.info(f"Salt (first 16 bytes): {salt[:16].hex()}")
        
        # Get master password from user
        master_password = input("Enter master password: ").strip()
        if not master_password:
            logger.error("No password provided")
            return
            
        # Derive the key
        logger.info("Deriving master key...")
        master_key = derive_key(master_password, salt)
        logger.info(f"Master key derived (first 16 bytes): {master_key[:16].hex()}")
        
        # First, check the database structure
        logger.info("Checking database structure...")
        cursor.execute("PRAGMA table_info(passwords)")
        columns = [col[1] for col in cursor.fetchall()]
        logger.info(f"Password table columns: {', '.join(columns)}")
        
        # Get all password entries with all fields
        logger.info("Fetching all password entries...")
        cursor.execute('SELECT * FROM passwords')
        entries = cursor.fetchall()
        
        if not entries:
            logger.error("No password entries found in the database.")
            return
            
        logger.info(f"Found {len(entries)} entries to test")
        
        # Print summary of entries
        print("\n=== Database Summary ===")
        print(f"Total entries: {len(entries)}")
        print("\nFirst few entries:")
        
        # Check first 5 entries in detail
        for i, entry in enumerate(entries[:5]):
            entry_dict = dict(zip(columns, entry))
            entry_id = entry_dict.get('id', 'N/A')
            title = entry_dict.get('title', 'N/A')
            username = entry_dict.get('username', 'N/A')
            has_encrypted = 'password_encrypted' in entry_dict and entry_dict['password_encrypted'] is not None
            has_iv = 'iv' in entry_dict and entry_dict['iv'] is not None
            has_plain = 'password' in entry_dict and entry_dict['password'] is not None
            
            print(f"\n--- Entry {i+1} ---")
            print(f"ID: {entry_id}")
            print(f"Title: {title}")
            print(f"Username: {username}")
            print(f"Has encrypted password: {has_encrypted}")
            print(f"Has IV: {has_iv}")
            print(f"Has plain password: {has_plain}")
            
            # Try to decrypt if we have the required fields
            if has_encrypted and has_iv:
                try:
                    encrypted_data = entry_dict['password_encrypted']
                    iv = entry_dict['iv']
                    logger.debug(f"Encrypted data (first 16 bytes): {encrypted_data[:16].hex()}")
                    logger.debug(f"IV (first 16 bytes): {iv[:16].hex()}")
                    
                    decrypted = decrypt_data(encrypted_data, iv, master_key)
                    print(f"Decrypted password: {decrypted}")
                    print(f"Password length: {len(decrypted)} characters")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to decrypt entry {entry_id}: {str(e)}")
            else:
                print("Skipping decryption - missing required fields")
                if has_plain:
                    print(f"Plain password: {entry_dict['password']}")
        
        # Count entries with/without encrypted passwords
        cursor.execute("SELECT COUNT(*) FROM passwords WHERE password_encrypted IS NOT NULL AND iv IS NOT NULL")
        encrypted_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM passwords WHERE password_encrypted IS NULL OR iv IS NULL")
        missing_encryption = cursor.fetchone()[0]
        
        # Find entries with empty decrypted passwords
        empty_password_entries = []
        for entry in entries:
            entry_dict = dict(zip(columns, entry))
            if 'password_encrypted' in entry_dict and 'iv' in entry_dict and entry_dict['password_encrypted'] and entry_dict['iv']:
                try:
                    decrypted = decrypt_data(entry_dict['password_encrypted'], entry_dict['iv'], master_key)
                    if not decrypted or decrypted.strip() == '':
                        empty_password_entries.append({
                            'id': entry_dict.get('id', 'N/A'),
                            'title': entry_dict.get('title', 'N/A'),
                            'username': entry_dict.get('username', 'N/A'),
                            'encrypted_length': len(entry_dict['password_encrypted']),
                            'iv_length': len(entry_dict['iv'])
                        })
                except Exception as e:
                    logger.warning(f"Error checking entry {entry_dict.get('id', 'unknown')}: {e}")
        
        print("\n=== Encryption Status ===")
        print(f"Total entries: {len(entries)}")
        print(f"Entries with encrypted passwords: {encrypted_count}")
        print(f"Entries missing encryption: {missing_encryption}")
        print(f"\nEntries with empty/blank decrypted passwords: {len(empty_password_entries)}")
        
        if empty_password_entries:
            print("\n=== Entries with Empty/Blank Passwords ===")
            for i, entry in enumerate(empty_password_entries[:10], 1):  # Show first 10 for brevity
                print(f"{i}. ID: {entry['id']}, Title: {entry['title']}, Username: {entry['username']}, "
                      f"Encrypted Len: {entry['encrypted_length']}, IV Len: {entry['iv_length']}")
            if len(empty_password_entries) > 10:
                print(f"... and {len(empty_password_entries) - 10} more")
        
        # Check for entries with very short encrypted data (potential issues)
        suspicious_entries = []
        for entry in entries:
            entry_dict = dict(zip(columns, entry))
            if 'password_encrypted' in entry_dict and entry_dict['password_encrypted']:
                enc_len = len(entry_dict['password_encrypted'])
                if enc_len < 8:  # AES-GCM encrypted data should typically be longer
                    suspicious_entries.append({
                        'id': entry_dict.get('id', 'N/A'),
                        'title': entry_dict.get('title', 'N/A'),
                        'encrypted_length': enc_len,
                        'iv_length': len(entry_dict.get('iv', ''))
                    })
        
        if suspicious_entries:
            print("\n=== Suspicious Entries (Very Short Encrypted Data) ===")
            for entry in suspicious_entries:
                print(f"ID: {entry['id']}, Title: {entry['title']}, "
                      f"Encrypted Len: {entry['encrypted_length']}, IV Len: {entry['iv_length']}")
        
        # Check for potential encoding issues
        print("\n=== Password Length Analysis ===")
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN LENGTH(password_encrypted) = 0 THEN 1 ELSE 0 END) as empty_encrypted,
                SUM(CASE WHEN LENGTH(iv) = 0 THEN 1 ELSE 0 END) as empty_iv,
                AVG(LENGTH(password_encrypted)) as avg_encrypted_len,
                MIN(LENGTH(password_encrypted)) as min_encrypted_len,
                MAX(LENGTH(password_encrypted)) as max_encrypted_len
            FROM passwords
        """)
        stats = cursor.fetchone()
        print(f"Total entries: {stats[0]}")
        print(f"Entries with empty encrypted data: {stats[1]}")
        print(f"Entries with empty IV: {stats[2]}")
        print(f"Average encrypted data length: {stats[3]:.2f} bytes")
        print(f"Minimum encrypted data length: {stats[4]} bytes")
        print(f"Maximum encrypted data length: {stats[5]} bytes")
                
        logger.info("Test completed")
                
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    test_decrypt()
