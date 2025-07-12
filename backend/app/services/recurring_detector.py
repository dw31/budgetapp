import hashlib
import re
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from difflib import SequenceMatcher
from ..models import db, Transaction, Account
from sqlalchemy import and_, or_, func

class RecurringTransactionDetector:
    def __init__(self):
        self.similarity_threshold = 0.8  # How similar descriptions must be
        self.amount_tolerance = 0.05  # 5% tolerance for amount variations
        self.min_occurrences = 3  # Minimum occurrences to consider recurring
        self.max_gap_days = 45  # Maximum days between occurrences
        self.min_gap_days = 20  # Minimum days between occurrences (to avoid daily transactions)
    
    def detect_recurring_transactions(self, user_id=None):
        """
        Main method to detect and mark recurring transactions
        """
        print("=== Starting Recurring Transaction Detection ===")
        
        # Get user's transactions
        query = Transaction.query.join(Account)
        if user_id:
            query = query.filter(Account.user_id == user_id)
        
        transactions = query.order_by(Transaction.date.desc()).all()
        print(f"Analyzing {len(transactions)} transactions")
        
        if len(transactions) < self.min_occurrences:
            return {'success': True, 'message': 'Not enough transactions for pattern detection', 'patterns_found': 0}
        
        # Group transactions by potential patterns
        patterns = self._find_transaction_patterns(transactions)
        
        # Analyze patterns and mark recurring transactions
        recurring_count = 0
        for pattern_id, pattern_transactions in patterns.items():
            if self._is_valid_recurring_pattern(pattern_transactions):
                recurring_count += len(pattern_transactions)
                self._mark_as_recurring(pattern_transactions, pattern_id)
        
        # Commit changes
        try:
            db.session.commit()
            print(f"Successfully marked {recurring_count} transactions as recurring")
            return {
                'success': True,
                'patterns_found': len(patterns),
                'recurring_transactions': recurring_count
            }
        except Exception as e:
            db.session.rollback()
            print(f"Error committing recurring transactions: {e}")
            return {'success': False, 'error': str(e)}
    
    def _find_transaction_patterns(self, transactions):
        """
        Group transactions by similarity patterns
        """
        patterns = defaultdict(list)
        
        for transaction in transactions:
            # Skip income transactions (focus on expenses for recurring detection)
            if transaction.amount > 0:
                continue
            
            # Create a pattern key based on normalized description and amount
            pattern_key = self._generate_pattern_key(transaction)
            patterns[pattern_key].append(transaction)
        
        # Filter out patterns with too few transactions
        filtered_patterns = {
            key: transactions for key, transactions in patterns.items()
            if len(transactions) >= self.min_occurrences
        }
        
        print(f"Found {len(filtered_patterns)} potential recurring patterns")
        return filtered_patterns
    
    def _generate_pattern_key(self, transaction):
        """
        Generate a key to group similar transactions
        """
        # Normalize description - remove numbers, dates, and common variable parts
        normalized_desc = self._normalize_description(transaction.description)
        
        # Round amount to handle small variations
        amount_bucket = round(abs(float(transaction.amount)), 0)  # Round to nearest dollar
        
        # Use merchant if available for better grouping
        merchant_part = self._normalize_description(transaction.merchant or "")
        
        # Create pattern key
        pattern_data = f"{normalized_desc}_{merchant_part}_{amount_bucket}"
        return hashlib.md5(pattern_data.encode()).hexdigest()[:16]
    
    def _normalize_description(self, text):
        """
        Normalize transaction description for pattern matching
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove common variable parts
        patterns_to_remove = [
            r'\d{4}-\d{2}-\d{2}',  # Dates
            r'\d{2}/\d{2}/\d{4}',  # Dates
            r'\d{2}-\d{2}-\d{4}',  # Dates
            r'#\d+',               # Reference numbers
            r'\*\d+',              # Card numbers
            r'ref\s*\d+',          # Reference numbers
            r'transaction\s*\d+',  # Transaction IDs
            r'\b\d{10,}\b',        # Long numbers
        ]
        
        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove extra whitespace and special characters
        text = re.sub(r'[^\w\s]', ' ', text)
        text = ' '.join(text.split())
        
        # Take only the first few meaningful words
        words = text.split()[:4]
        return ' '.join(words)
    
    def _is_valid_recurring_pattern(self, transactions):
        """
        Validate if a group of transactions represents a valid recurring pattern
        """
        if len(transactions) < self.min_occurrences:
            return False
        
        # Sort by date
        transactions.sort(key=lambda t: t.date)
        
        # Check time intervals between transactions
        intervals = []
        for i in range(1, len(transactions)):
            delta = (transactions[i].date - transactions[i-1].date).days
            intervals.append(delta)
        
        # Filter out very short intervals (daily transactions)
        valid_intervals = [interval for interval in intervals if interval >= self.min_gap_days]
        
        if not valid_intervals:
            return False
        
        # Check if intervals are reasonably consistent (within monthly range)
        avg_interval = sum(valid_intervals) / len(valid_intervals)
        if not (20 <= avg_interval <= 45):  # Roughly monthly (20-45 days)
            return False
        
        # Check amount consistency
        amounts = [abs(float(t.amount)) for t in transactions]
        avg_amount = sum(amounts) / len(amounts)
        amount_variations = [abs(amount - avg_amount) / avg_amount for amount in amounts]
        max_variation = max(amount_variations) if amount_variations else 0
        
        if max_variation > self.amount_tolerance:
            return False
        
        print(f"Valid recurring pattern found: {len(transactions)} transactions, avg interval: {avg_interval:.1f} days")
        return True
    
    def _mark_as_recurring(self, transactions, pattern_id):
        """
        Mark transactions as recurring with the given pattern ID
        """
        for transaction in transactions:
            transaction.is_recurring = True
            transaction.recurring_pattern_id = pattern_id
    
    def get_recurring_patterns_summary(self, user_id=None):
        """
        Get a summary of all recurring patterns for a user
        """
        try:
            query = Transaction.query.join(Account)
            if user_id:
                query = query.filter(Account.user_id == user_id)
            
            # Check if the fields exist before filtering
            recurring_transactions = query.filter(Transaction.is_recurring == True).all()
        except Exception as e:
            print(f"Error accessing recurring fields: {e}")
            # Return empty patterns if fields don't exist yet
            return []
        
        # Group by pattern
        patterns = defaultdict(list)
        for transaction in recurring_transactions:
            patterns[transaction.recurring_pattern_id].append(transaction)
        
        # Create summary
        summary = []
        for pattern_id, transactions in patterns.items():
            transactions.sort(key=lambda t: t.date)
            
            # Calculate average amount and frequency
            amounts = [abs(float(t.amount)) for t in transactions]
            avg_amount = sum(amounts) / len(amounts)
            
            # Calculate average interval
            if len(transactions) > 1:
                intervals = []
                for i in range(1, len(transactions)):
                    delta = (transactions[i].date - transactions[i-1].date).days
                    intervals.append(delta)
                avg_interval = sum(intervals) / len(intervals)
            else:
                avg_interval = 30  # Default to monthly
            
            summary.append({
                'pattern_id': pattern_id,
                'description': self._get_pattern_description(transactions),
                'merchant': transactions[0].merchant,
                'category_name': transactions[0].category.name if transactions[0].category else 'Uncategorized',
                'avg_amount': round(avg_amount, 2),
                'frequency_days': round(avg_interval),
                'total_occurrences': len(transactions),
                'last_date': transactions[-1].date.isoformat(),
                'next_predicted': self._predict_next_occurrence(transactions)
            })
        
        return summary
    
    def _get_pattern_description(self, transactions):
        """
        Get a representative description for a pattern
        """
        descriptions = [t.description for t in transactions]
        # Find the most common description or use the first one
        if descriptions:
            return max(set(descriptions), key=descriptions.count)
        return "Unknown"
    
    def _predict_next_occurrence(self, transactions):
        """
        Predict when the next occurrence of this recurring transaction might happen
        """
        if len(transactions) < 2:
            return None
        
        transactions.sort(key=lambda t: t.date)
        
        # Calculate average interval
        intervals = []
        for i in range(1, len(transactions)):
            delta = (transactions[i].date - transactions[i-1].date).days
            intervals.append(delta)
        
        avg_interval = sum(intervals) / len(intervals)
        last_date = transactions[-1].date
        
        # Predict next date
        next_date = last_date + timedelta(days=round(avg_interval))
        return next_date.isoformat()
    
    def get_monthly_recurring_vs_nonrecurring(self, user_id, year, month):
        """
        Get recurring vs non-recurring expenses for a specific month
        """
        from datetime import date
        
        # Calculate month boundaries
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        # Get user's transactions for the month
        query = Transaction.query.join(Account).filter(
            Account.user_id == user_id,
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.amount < 0  # Only expenses
        )
        
        transactions = query.all()
        
        # Separate recurring and non-recurring (with fallback if fields don't exist)
        recurring_total = 0
        non_recurring_total = 0
        
        for transaction in transactions:
            amount = abs(float(transaction.amount))
            try:
                if hasattr(transaction, 'is_recurring') and transaction.is_recurring:
                    recurring_total += amount
                else:
                    non_recurring_total += amount
            except:
                # If is_recurring field doesn't exist, treat as non-recurring
                non_recurring_total += amount
        
        # Get category breakdown
        recurring_by_category = defaultdict(float)
        non_recurring_by_category = defaultdict(float)
        
        for transaction in transactions:
            category_name = transaction.category.name if transaction.category else 'Uncategorized'
            amount = abs(float(transaction.amount))
            
            try:
                if hasattr(transaction, 'is_recurring') and transaction.is_recurring:
                    recurring_by_category[category_name] += amount
                else:
                    non_recurring_by_category[category_name] += amount
            except:
                # If is_recurring field doesn't exist, treat as non-recurring
                non_recurring_by_category[category_name] += amount
        
        return {
            'month': f"{year}-{month:02d}",
            'total_expenses': recurring_total + non_recurring_total,
            'recurring': {
                'total': round(recurring_total, 2),
                'percentage': round((recurring_total / (recurring_total + non_recurring_total) * 100) if (recurring_total + non_recurring_total) > 0 else 0, 1),
                'by_category': {cat: round(amount, 2) for cat, amount in recurring_by_category.items()}
            },
            'non_recurring': {
                'total': round(non_recurring_total, 2),
                'percentage': round((non_recurring_total / (recurring_total + non_recurring_total) * 100) if (recurring_total + non_recurring_total) > 0 else 0, 1),
                'by_category': {cat: round(amount, 2) for cat, amount in non_recurring_by_category.items()}
            },
            'transaction_count': {
                'recurring': len([t for t in transactions if hasattr(t, 'is_recurring') and t.is_recurring]),
                'non_recurring': len([t for t in transactions if not (hasattr(t, 'is_recurring') and t.is_recurring)])
            }
        }