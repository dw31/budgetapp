import pandas as pd
import hashlib
from datetime import datetime
from ..models import db, Transaction, UploadHistory
import uuid
import re

class CSVProcessor:
    def __init__(self):
        self.supported_formats = {
            'chase': {
                'date_col': 'Transaction Date',
                'description_col': 'Description',
                'amount_col': 'Amount',
                'date_format': '%m/%d/%Y'
            },
            'bank_of_america': {
                'date_col': 'Date',
                'description_col': 'Description',
                'amount_col': 'Amount',
                'date_format': '%m/%d/%Y'
            },
            'wells_fargo': {
                'date_col': 'Date',
                'description_col': 'Description',
                'amount_col': 'Amount',
                'date_format': '%m/%d/%Y'
            },
            'generic': {
                'date_col': 'date',
                'description_col': 'description',
                'amount_col': 'amount',
                'date_format': '%Y-%m-%d'
            }
        }
    
    def process_csv(self, file_path, account_id, user_id, file_format='generic'):
        """Process CSV file and import transactions"""
        upload_history = UploadHistory(
            user_id=user_id,
            account_id=account_id,
            filename=file_path,
            status='processing'
        )
        db.session.add(upload_history)
        db.session.commit()
        
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            upload_history.total_rows = len(df)
            
            # Get format configuration
            format_config = self.supported_formats.get(file_format, self.supported_formats['generic'])
            
            # Process transactions
            processed_count = 0
            error_count = 0
            batch_id = uuid.uuid4()
            
            # Process transactions in batches for better error handling
            batch_size = 100
            current_batch = 0
            
            for index, row in df.iterrows():
                try:
                    transaction_data = self._extract_transaction_data(row, format_config)
                    transaction_data['account_id'] = account_id
                    transaction_data['upload_batch_id'] = str(batch_id)
                    
                    # Generate hash key (but don't check for duplicates)
                    hash_key = self._generate_hash(transaction_data)
                    
                    transaction_data['hash_key'] = hash_key
                    
                    # Create transaction with no category (uncategorized by default)
                    transaction = Transaction(**transaction_data)
                    transaction.category_id = None
                    transaction.category_confidence = 0.0
                    transaction.is_manually_categorized = False
                    
                    # Initialize recurring transaction fields (if they exist)
                    if hasattr(transaction, 'is_recurring'):
                        transaction.is_recurring = False
                    if hasattr(transaction, 'recurring_pattern_id'):
                        transaction.recurring_pattern_id = None
                    
                    db.session.add(transaction)
                    processed_count += 1
                    current_batch += 1
                    
                    # Commit in batches to avoid large transactions
                    if current_batch >= batch_size:
                        try:
                            db.session.commit()
                            current_batch = 0
                        except Exception as commit_error:
                            print(f"Error committing batch at row {index}: {commit_error}")
                            db.session.rollback()
                            # Continue processing but don't count this batch
                            processed_count -= current_batch
                            error_count += current_batch
                            current_batch = 0
                    
                except Exception as e:
                    error_count += 1
                    print(f"Error processing row {index}: {e}")
                    # Don't let individual row errors corrupt the session
                    if current_batch > 0:
                        try:
                            db.session.rollback()
                        except:
                            pass
                        current_batch = 0
            
            # Commit any remaining transactions
            if current_batch > 0:
                try:
                    db.session.commit()
                except Exception as commit_error:
                    print(f"Error committing final batch: {commit_error}")
                    db.session.rollback()
                    processed_count -= current_batch
                    error_count += current_batch
            
            # Update upload history
            upload_history.processed_rows = processed_count
            upload_history.duplicate_rows = 0  # No longer tracking duplicates
            upload_history.error_rows = error_count
            upload_history.status = 'completed'
            upload_history.completed_at = datetime.utcnow()
            db.session.commit()
            
            return {
                'success': True,
                'processed': processed_count,
                'duplicates': 0,  # No longer skipping duplicates
                'errors': error_count,
                'batch_id': str(batch_id)
            }
            
        except Exception as e:
            # Rollback the session to clear any pending transactions
            db.session.rollback()
            
            # Update upload history in a new transaction
            upload_history.status = 'failed'
            upload_history.error_message = str(e)
            try:
                db.session.commit()
            except Exception as commit_error:
                print(f"Failed to update upload history: {commit_error}")
                db.session.rollback()
            
            return {'success': False, 'error': str(e)}
    
    def _extract_transaction_data(self, row, format_config):
        """Extract transaction data from CSV row"""
        date_str = str(row[format_config['date_col']])
        date_obj = datetime.strptime(date_str, format_config['date_format']).date()
        
        amount = float(row[format_config['amount_col']])
        description = str(row[format_config['description_col']])
        
        return {
            'date': date_obj,
            'description': description,
            'amount': amount,
            'merchant': self._extract_merchant(description)
        }
    
    def _extract_merchant(self, description):
        """Extract merchant name from transaction description"""
        # Simple merchant extraction logic
        words = description.split()
        return words[0] if words else description
    
    def _generate_hash(self, transaction_data):
        """Generate hash for duplicate detection"""
        hash_string = f"{transaction_data['date']}{transaction_data['description']}{transaction_data['amount']}"
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def generate_preview(self, file_path, mappings, account_id, preview_rows=10):
        """Generate preview data with user mappings"""
        try:
            df = pd.read_csv(file_path)
            
            preview_data = {
                'total_rows': len(df),
                'sample_transactions': [],
                'mapping_summary': {},
                'warnings': []
            }
            
            # Process sample rows
            sample_size = min(preview_rows, len(df))
            for i in range(sample_size):
                row = df.iloc[i]
                try:
                    transaction_data = self._extract_transaction_from_mapping(row, mappings)
                    preview_data['sample_transactions'].append({
                        'row_number': i + 1,
                        'date': str(transaction_data['date']),
                        'description': transaction_data['description'],
                        'amount': transaction_data['amount'],
                        'merchant': transaction_data.get('merchant', ''),
                        'category': transaction_data.get('category', ''),
                        'reference_number': transaction_data.get('reference_number', '')
                    })
                except Exception as e:
                    preview_data['warnings'].append(f"Row {i+1}: {str(e)}")
            
            # Generate mapping summary
            for field, column in mappings.items():
                if column in df.columns:
                    non_empty_count = df[column].notna().sum()
                    preview_data['mapping_summary'][field] = {
                        'source_column': column,
                        'non_empty_rows': int(non_empty_count),
                        'empty_rows': int(len(df) - non_empty_count),
                        'sample_values': df[column].dropna().head(3).tolist()
                    }
            
            return preview_data
            
        except Exception as e:
            raise Exception(f"Preview generation failed: {str(e)}")
    
    def process_csv_with_mappings(self, file_path, mappings, account_id, user_id):
        """Process CSV file with user-defined mappings"""
        upload_history = UploadHistory(
            user_id=user_id,
            account_id=account_id,
            filename=file_path,
            status='processing'
        )
        db.session.add(upload_history)
        db.session.commit()
        
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            upload_history.total_rows = len(df)
            
            # Process transactions
            processed_count = 0
            error_count = 0
            batch_id = uuid.uuid4()
            
            # Process transactions in batches for better error handling
            batch_size = 100
            current_batch = 0
            
            for index, row in df.iterrows():
                try:
                    transaction_data = self._extract_transaction_from_mapping(row, mappings)
                    transaction_data['account_id'] = account_id
                    transaction_data['upload_batch_id'] = str(batch_id)
                    
                    # Generate hash key (but don't check for duplicates)
                    hash_key = self._generate_hash(transaction_data)
                    
                    transaction_data['hash_key'] = hash_key
                    
                    # Create transaction with no category (uncategorized by default)
                    transaction = Transaction(**transaction_data)
                    transaction.category_id = None
                    transaction.category_confidence = 0.0
                    transaction.is_manually_categorized = False
                    
                    # Initialize recurring transaction fields (if they exist)
                    if hasattr(transaction, 'is_recurring'):
                        transaction.is_recurring = False
                    if hasattr(transaction, 'recurring_pattern_id'):
                        transaction.recurring_pattern_id = None
                    
                    db.session.add(transaction)
                    processed_count += 1
                    current_batch += 1
                    
                    # Commit in batches to avoid large transactions
                    if current_batch >= batch_size:
                        try:
                            db.session.commit()
                            current_batch = 0
                        except Exception as commit_error:
                            print(f"Error committing batch at row {index}: {commit_error}")
                            db.session.rollback()
                            # Continue processing but don't count this batch
                            processed_count -= current_batch
                            error_count += current_batch
                            current_batch = 0
                    
                except Exception as e:
                    error_count += 1
                    print(f"Error processing row {index}: {e}")
                    # Don't let individual row errors corrupt the session
                    if current_batch > 0:
                        try:
                            db.session.rollback()
                        except:
                            pass
                        current_batch = 0
            
            # Commit any remaining transactions
            if current_batch > 0:
                try:
                    db.session.commit()
                except Exception as commit_error:
                    print(f"Error committing final batch: {commit_error}")
                    db.session.rollback()
                    processed_count -= current_batch
                    error_count += current_batch
            
            # Update upload history
            upload_history.processed_rows = processed_count
            upload_history.duplicate_rows = 0  # No longer tracking duplicates
            upload_history.error_rows = error_count
            upload_history.status = 'completed'
            upload_history.completed_at = datetime.utcnow()
            db.session.commit()
            
            return {
                'success': True,
                'processed': processed_count,
                'duplicates': 0,  # No longer skipping duplicates
                'errors': error_count,
                'batch_id': str(batch_id)
            }
            
        except Exception as e:
            # Rollback the session to clear any pending transactions
            db.session.rollback()
            
            # Update upload history in a new transaction
            upload_history.status = 'failed'
            upload_history.error_message = str(e)
            try:
                db.session.commit()
            except Exception as commit_error:
                print(f"Failed to update upload history: {commit_error}")
                db.session.rollback()
            
            return {'success': False, 'error': str(e)}
    
    def _extract_transaction_from_mapping(self, row, mappings):
        """Extract transaction data using user-defined mappings"""
        transaction_data = {}
        
        # Extract date
        if 'date' in mappings:
            date_str = str(row[mappings['date']])
            transaction_data['date'] = self._parse_date(date_str)
        
        # Extract description
        if 'description' in mappings:
            transaction_data['description'] = str(row[mappings['description']])
        
        # Extract amount
        if 'amount' in mappings:
            amount_str = str(row[mappings['amount']])
            transaction_data['amount'] = self._parse_amount(amount_str)
        
        # Extract optional fields
        if 'merchant' in mappings and mappings['merchant']:
            transaction_data['merchant'] = str(row[mappings['merchant']])
        else:
            transaction_data['merchant'] = self._extract_merchant(transaction_data.get('description', ''))
        
        if 'category' in mappings and mappings['category']:
            transaction_data['category'] = str(row[mappings['category']])
        
        if 'reference_number' in mappings and mappings['reference_number']:
            transaction_data['reference_number'] = str(row[mappings['reference_number']])
        
        return transaction_data
    
    def _parse_date(self, date_str):
        """Parse date string with comprehensive format support"""
        if not date_str or pd.isna(date_str):
            raise ValueError("Empty date value")
            
        date_str = str(date_str).strip()
        
        # Comprehensive date format patterns (same as validator)
        date_formats = [
            # ISO and common formats
            '%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d',
            '%m/%d/%Y', '%m-%d-%Y', '%m.%d.%Y',
            '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y',
            
            # 2-digit year formats
            '%m/%d/%y', '%m-%d-%y', '%m.%d.%y',
            '%d/%m/%y', '%d-%m-%y', '%d.%m.%y',
            '%y/%m/%d', '%y-%m-%d', '%y.%m.%d',
            
            # With time components (extract date part)
            '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M',
            '%m/%d/%Y %H:%M:%S', '%m/%d/%Y %H:%M',
            '%d/%m/%Y %H:%M:%S', '%d/%m/%Y %H:%M',
            
            # Month names
            '%B %d, %Y', '%b %d, %Y', '%d %B %Y', '%d %b %Y',
            '%B %d %Y', '%b %d %Y', '%Y %B %d', '%Y %b %d',
        ]
        
        # First try exact format matching
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        # Fallback to pandas intelligent parsing
        try:
            parsed_date = pd.to_datetime(date_str, infer_datetime_format=True)
            return parsed_date.date()
        except (ValueError, TypeError, pd.errors.ParserError):
            pass
        
        # Final fallback to dateutil parser
        try:
            from dateutil import parser
            parsed_date = parser.parse(date_str)
            return parsed_date.date()
        except (ValueError, TypeError):
            pass
        
        raise ValueError(f"Unable to parse date: {date_str}")
    
    def _parse_amount(self, amount_str):
        """Parse amount string with format detection"""
        # Remove currency symbols and whitespace
        clean_amount = re.sub(r'[$,\s]', '', amount_str)
        
        # Handle parentheses (negative amounts)
        if clean_amount.startswith('(') and clean_amount.endswith(')'):
            clean_amount = '-' + clean_amount[1:-1]
        
        try:
            return float(clean_amount)
        except ValueError:
            raise ValueError(f"Unable to parse amount: {amount_str}")