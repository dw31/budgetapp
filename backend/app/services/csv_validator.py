import pandas as pd
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    file_info: Dict[str, Any]
    columns: List[str]
    sample_data: List[Dict[str, Any]]
    suggested_mappings: Dict[str, str]

@dataclass
class ColumnMapping:
    source_column: str
    target_field: str
    data_type: str
    sample_values: List[str]
    validation_errors: List[str]

class CSVValidator:
    def __init__(self):
        self.required_fields = ['date', 'description', 'amount']
        self.optional_fields = ['merchant', 'category', 'reference_number']
        
        # Common column name patterns for auto-mapping
        self.column_patterns = {
            'date': [
                r'.*date.*', r'.*transaction.*date.*', r'.*posted.*date.*',
                r'.*effective.*date.*', r'.*process.*date.*'
            ],
            'description': [
                r'.*description.*', r'.*desc.*', r'.*detail.*', r'.*memo.*',
                r'.*transaction.*', r'.*payee.*', r'.*merchant.*'
            ],
            'amount': [
                r'.*amount.*', r'.*total.*', r'.*value.*', r'.*sum.*',
                r'.*credit.*', r'.*debit.*', r'.*balance.*'
            ],
            'merchant': [
                r'.*merchant.*', r'.*payee.*', r'.*vendor.*', r'.*store.*'
            ],
            'category': [
                r'.*category.*', r'.*type.*', r'.*class.*'
            ],
            'reference_number': [
                r'.*reference.*', r'.*ref.*', r'.*check.*', r'.*number.*',
                r'.*id.*', r'.*transaction.*id.*'
            ]
        }
        
        # Comprehensive date format patterns
        self.date_formats = [
            # ISO and common formats
            '%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d',
            '%m/%d/%Y', '%m-%d-%Y', '%m.%d.%Y',
            '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y',
            
            # 2-digit year formats
            '%m/%d/%y', '%m-%d-%y', '%m.%d.%y',
            '%d/%m/%y', '%d-%m-%y', '%d.%m.%y',
            '%y/%m/%d', '%y-%m-%d', '%y.%m.%d',
            
            # With time components
            '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M',
            '%m/%d/%Y %H:%M:%S', '%m/%d/%Y %H:%M',
            '%d/%m/%Y %H:%M:%S', '%d/%m/%Y %H:%M',
            
            # Month names (full and abbreviated)
            '%B %d, %Y', '%b %d, %Y', '%d %B %Y', '%d %b %Y',
            '%B %d %Y', '%b %d %Y', '%Y %B %d', '%Y %b %d',
            '%B-%d-%Y', '%b-%d-%Y', '%d-%B-%Y', '%d-%b-%Y',
            
            # Common bank formats
            '%m/%d/%Y %H:%M:%S %p',  # 12/31/2023 11:59:59 PM
            '%Y-%m-%dT%H:%M:%S',     # 2023-12-31T23:59:59
            '%Y-%m-%dT%H:%M:%SZ',    # 2023-12-31T23:59:59Z
            '%Y-%m-%d %I:%M:%S %p',  # 2023-12-31 11:59:59 PM
            
            # European formats
            '%d.%m.%Y', '%d.%m.%y',
            '%d/%m/%Y', '%d/%m/%y',
            '%d-%m-%Y', '%d-%m-%y',
            
            # Single digit formats
            '%m/%d/%Y', '%m/%d/%y',  # Already included but important
            '%-m/%-d/%Y', '%-m/%-d/%y',  # Without leading zeros on Unix
            '%#m/%#d/%Y', '%#m/%#d/%y',  # Without leading zeros on Windows
        ]
    
    def validate_file(self, file_path: str) -> ValidationResult:
        """Validate CSV file structure and content"""
        errors = []
        warnings = []
        columns = []
        sample_data = []
        suggested_mappings = {}
        
        try:
            # Check file existence and size
            if not os.path.exists(file_path):
                errors.append("File does not exist")
                return ValidationResult(False, errors, warnings, {}, [], [], {})
            
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                errors.append("File is empty")
                return ValidationResult(False, errors, warnings, {}, [], [], {})
            
            if file_size > 50 * 1024 * 1024:  # 50MB limit
                errors.append("File too large (max 50MB)")
                return ValidationResult(False, errors, warnings, {}, [], [], {})
            
            # Read CSV file
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(file_path, encoding='latin1')
                    warnings.append("File encoding detected as Latin1")
                except Exception as e:
                    errors.append(f"Cannot read file: {str(e)}")
                    return ValidationResult(False, errors, warnings, {}, [], [], {})
            except Exception as e:
                errors.append(f"Invalid CSV format: {str(e)}")
                return ValidationResult(False, errors, warnings, {}, [], [], {})
            
            # Basic structure validation
            if df.empty:
                errors.append("CSV file contains no data")
                return ValidationResult(False, errors, warnings, {}, [], [], {})
            
            if len(df.columns) < 3:
                errors.append("CSV file must have at least 3 columns")
                return ValidationResult(False, errors, warnings, {}, [], [], {})
            
            # Get file info
            file_info = {
                'filename': os.path.basename(file_path),
                'size': file_size,
                'rows': len(df),
                'columns': len(df.columns),
                'encoding': 'utf-8' if 'utf-8' not in warnings else 'latin1'
            }
            
            # Get columns and clean them
            columns = [str(col).strip() for col in df.columns]
            
            # Generate sample data (first 5 rows)
            sample_data = []
            for i in range(min(5, len(df))):
                row_data = {}
                for col in columns:
                    value = df.iloc[i][col]
                    if pd.isna(value):
                        row_data[col] = None
                    else:
                        row_data[col] = str(value).strip()
                sample_data.append(row_data)
            
            # Auto-suggest column mappings
            suggested_mappings = self._suggest_mappings(columns, sample_data)
            
            # Validate suggested mappings
            mapping_errors = self._validate_mappings(df, suggested_mappings)
            if mapping_errors:
                warnings.extend(mapping_errors)
            
            # Check for required fields
            missing_fields = []
            for field in self.required_fields:
                if field not in suggested_mappings:
                    missing_fields.append(field)
            
            if missing_fields:
                warnings.append(f"Could not auto-map required fields: {', '.join(missing_fields)}")
            
            # Additional validations
            if len(df) > 10000:
                warnings.append(f"Large file with {len(df)} rows - processing may take time")
            
            # Check for duplicate columns
            if len(columns) != len(set(columns)):
                warnings.append("Duplicate column names detected")
            
            is_valid = len(errors) == 0
            
            return ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                file_info=file_info,
                columns=columns,
                sample_data=sample_data,
                suggested_mappings=suggested_mappings
            )
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return ValidationResult(False, errors, warnings, {}, [], [], {})
    
    def _suggest_mappings(self, columns: List[str], sample_data: List[Dict[str, Any]]) -> Dict[str, str]:
        """Auto-suggest column mappings based on column names and sample data"""
        mappings = {}
        
        for field, patterns in self.column_patterns.items():
            best_match = None
            best_score = 0
            
            for column in columns:
                score = self._calculate_column_score(column, patterns, sample_data, field)
                if score > best_score and score > 0.3:  # Minimum confidence threshold
                    best_score = score
                    best_match = column
            
            if best_match:
                mappings[field] = best_match
        
        return mappings
    
    def _calculate_column_score(self, column: str, patterns: List[str], 
                              sample_data: List[Dict[str, Any]], field: str) -> float:
        """Calculate confidence score for column mapping"""
        column_lower = column.lower()
        
        # Score based on column name matching
        name_score = 0
        for pattern in patterns:
            if re.search(pattern, column_lower, re.IGNORECASE):
                name_score = 0.8
                break
        
        # Score based on data content
        content_score = 0
        if sample_data:
            content_score = self._analyze_content(sample_data, column, field)
        
        # Combine scores
        return (name_score * 0.6) + (content_score * 0.4)
    
    def _analyze_content(self, sample_data: List[Dict[str, Any]], column: str, field: str) -> float:
        """Analyze column content to determine field type"""
        if not sample_data:
            return 0
        
        values = [row.get(column) for row in sample_data if row.get(column)]
        if not values:
            return 0
        
        if field == 'date':
            return self._analyze_date_content(values)
        elif field == 'amount':
            return self._analyze_amount_content(values)
        elif field == 'description':
            return self._analyze_description_content(values)
        
        return 0
    
    def _analyze_date_content(self, values: List[str]) -> float:
        """Analyze if values look like dates"""
        date_count = 0
        for value in values:
            if self._is_date_like(str(value)):
                date_count += 1
        
        return date_count / len(values)
    
    def _analyze_amount_content(self, values: List[str]) -> float:
        """Analyze if values look like amounts"""
        amount_count = 0
        for value in values:
            if self._is_amount_like(str(value)):
                amount_count += 1
        
        return amount_count / len(values)
    
    def _analyze_description_content(self, values: List[str]) -> float:
        """Analyze if values look like descriptions"""
        # Check for typical description characteristics
        text_count = 0
        for value in values:
            if (len(str(value)) > 5 and 
                any(char.isalpha() for char in str(value)) and
                not self._is_date_like(str(value)) and
                not self._is_amount_like(str(value))):
                text_count += 1
        
        return text_count / len(values)
    
    def _is_date_like(self, value: str) -> bool:
        """Check if value looks like a date"""
        if not value or pd.isna(value):
            return False
            
        value_str = str(value).strip()
        
        # First try exact format matching
        for fmt in self.date_formats:
            try:
                datetime.strptime(value_str, fmt)
                return True
            except ValueError:
                continue
        
        # Fallback to pandas intelligent date parsing
        try:
            pd.to_datetime(value_str, infer_datetime_format=True)
            return True
        except (ValueError, TypeError, pd.errors.ParserError):
            pass
        
        # Try with common preprocessing
        try:
            # Remove extra whitespace and try again
            cleaned_value = re.sub(r'\s+', ' ', value_str)
            pd.to_datetime(cleaned_value, infer_datetime_format=True)
            return True
        except (ValueError, TypeError, pd.errors.ParserError):
            pass
            
        # Try dateutil parser as final fallback (very flexible)
        try:
            from dateutil import parser
            parser.parse(value_str)
            return True
        except (ValueError, TypeError):
            pass
            
        return False
    
    def _is_amount_like(self, value: str) -> bool:
        """Check if value looks like an amount"""
        # Remove common currency symbols and formatting
        clean_value = re.sub(r'[$,\s]', '', value)
        
        # Check for decimal number pattern
        if re.match(r'^-?\d+\.?\d*$', clean_value):
            return True
        
        # Check for parentheses (negative amounts)
        if re.match(r'^\(\d+\.?\d*\)$', clean_value):
            return True
        
        return False
    
    def _validate_mappings(self, df: pd.DataFrame, mappings: Dict[str, str]) -> List[str]:
        """Validate suggested column mappings"""
        errors = []
        
        for field, column in mappings.items():
            if column not in df.columns:
                errors.append(f"Column '{column}' not found in CSV")
                continue
            
            # Check for too many empty values
            empty_count = df[column].isna().sum()
            if empty_count > len(df) * 0.5:
                errors.append(f"Column '{column}' has too many empty values ({empty_count}/{len(df)})")
            
            # Field-specific validations
            if field == 'date':
                self._validate_date_column(df, column, errors)
            elif field == 'amount':
                self._validate_amount_column(df, column, errors)
        
        return errors
    
    def _validate_date_column(self, df: pd.DataFrame, column: str, errors: List[str]):
        """Validate date column"""
        sample_values = df[column].dropna().head(10)
        valid_dates = 0
        
        print(f"Validating date column '{column}' with {len(sample_values)} sample values")
        
        for i, value in enumerate(sample_values):
            is_valid = self._is_date_like(str(value))
            print(f"  Sample {i+1}: '{value}' -> {is_valid}")
            if is_valid:
                valid_dates += 1
        
        print(f"Date validation result: {valid_dates}/{len(sample_values)} valid dates")
        
        # More lenient threshold - only require 60% of sample values to be valid dates
        # Also provide more helpful error message
        if valid_dates < len(sample_values) * 0.6:
            sample_list = [str(val) for val in sample_values[:3]]
            errors.append(f"Date column '{column}' contains invalid date formats. Sample values: {sample_list}. Only {valid_dates}/{len(sample_values)} values are valid dates.")
    
    def _validate_amount_column(self, df: pd.DataFrame, column: str, errors: List[str]):
        """Validate amount column"""
        sample_values = df[column].dropna().head(10)
        valid_amounts = 0
        
        for value in sample_values:
            if self._is_amount_like(str(value)):
                valid_amounts += 1
        
        if valid_amounts < len(sample_values) * 0.8:
            errors.append(f"Amount column '{column}' contains invalid numeric formats")
    
    def validate_column_mapping(self, file_path: str, mappings: Dict[str, str]) -> ValidationResult:
        """Validate user-defined column mappings"""
        errors = []
        warnings = []
        
        try:
            df = pd.read_csv(file_path)
            
            # Check if all required fields are mapped
            for field in self.required_fields:
                if field not in mappings or not mappings[field]:
                    errors.append(f"Required field '{field}' is not mapped")
            
            # Validate each mapping (skip empty mappings)
            for field, column in mappings.items():
                if not column:  # Skip empty mappings
                    continue
                if column not in df.columns:
                    errors.append(f"Column '{column}' not found in CSV")
                    continue
                
                # Field-specific validations
                if field == 'date':
                    self._validate_date_column(df, column, errors)
                elif field == 'amount':
                    self._validate_amount_column(df, column, errors)
            
            # Check for duplicate mappings (ignore empty values)
            mapped_columns = [col for col in mappings.values() if col]
            if len(mapped_columns) != len(set(mapped_columns)):
                errors.append("Multiple fields cannot be mapped to the same column")
            
            is_valid = len(errors) == 0
            
            return ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                file_info={},
                columns=list(df.columns),
                sample_data=[],
                suggested_mappings=mappings
            )
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return ValidationResult(False, errors, warnings, {}, [], [], {})