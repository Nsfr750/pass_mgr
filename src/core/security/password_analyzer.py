"""Password analysis utilities including duplicate detection and strength analysis."""
from typing import List, Dict, Tuple, Set, Optional
from dataclasses import dataclass
from collections import defaultdict
import re
import string
from datetime import datetime, timedelta

from ...models import PasswordEntry

@dataclass
class PasswordAnalysisResult:
    """Results of password analysis."""
    is_duplicate: bool = False
    strength_score: int = 0  # 0-100
    strength_label: str = "Very Weak"  # Very Weak, Weak, Moderate, Strong, Very Strong
    is_breached: bool = False
    age_days: Optional[int] = None
    common_patterns: List[str] = None
    recommendations: List[str] = None

@dataclass
class DuplicatePasswords:
    """Information about duplicate passwords."""
    password: str
    count: int
    entries: List[PasswordEntry]

class PasswordAnalyzer:
    """Analyze passwords for security issues."""
    
    # Common passwords to check against
    COMMON_PASSWORDS = {
        '123456', 'password', '12345678', 'qwerty', '123456789',
        '12345', '1234', '111111', '1234567', 'dragon', '123123',
        'baseball', 'abc123', 'football', 'monkey', 'letmein',
        'shadow', 'master', '666666', 'qwertyuiop', '123321',
        'mustang', '1234567890', 'michael', '654321', 'superman',
        '1qaz2wsx', '7777777', 'fuckyou', '121212', '000000'
    }
    
    # Common patterns to detect
    COMMON_PATTERNS = [
        (r'^[0-9]+$', 'Numbers only'),
        (r'^[a-zA-Z]+$', 'Letters only'),
        (r'(.)\1{2,}', 'Repeated characters'),
        (r'12345|23456|34567|45678|56789|67890', 'Simple sequences'),
        (r'qwerty|asdfgh|zxcvbn|qazwsx|qwertyuiop', 'Keyboard patterns'),
        (r'^[A-Z][a-z]+\d+$', 'Capital letter followed by lowercase and numbers'),
        (r'^\d+[a-zA-Z]+$', 'Numbers followed by letters')
    ]
    
    def __init__(self, entries: List[PasswordEntry]):
        """Initialize the analyzer with password entries."""
        self.entries = entries
        self._password_map = self._build_password_map()
    
    def _build_password_map(self) -> Dict[str, List[PasswordEntry]]:
        """Build a map of password to list of entries using that password."""
        password_map = defaultdict(list)
        for entry in self.entries:
            if entry.password:  # Only include entries with passwords
                password_map[entry.password].append(entry)
        return password_map
    
    def find_duplicate_passwords(self) -> List[DuplicatePasswords]:
        """Find all passwords that are used for multiple accounts.
        
        Returns:
            List of DuplicatePasswords objects for passwords used more than once
        """
        duplicates = []
        for password, entries in self._password_map.items():
            if len(entries) > 1:  # Only include duplicates
                duplicates.append(DuplicatePasswords(
                    password=password,
                    count=len(entries),
                    entries=entries
                ))
        
        # Sort by count in descending order
        return sorted(duplicates, key=lambda x: x.count, reverse=True)
    
    def analyze_password(self, password: str, entry: PasswordEntry = None) -> PasswordAnalysisResult:
        """Analyze a single password for security issues.
        
        Args:
            password: The password to analyze
            entry: Optional PasswordEntry for additional context (e.g., username, URL)
            
        Returns:
            PasswordAnalysisResult with analysis details
        """
        if not password:
            return PasswordAnalysisResult(
                strength_score=0,
                strength_label="No Password"
            )
        
        result = PasswordAnalysisResult()
        
        # Check for duplicates
        if password in self._password_map:
            result.is_duplicate = len(self._password_map[password]) > 1
        
        # Calculate strength score (0-100)
        score = 0
        
        # Length (up to 30 points)
        length = len(password)
        if length >= 12:
            score += 30
        else:
            score += min(30, length * 2.5)  # 2.5 points per character up to 30
        
        # Character variety (up to 30 points)
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        # Add points for each character type present
        char_variety = sum([has_lower, has_upper, has_digit, has_special])
        score += char_variety * 7.5  # Up to 30 points (4 * 7.5)
        
        # Entropy (up to 20 points)
        # This is a simplified version - a real implementation would calculate actual entropy
        char_set = 0
        if has_lower:
            char_set += 26
        if has_upper:
            char_set += 26
        if has_digit:
            char_set += 10
        if has_special:
            char_set += 32  # Common special characters
        
        # Simplified entropy calculation
        if char_set > 0:
            entropy = length * (char_set ** 0.5)
            score += min(20, (entropy / 50) * 20)
        
        # Penalties (up to -20 points)
        penalties = 0
        
        # Common password penalty
        if password.lower() in self.COMMON_PASSWORDS:
            penalties += 10
        
        # Check for common patterns
        result.common_patterns = []
        for pattern, description in self.COMMON_PATTERNS:
            if re.search(pattern, password):
                result.common_patterns.append(description)
                penalties += 2  # Small penalty for each pattern
        
        # Apply penalties (but don't go below 0)
        score = max(0, score - min(penalties, 20))
        
        # Set strength label
        if score >= 80:
            strength_label = "Very Strong"
        elif score >= 60:
            strength_label = "Strong"
        elif score >= 40:
            strength_label = "Moderate"
        elif score >= 20:
            strength_label = "Weak"
        else:
            strength_label = "Very Weak"
        
        # Check password age if entry has timestamps
        age_days = None
        if entry and hasattr(entry, 'updated_at') and entry.updated_at:
            if isinstance(entry.updated_at, str):
                try:
                    from datetime import datetime
                    updated = datetime.fromisoformat(entry.updated_at)
                    age_days = (datetime.now() - updated).days
                except (ValueError, TypeError):
                    pass
            elif hasattr(entry.updated_at, 'timestamp'):
                age_days = (datetime.now() - entry.updated_at).days
        
        # Generate recommendations
        recommendations = []
        if score < 60:
            recommendations.append("Use a stronger password")
        if result.is_duplicate:
            recommendations.append("Don't reuse passwords across multiple accounts")
        if age_days and age_days > 180:  # 6 months
            recommendations.append("Consider changing this password")
        if not has_special and score < 80:
            recommendations.append("Add special characters")
        if length < 12 and score < 80:
            recommendations.append("Use a longer password")
        
        # Set the result
        result.strength_score = int(score)
        result.strength_label = strength_label
        result.age_days = age_days
        result.recommendations = recommendations if recommendations else ["Good password!"]
        
        return result
    
    def analyze_all(self) -> List[Tuple[PasswordEntry, PasswordAnalysisResult]]:
        """Analyze all passwords in the database.
        
        Returns:
            List of tuples containing (entry, analysis_result)
        """
        results = []
        for entry in self.entries:
            if hasattr(entry, 'password') and entry.password:
                analysis = self.analyze_password(entry.password, entry)
                results.append((entry, analysis))
        return results
    
    def get_weak_passwords(self, threshold: int = 60) -> List[Tuple[PasswordEntry, PasswordAnalysisResult]]:
        """Get all passwords with a strength score below the threshold.
        
        Args:
            threshold: Maximum score to consider a password weak (0-100)
            
        Returns:
            List of (entry, analysis) for weak passwords
        """
        return [
            (entry, analysis) 
            for entry, analysis in self.analyze_all() 
            if analysis.strength_score < threshold
        ]
    
    def get_old_passwords(self, max_age_days: int = 180) -> List[Tuple[PasswordEntry, int]]:
        """Get all passwords that haven't been updated in more than max_age_days.
        
        Args:
            max_age_days: Maximum age in days to consider a password "old"
            
        Returns:
            List of (entry, age_in_days) for old passwords
        """
        old_passwords = []
        now = datetime.now()
        
        for entry in self.entries:
            if not hasattr(entry, 'updated_at') or not entry.updated_at:
                continue
                
            if isinstance(entry.updated_at, str):
                try:
                    updated = datetime.fromisoformat(entry.updated_at)
                    age_days = (now - updated).days
                except (ValueError, TypeError):
                    continue
            else:
                age_days = (now - entry.updated_at).days
            
            if age_days > max_age_days:
                old_passwords.append((entry, age_days))
        
        return sorted(old_passwords, key=lambda x: x[1], reverse=True)
    
    def get_password_health_summary(self) -> Dict[str, any]:
        """Get a summary of password health metrics.
        
        Returns:
            Dict containing various password health metrics
        """
        analysis_results = self.analyze_all()
        total = len(analysis_results)
        
        if total == 0:
            return {
                'total_passwords': 0,
                'weak_passwords': 0,
                'duplicate_passwords': 0,
                'old_passwords': 0,
                'average_strength': 0,
                'strength_distribution': {
                    'very_weak': 0,
                    'weak': 0,
                    'moderate': 0,
                    'strong': 0,
                    'very_strong': 0
                }
            }
        
        # Count passwords by strength
        strength_counts = {
            'very_weak': 0,
            'weak': 0,
            'moderate': 0,
            'strong': 0,
            'very_strong': 0
        }
        
        weak_count = 0
        duplicate_count = 0
        total_strength = 0
        
        # First pass: count strengths and find duplicates
        password_usage = defaultdict(int)
        for entry, analysis in analysis_results:
            password_usage[entry.password] += 1
            
            if analysis.strength_score < 40:
                strength_counts['very_weak'] += 1
                weak_count += 1
            elif analysis.strength_score < 60:
                strength_counts['weak'] += 1
                weak_count += 1
            elif analysis.strength_score < 80:
                strength_counts['moderate'] += 1
            elif analysis.strength_score < 90:
                strength_counts['strong'] += 1
            else:
                strength_counts['very_strong'] += 1
            
            total_strength += analysis.strength_score
        
        # Count duplicates (passwords used more than once)
        duplicate_count = sum(1 for count in password_usage.values() if count > 1)
        
        # Count old passwords
        old_passwords = self.get_old_passwords()
        old_count = len(old_passwords)
        
        return {
            'total_passwords': total,
            'weak_passwords': weak_count,
            'duplicate_passwords': duplicate_count,
            'old_passwords': old_count,
            'average_strength': round(total_strength / total, 1) if total > 0 else 0,
            'strength_distribution': strength_counts
        }
