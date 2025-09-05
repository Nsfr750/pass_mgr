"""Comprehensive password security audit tool."""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..models import PasswordEntry
from .password_analyzer import PasswordAnalyzer, PasswordAnalysisResult
from .breach_monitor import BreachMonitor

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class AuditResult:
    """Results of a password audit."""
    timestamp: str
    total_entries: int = 0
    weak_passwords: int = 0
    duplicate_passwords: int = 0
    old_passwords: int = 0
    breached_passwords: int = 0
    average_strength: float = 0.0
    strength_distribution: Dict[str, int] = field(default_factory=dict)
    weak_password_entries: List[Tuple[PasswordEntry, PasswordAnalysisResult]] = field(default_factory=list)
    duplicate_password_entries: List[Tuple[str, List[PasswordEntry]]] = field(default_factory=list)
    old_password_entries: List[Tuple[PasswordEntry, int]] = field(default_factory=list)
    breached_password_entries: List[Tuple[PasswordEntry, int]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the audit result to a dictionary."""
        return {
            'timestamp': self.timestamp,
            'total_entries': self.total_entries,
            'weak_passwords': self.weak_passwords,
            'duplicate_passwords': self.duplicate_passwords,
            'old_passwords': self.old_passwords,
            'breached_passwords': self.breached_passwords,
            'average_strength': self.average_strength,
            'strength_distribution': self.strength_distribution,
            'recommendations': self.recommendations
        }

class PasswordAuditor:
    """Comprehensive password security auditor."""
    
    def __init__(self, entries: List[PasswordEntry], hibp_api_key: str = None):
        """Initialize the password auditor.
        
        Args:
            entries: List of PasswordEntry objects to audit
            hibp_api_key: Optional API key for Have I Been Pwned
        """
        self.entries = entries
        self.analyzer = PasswordAnalyzer(entries)
        self.breach_monitor = BreachMonitor(api_key=hibp_api_key)
    
    def run_audit(
        self, 
        check_breaches: bool = True,
        weak_threshold: int = 60,
        max_age_days: int = 180,
        progress_callback=None
    ) -> AuditResult:
        """Run a comprehensive password security audit.
        
        Args:
            check_breaches: Whether to check for breached passwords
            weak_threshold: Maximum score to consider a password weak (0-100)
            max_age_days: Maximum age in days to consider a password "old"
            progress_callback: Optional callback function for progress updates
            
        Returns:
            AuditResult with the audit findings
        """
        logger.info("Starting password security audit...")
        result = AuditResult(timestamp=datetime.now().isoformat())
        
        # Get total number of steps for progress tracking
        total_steps = 4  # Analysis, weak passwords, duplicates, old passwords
        if check_breaches:
            total_steps += 1
        
        current_step = 0
        
        # 1. Run password analysis
        if progress_callback:
            progress_callback(current_step, total_steps, "Analyzing password strength...")
        
        # Get password health summary
        health_summary = self.analyzer.get_password_health_summary()
        
        # Update result with basic metrics
        result.total_entries = health_summary['total_passwords']
        result.weak_passwords = health_summary['weak_passwords']
        result.duplicate_passwords = health_summary['duplicate_passwords']
        result.old_passwords = health_summary['old_passwords']
        result.average_strength = health_summary['average_strength']
        result.strength_distribution = health_summary['strength_distribution']
        
        current_step += 1
        
        # 2. Get weak passwords
        if progress_callback:
            progress_callback(current_step, total_steps, "Identifying weak passwords...")
        
        result.weak_password_entries = self.analyzer.get_weak_passwords(threshold=weak_threshold)
        
        current_step += 1
        
        # 3. Get duplicate passwords
        if progress_callback:
            progress_callback(current_step, total_steps, "Finding duplicate passwords...")
        
        duplicates = self.analyzer.find_duplicate_passwords()
        result.duplicate_password_entries = [
            (dup.password, dup.entries) 
            for dup in duplicates
        ]
        
        current_step += 1
        
        # 4. Get old passwords
        if progress_callback:
            progress_callback(current_step, total_steps, "Checking for old passwords...")
        
        result.old_password_entries = self.analyzer.get_old_passwords(max_age_days=max_age_days)
        
        current_step += 1
        
        # 5. Check for breached passwords (if enabled)
        if check_breaches:
            if progress_callback:
                progress_callback(current_step, total_steps, "Checking for breached passwords...")
            
            # Only check non-empty passwords
            entries_to_check = [
                entry for entry in self.entries 
                if hasattr(entry, 'password') and entry.password
            ]
            
            # Define a nested progress callback
            def breach_progress(completed, total):
                if progress_callback:
                    progress_callback(
                        current_step, 
                        total_steps, 
                        f"Checking for breached passwords... ({completed}/{total})"
                    )
            
            # Check for breached passwords
            breach_results = self.breach_monitor.check_breaches_for_entries(
                entries_to_check,
                progress_callback=breach_progress
            )
            
            # Process breach results
            for password, entries in breach_results.items():
                # Get the breach count from the first entry (all entries with same password have same count)
                breach_count = self.breach_monitor._check_password_breach(password).breach_count
                for entry in entries:
                    result.breached_password_entries.append((entry, breach_count))
            
            result.breached_passwords = len(breach_results)
            current_step += 1
        
        # Generate recommendations
        self._generate_recommendations(result)
        
        if progress_callback:
            progress_callback(total_steps, total_steps, "Audit complete!")
        
        logger.info("Password security audit completed.")
        return result
    
    def _generate_recommendations(self, result: AuditResult) -> None:
        """Generate security recommendations based on audit results."""
        recommendations = []
        
        # Weak passwords
        if result.weak_passwords > 0:
            weak_pct = (result.weak_passwords / result.total_entries) * 100
            recommendations.append(
                f"Change {result.weak_passwords} weak passwords ({weak_pct:.1f}% of total)."
            )
        
        # Duplicate passwords
        if result.duplicate_passwords > 0:
            dup_pct = (result.duplicate_passwords / result.total_entries) * 100
            recommendations.append(
                f"{result.duplicate_passwords} passwords are used for multiple accounts ({dup_pct:.1f}% of total). "
                "Consider using unique passwords for each account."
            )
        
        # Old passwords
        if result.old_passwords > 0:
            old_pct = (result.old_passwords / result.total_entries) * 100
            recommendations.append(
                f"{result.old_passwords} passwords haven't been changed in over 6 months ({old_pct:.1f}% of total). "
                "Consider rotating these passwords."
            )
        
        # Breached passwords
        if result.breached_passwords > 0:
            breach_pct = (result.breached_passwords / result.total_entries) * 100
            recommendations.append(
                f"{result.breached_passwords} passwords have been exposed in data breaches ({breach_pct:.1f}% of total). "
                "Change these passwords immediately."
            )
        
        # Password strength
        if result.average_strength < 70:
            recommendations.append(
                f"The average password strength is {result.average_strength:.1f}/100. "
                "Consider using stronger passwords."
            )
        
        # If no issues found
        if not recommendations:
            recommendations.append("Great job! Your passwords are secure.")
        
        result.recommendations = recommendations
    
    def get_security_score(self, result: AuditResult) -> int:
        """Calculate an overall security score (0-100) based on audit results."""
        if result.total_entries == 0:
            return 0
        
        score = 100
        
        # Penalize for weak passwords
        weak_pct = (result.weak_passwords / result.total_entries) * 100
        score -= min(weak_pct * 0.5, 30)  # Up to 30 points for weak passwords
        
        # Penalize for duplicate passwords
        dup_pct = (result.duplicate_passwords / result.total_entries) * 100
        score -= min(dup_pct * 0.5, 20)  # Up to 20 points for duplicates
        
        # Penalize for old passwords
        old_pct = (result.old_passwords / result.total_entries) * 100
        score -= min(old_pct * 0.3, 15)  # Up to 15 points for old passwords
        
        # Penalize for breached passwords
        breach_pct = (result.breached_passwords / result.total_entries) * 100
        score -= min(breach_pct * 1.0, 35)  # Up to 35 points for breaches
        
        # Adjust based on average strength
        strength_penalty = max(0, 70 - result.average_strength) * 0.3
        score -= strength_penalty
        
        # Ensure score is within bounds
        return max(0, min(100, int(score)))
    
    def generate_report(self, result: AuditResult) -> str:
        """Generate a human-readable security report."""
        report = []
        report.append("=" * 50)
        report.append("PASSWORD SECURITY AUDIT REPORT")
        report.append("=" * 50)
        report.append(f"Date: {result.timestamp}")
        report.append(f"Total entries: {result.total_entries}")
        report.append("\nSUMMARY:")
        report.append(f"- Weak passwords: {result.weak_passwords} (Score < 60)")
        report.append(f"- Duplicate passwords: {result.duplicate_passwords}")
        report.append(f"- Old passwords (>6 months): {result.old_passwords}")
        report.append(f"- Breached passwords: {result.breached_passwords}")
        report.append(f"- Average strength: {result.average_strength:.1f}/100")
        
        # Strength distribution
        report.append("\nSTRENGTH DISTRIBUTION:")
        for strength, count in result.strength_distribution.items():
            pct = (count / result.total_entries * 100) if result.total_entries > 0 else 0
            report.append(f"- {strength.replace('_', ' ').title()}: {count} ({pct:.1f}%)")
        
        # Recommendations
        if result.recommendations:
            report.append("\nRECOMMENDATIONS:")
            for i, rec in enumerate(result.recommendations, 1):
                report.append(f"{i}. {rec}")
        
        # Overall security score
        security_score = self.get_security_score(result)
        report.append(f"\nOVERALL SECURITY SCORE: {security_score}/100")
        
        return "\n".join(report)
