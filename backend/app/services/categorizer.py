from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import pickle
import os
import re
import numpy as np
from collections import Counter
from datetime import datetime
from ..models import db, Transaction, Category, CategorizationRule

class TransactionCategorizer:
    def __init__(self):
        self.model = None
        self.model_path = os.path.join(os.path.dirname(__file__), '../../models/categorization_model.pkl')
        self.label_encoder_path = os.path.join(os.path.dirname(__file__), '../../models/label_encoder.pkl')
        self.category_mapping = {}
        self.reverse_category_mapping = {}
        self.confidence_threshold = 0.6
        self.merchant_patterns = {}
        self._load_or_create_model()
        self._load_merchant_patterns()
    
    def _load_or_create_model(self):
        """Load existing model or create new one"""
        # Ensure models directory exists
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        if os.path.exists(self.model_path) and os.path.exists(self.label_encoder_path):
            try:
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                with open(self.label_encoder_path, 'rb') as f:
                    data = pickle.load(f)
                    self.category_mapping = data['category_mapping']
                    self.reverse_category_mapping = data['reverse_category_mapping']
                print("Loaded existing categorization model")
            except Exception as e:
                print(f"Error loading model: {e}")
                self._create_new_model()
        else:
            self._create_new_model()
    
    def _create_new_model(self):
        """Create a new ML model"""
        self.model = Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=2000,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.8
            )),
            ('classifier', RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                max_depth=10,
                min_samples_split=5
            ))
        ])
        print("Created new categorization model")
    
    def categorize_transaction(self, transaction):
        """Categorize a single transaction with enhanced logic"""
        # First, try rule-based categorization
        rule_result = self._apply_rules(transaction)
        if rule_result:
            return rule_result[0], rule_result[1], 'rule-based'
        
        # Try merchant pattern matching
        merchant_result = self._match_merchant_patterns(transaction)
        if merchant_result:
            return merchant_result[0], merchant_result[1], 'merchant-pattern'
        
        # Fallback to ML model
        if self.model and hasattr(self.model, 'predict_proba') and self.category_mapping:
            features = self._extract_features(transaction)
            try:
                prediction_proba = self.model.predict_proba([features])[0]
                max_prob_idx = np.argmax(prediction_proba)
                max_probability = prediction_proba[max_prob_idx]
                
                if max_probability >= self.confidence_threshold:
                    predicted_label = self.model.classes_[max_prob_idx]
                    category_id = self.reverse_category_mapping.get(predicted_label)
                    if category_id:
                        return category_id, max_probability, 'ml-model'
            except Exception as e:
                print(f"ML prediction error: {e}")
        
        # Try amount-based categorization for common patterns
        amount_result = self._categorize_by_amount(transaction)
        if amount_result:
            return amount_result[0], amount_result[1], 'amount-pattern'
        
        # Default category (uncategorized)
        return self._get_default_category(), 0.0, 'default'
    
    def _apply_rules(self, transaction):
        """Apply user-defined categorization rules"""
        rules = CategorizationRule.query.filter_by(is_active=True).order_by(CategorizationRule.priority).all()
        
        for rule in rules:
            if self._rule_matches(transaction, rule):
                return rule.category_id, 1.0  # 100% confidence for rule-based
        
        return None
    
    def _rule_matches(self, transaction, rule):
        """Check if transaction matches a rule"""
        if rule.rule_type == 'merchant':
            value = transaction.merchant or ''
        elif rule.rule_type == 'description':
            value = transaction.description
        elif rule.rule_type == 'amount':
            value = str(transaction.amount)
        else:
            return False
        
        if rule.condition == 'contains':
            return rule.value.lower() in value.lower()
        elif rule.condition == 'equals':
            return rule.value.lower() == value.lower()
        elif rule.condition == 'starts_with':
            return value.lower().startswith(rule.value.lower())
        elif rule.condition == 'ends_with':
            return value.lower().endswith(rule.value.lower())
        elif rule.condition == 'greater_than':
            return float(value) > float(rule.value)
        elif rule.condition == 'less_than':
            return float(value) < float(rule.value)
        
        return False
    
    def _get_default_category(self):
        """Get default uncategorized category"""
        category = Category.query.filter_by(name='Uncategorized', is_system=True).first()
        if not category:
            # Create uncategorized category if it doesn't exist
            category = Category(
                name='Uncategorized',
                color='#9CA3AF',
                is_income=False,
                is_system=True
            )
            db.session.add(category)
            db.session.commit()
        return category.id
    
    def train_model(self, transactions=None, user_id=None):
        """Train the ML model with categorized transactions"""
        if not transactions:
            # Load all categorized transactions from database
            query = Transaction.query.filter(Transaction.category_id.isnot(None))
            if user_id:
                # Filter by user's accounts
                from ..models import Account
                user_accounts = Account.query.filter_by(user_id=user_id).all()
                account_ids = [acc.id for acc in user_accounts]
                query = query.filter(Transaction.account_id.in_(account_ids))
            
            transactions = query.all()
        
        if not transactions or len(transactions) < 10:
            print("Not enough categorized transactions for training")
            return False
        
        features = []
        labels = []
        categories = set()
        
        for transaction in transactions:
            if transaction.category_id and transaction.category:
                feature_text = self._extract_features(transaction)
                features.append(feature_text)
                labels.append(transaction.category_id)
                categories.add(transaction.category_id)
        
        if len(features) < 10 or len(categories) < 2:
            print("Not enough diverse data for training")
            return False
        
        # Create category mappings
        self.category_mapping = {cat_id: i for i, cat_id in enumerate(sorted(categories))}
        self.reverse_category_mapping = {i: cat_id for cat_id, i in self.category_mapping.items()}
        
        # Convert labels to numeric
        numeric_labels = [self.category_mapping[label] for label in labels]
        
        # Split data for validation
        if len(features) > 50:
            X_train, X_test, y_train, y_test = train_test_split(
                features, numeric_labels, test_size=0.2, random_state=42, stratify=numeric_labels
            )
        else:
            X_train, y_train = features, numeric_labels
            X_test, y_test = features, numeric_labels
        
        # Train the model
        self.model.fit(X_train, y_train)
        
        # Evaluate the model
        if len(X_test) > 0:
            y_pred = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            print(f"Model accuracy: {accuracy:.2f}")
            
            # Update confidence threshold based on accuracy
            if accuracy > 0.8:
                self.confidence_threshold = 0.5
            elif accuracy > 0.6:
                self.confidence_threshold = 0.7
            else:
                self.confidence_threshold = 0.8
        
        # Save the model
        self._save_model()
        self._update_merchant_patterns(transactions)
        
        return True
    
    def _save_model(self):
        """Save the trained model and mappings"""
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            
            with open(self.label_encoder_path, 'wb') as f:
                pickle.dump({
                    'category_mapping': self.category_mapping,
                    'reverse_category_mapping': self.reverse_category_mapping,
                    'confidence_threshold': self.confidence_threshold,
                    'merchant_patterns': self.merchant_patterns
                }, f)
            
            print("Model saved successfully")
        except Exception as e:
            print(f"Error saving model: {e}")
    
    def _extract_features(self, transaction):
        """Extract features from transaction for ML model"""
        description = transaction.description.lower() if transaction.description else ''
        merchant = transaction.merchant.lower() if transaction.merchant else ''
        amount = abs(float(transaction.amount)) if transaction.amount else 0
        
        # Clean description
        description = re.sub(r'[^a-zA-Z0-9\s]', ' ', description)
        description = ' '.join(description.split())
        
        # Add amount range as feature
        amount_range = self._get_amount_range(amount)
        
        # Combine features
        features = f"{description} {merchant} {amount_range}"
        return features
    
    def _get_amount_range(self, amount):
        """Categorize amount into ranges"""
        if amount < 10:
            return "micro"
        elif amount < 50:
            return "small"
        elif amount < 200:
            return "medium"
        elif amount < 1000:
            return "large"
        else:
            return "xlarge"
    
    def _load_merchant_patterns(self):
        """Load merchant patterns from saved data"""
        if os.path.exists(self.label_encoder_path):
            try:
                with open(self.label_encoder_path, 'rb') as f:
                    data = pickle.load(f)
                    self.merchant_patterns = data.get('merchant_patterns', {})
                    self.confidence_threshold = data.get('confidence_threshold', 0.6)
            except Exception as e:
                print(f"Error loading merchant patterns: {e}")
    
    def _update_merchant_patterns(self, transactions):
        """Update merchant patterns based on transaction data"""
        merchant_categories = {}
        
        for transaction in transactions:
            if transaction.merchant and transaction.category_id:
                merchant_clean = self._clean_merchant_name(transaction.merchant)
                if merchant_clean not in merchant_categories:
                    merchant_categories[merchant_clean] = []
                merchant_categories[merchant_clean].append(transaction.category_id)
        
        # Calculate most common category for each merchant
        for merchant, categories in merchant_categories.items():
            if len(categories) >= 2:  # Only consider merchants with multiple transactions
                counter = Counter(categories)
                most_common_category, count = counter.most_common(1)[0]
                confidence = count / len(categories)
                
                if confidence >= 0.7:  # 70% confidence threshold
                    self.merchant_patterns[merchant] = {
                        'category_id': most_common_category,
                        'confidence': confidence,
                        'count': count
                    }
    
    def _clean_merchant_name(self, merchant):
        """Clean and normalize merchant name"""
        merchant = merchant.lower().strip()
        # Remove common prefixes/suffixes
        merchant = re.sub(r'\b(inc|llc|corp|ltd|co)\b', '', merchant)
        merchant = re.sub(r'[^a-zA-Z0-9\s]', ' ', merchant)
        merchant = ' '.join(merchant.split())
        return merchant
    
    def _match_merchant_patterns(self, transaction):
        """Try to categorize based on merchant patterns"""
        if not transaction.merchant or not self.merchant_patterns:
            return None
        
        merchant_clean = self._clean_merchant_name(transaction.merchant)
        
        # Direct match
        if merchant_clean in self.merchant_patterns:
            pattern = self.merchant_patterns[merchant_clean]
            return pattern['category_id'], pattern['confidence']
        
        # Partial match
        for pattern_merchant, pattern_data in self.merchant_patterns.items():
            if (len(pattern_merchant) > 3 and pattern_merchant in merchant_clean) or \
               (len(merchant_clean) > 3 and merchant_clean in pattern_merchant):
                # Reduce confidence for partial matches
                confidence = pattern_data['confidence'] * 0.8
                if confidence >= 0.5:
                    return pattern_data['category_id'], confidence
        
        return None
    
    def _categorize_by_amount(self, transaction):
        """Categorize based on common amount patterns"""
        if not transaction.amount:
            return None
        
        amount = abs(float(transaction.amount))
        description = transaction.description.lower() if transaction.description else ""
        merchant = transaction.merchant.lower() if transaction.merchant else ""
        
        # Combine description and merchant for better matching
        full_text = f"{description} {merchant}"
        
        # Dining and Food
        food_keywords = ['restaurant', 'mcdonald', 'burger', 'pizza', 'starbucks', 'coffee', 'cafe', 'dining', 'food', 'subway', 'taco', 'kfc', 'domino', 'chipotle', 'panera']
        if any(keyword in full_text for keyword in food_keywords):
            category = Category.query.filter_by(name='Food & Dining', is_system=True).first()
            if category:
                return category.id, 0.7
        
        # Gas and Transportation
        gas_keywords = ['gas', 'fuel', 'exxon', 'shell', 'bp', 'chevron', 'mobil', 'station', 'petrol']
        if any(keyword in full_text for keyword in gas_keywords):
            category = Category.query.filter_by(name='Transportation', is_system=True).first()
            if category:
                return category.id, 0.8
        
        # Shopping
        shopping_keywords = ['walmart', 'target', 'amazon', 'store', 'shop', 'mall', 'retail', 'market', 'purchase']
        if any(keyword in full_text for keyword in shopping_keywords):
            category = Category.query.filter_by(name='Shopping', is_system=True).first()
            if category:
                return category.id, 0.7
        
        # Utilities
        utility_keywords = ['electric', 'gas', 'water', 'internet', 'phone', 'cable', 'utility', 'power', 'energy']
        if any(keyword in full_text for keyword in utility_keywords):
            category = Category.query.filter_by(name='Bills & Utilities', is_system=True).first()
            if category:
                return category.id, 0.8
        
        # Entertainment
        entertainment_keywords = ['movie', 'theater', 'netflix', 'spotify', 'game', 'entertainment', 'music', 'video']
        if any(keyword in full_text for keyword in entertainment_keywords):
            category = Category.query.filter_by(name='Entertainment', is_system=True).first()
            if category:
                return category.id, 0.7
        
        # Healthcare
        health_keywords = ['hospital', 'doctor', 'medical', 'pharmacy', 'health', 'clinic', 'dental', 'cvs', 'walgreens']
        if any(keyword in full_text for keyword in health_keywords):
            category = Category.query.filter_by(name='Healthcare', is_system=True).first()
            if category:
                return category.id, 0.8
        
        # ATM withdrawals and cash
        if any(keyword in full_text for keyword in ['atm', 'withdrawal', 'cash']):
            # Try to find existing category, if not found use "Other" or create it
            category = Category.query.filter_by(name='Cash & ATM', is_system=True).first()
            if not category:
                category = Category.query.filter_by(name='Other', is_system=True).first()
            if category:
                return category.id, 0.7
        
        # Income patterns
        if transaction.amount > 0 and amount > 500:
            income_keywords = ['salary', 'payroll', 'deposit', 'pay', 'income', 'wage', 'direct dep']
            if any(keyword in full_text for keyword in income_keywords):
                category = Category.query.filter_by(name='Salary', is_system=True).first()
                if category:
                    return category.id, 0.8
        
        return None
    
    def bulk_categorize(self, transactions, user_id=None):
        """Categorize multiple transactions at once"""
        results = []
        
        # Debug: List available categories
        categories = Category.query.filter_by(is_system=True).all()
        print(f"Available system categories: {[cat.name for cat in categories]}")
        
        print(f"Starting bulk categorization of {len(transactions)} transactions")
        
        for transaction in transactions:
            try:
                category_id, confidence, method = self.categorize_transaction(transaction)
                
                print(f"Transaction {transaction.id}: {transaction.description[:50]}...")
                print(f"  Result: category_id={category_id}, confidence={confidence}, method={method}")
                
                # Only update if we have a valid category (not default/uncategorized)
                if category_id and confidence > 0.0 and method != 'default':
                    # Update transaction
                    transaction.category_id = category_id
                    transaction.category_confidence = confidence
                    transaction.is_manually_categorized = False
                    
                    results.append({
                        'transaction_id': transaction.id,
                        'category_id': category_id,
                        'confidence': confidence,
                        'method': method
                    })
                    print(f"  Updated transaction {transaction.id}")
                else:
                    print(f"  Skipped: low confidence or default category")
                    
            except Exception as e:
                print(f"Error processing transaction {transaction.id}: {e}")
                continue
        
        try:
            db.session.commit()
            print(f"Bulk categorization completed: {len(results)} transactions updated")
            return {'success': True, 'results': results}
        except Exception as e:
            db.session.rollback()
            print(f"Error committing bulk categorization: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_categorization_stats(self, user_id=None):
        """Get statistics about categorization performance"""
        query = Transaction.query
        
        if user_id:
            from ..models import Account
            user_accounts = Account.query.filter_by(user_id=user_id).all()
            account_ids = [acc.id for acc in user_accounts]
            query = query.filter(Transaction.account_id.in_(account_ids))
        
        total_transactions = query.count()
        categorized_transactions = query.filter(Transaction.category_id.isnot(None)).count()
        manually_categorized = query.filter(
            Transaction.category_id.isnot(None),
            Transaction.is_manually_categorized == True
        ).count()
        
        auto_categorized = categorized_transactions - manually_categorized
        
        return {
            'total_transactions': total_transactions,
            'categorized_transactions': categorized_transactions,
            'auto_categorized': auto_categorized,
            'manually_categorized': manually_categorized,
            'categorization_rate': categorized_transactions / total_transactions if total_transactions > 0 else 0,
            'auto_categorization_rate': auto_categorized / total_transactions if total_transactions > 0 else 0
        }