#!/usr/bin/env python3
"""
Test script to read the Chrome passwords CSV file.
"""
import csv
import os
from pathlib import Path

def test_csv_read(file_path):
    """Test reading the CSV file and print the first few rows."""
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"❌ Error: File not found: {file_path}")
            return False
        
        print(f"✅ File found: {file_path}")
        print(f"   Size: {os.path.getsize(file_path) / 1024:.2f} KB")
        
        # Try to read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            # Check if the file is not empty
            first_line = f.readline().strip()
            if not first_line:
                print("❌ Error: File is empty")
                return False
                
            print("\nFirst line of the file:")
            print(first_line)
            
            # Try to parse as CSV
            f.seek(0)  # Go back to the start of the file
            reader = csv.reader(f)
            headers = next(reader, None)
            
            if not headers:
                print("❌ Error: Could not read CSV headers")
                return False
                
            print("\nCSV Headers:")
            print(", ".join(headers))
            
            # Read first few rows
            print("\nFirst 5 rows of data:")
            for i, row in enumerate(reader):
                if i >= 5:  # Only show first 5 rows
                    break
                print(f"Row {i+1}: {row}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = input("Enter path to CSV file: ").strip('"')
    
    print(f"\nTesting file: {file_path}")
    test_csv_read(file_path)
