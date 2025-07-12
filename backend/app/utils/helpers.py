from decimal import Decimal
from datetime import datetime, date
import hashlib
import os

def format_currency(amount):
    """Format amount as currency string"""
    return f"${amount:,.2f}"

def safe_decimal(value, default=0.0):
    """Safely convert value to Decimal"""
    try:
        return Decimal(str(value))
    except (ValueError, TypeError):
        return Decimal(str(default))

def generate_file_hash(file_path):
    """Generate MD5 hash of file contents"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def ensure_directory_exists(path):
    """Create directory if it doesn't exist"""
    os.makedirs(path, exist_ok=True)

def validate_date_range(start_date, end_date):
    """Validate that start_date is before end_date"""
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    return start_date <= end_date

def sanitize_filename(filename):
    """Remove potentially dangerous characters from filename"""
    import re
    # Remove path separators and other dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Limit length
    filename = filename[:255]
    return filename