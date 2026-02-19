"""
Bot Detection - Pure Rule-Based System
NO ML MODEL - Direct behavioral analysis with hard thresholds
Optimized to detect Selenium and other automation tools
"""

import numpy as np
from typing import Tuple, Dict, List, Any
from app.features.extractor import FeatureExtractor


class BotDetector:
    """
    Pure rule-based bot detection - NO ML MODEL
    Uses behavioral analysis with hard thresholds to detect automation
    """
    
    # ===== HUMAN BASELINE REQUIREMENTS =====
    # These are MINIMUM values a human session should have
    HUMAN_REQUIREMENTS = {
        # Mouse behavior
        'min_mouse_movements': 20,
        'min_mouse_distance': 200,
        'min_direction_changes': 8,
        'min_mouse_clicks': 1,
        'min_jitter_score': 0.015,
        'max_straight_line_ratio': 0.70,
        'min_velocity_std': 40,
        
        # Scroll behavior
        'min_scroll_events': 2,
        'max_scroll_regularity': 0.85,
        
        # Timing behavior
        'min_session_time_ms': 2500,
        'min_first_interaction_ms': 150,
        'min_interaction_gap_std': 80,
        
        # Entropy thresholds (randomness)
        'min_timing_entropy': 0.25,
        'min_velocity_entropy': 0.25,
    }
    
    # Score thresholds
    BOT_THRESHOLD = 0.60        # Below this = definitely bot
    SUSPICIOUS_THRESHOLD = 0.75  # Below this = suspicious (aggressively flagged as bot)
    HUMAN_THRESHOLD = 0.80       # Above this = likely human
    
    def __init__(self):
        self.feature_extractor = FeatureExtractor()
        self.model_loaded = False  # No model - pure rules
        print("Bot Detector initialized - Pure Rule-Based Mode (No ML)")
    
    def predict(self, features: np.ndarray, anomalies: List[str]) -> Tuple[bool, float, float]:
        """
        Detect bot using pure rule-based analysis
        
        Returns:
            Tuple of (is_human, confidence, risk_score)
        """
        feature_names = self.feature_extractor.get_feature_names()
        feature_dict = dict(zip(feature_names, features))
        
        # Start with base score
        score = 1.0
        penalties = []
        bonuses = []
        
        # ===== PHASE 1: INSTANT FAILURES (Score capped at 0.15) =====
        instant_fail, fail_reasons = self._check_instant_failures(feature_dict, anomalies)
        if instant_fail:
            score = 0.10
            for reason in fail_reasons:
                penalties.append(f"INSTANT_FAIL: {reason}")
            risk_score = 1 - score
            return False, score, risk_score
        
        # ===== PHASE 2: HARD BEHAVIORAL CHECKS =====
        behavioral_penalty, behavioral_reasons = self._check_behavioral_requirements(feature_dict)
        score -= behavioral_penalty
        penalties.extend(behavioral_reasons)
        
        # ===== PHASE 3: ENTROPY/RANDOMNESS CHECKS =====
        entropy_penalty, entropy_reasons = self._check_entropy_requirements(feature_dict)
        score -= entropy_penalty
        penalties.extend(entropy_reasons)
        
        # ===== PHASE 4: ANOMALY PENALTIES =====
        anomaly_penalty = self._calculate_anomaly_penalty(anomalies)
        score -= anomaly_penalty
        if anomaly_penalty > 0:
            penalties.append(f"Anomalies: {len(anomalies)} detected (-{anomaly_penalty:.2f})")
        
        # ===== PHASE 5: POSITIVE SIGNALS (BONUSES) =====
        bonus, bonus_reasons = self._calculate_bonuses(feature_dict)
        score += bonus
        bonuses.extend(bonus_reasons)
        
        # Clamp score
        score = max(0.0, min(1.0, score))
        
        # ===== AGGRESSIVE BOT FLAGGING =====
        # If score is below 70%, aggressively mark as bot with 20% score
        if score < self.SUSPICIOUS_THRESHOLD:
            original_score = score
            score = 0.20  # Force to 20%
            penalties.append(f"AGGRESSIVE_FLAG: Score {original_score:.2f} < 70% → forced to 20%")
            is_human = False
            print(f"\n🚨 AGGRESSIVE BOT DETECTION 🚨")
            print(f"Original Score: {original_score:.2f} → Forced to: {score:.2f}")
        else:
            is_human = True
        
        risk_score = 1 - score
        
        # Debug output
        print(f"\n=== BOT DETECTION RESULT ===")
        print(f"Final Score: {score:.2f} ({'✅ HUMAN' if is_human else '🤖 BOT DETECTED'})")
        print(f"Penalties: {penalties[:5]}")  # Show top 5
        print(f"Bonuses: {bonuses[:3]}")
        
        return is_human, score, risk_score
    
    def _check_instant_failures(self, features: Dict[str, float], anomalies: List[str]) -> Tuple[bool, List[str]]:
        """
        Check for conditions that INSTANTLY mark as bot (score capped at 15%)
        """
        failures = []
        
        # 1. Webdriver detected
        if features.get('env_webdriver', 0) > 0:
            failures.append("WEBDRIVER_DETECTED")
        
        # 2. Automation flags detected
        if features.get('env_automation_flag_count', 0) > 0:
            failures.append(f"AUTOMATION_FLAGS({int(features.get('env_automation_flag_count', 0))})")
        
        # 3. Zero mouse movement with clicks (impossible for human)
        mouse_count = features.get('mouse_movement_count', 0)
        click_count = features.get('mouse_click_count', 0)
        if mouse_count == 0 and click_count > 0:
            failures.append("CLICKS_WITHOUT_MOUSE_MOVEMENT")
        
        # 4. Instant interaction (faster than human reaction time)
        first_interaction = features.get('timing_first_interaction', -1)
        if first_interaction >= 0 and first_interaction < 50:
            failures.append(f"SUPERHUMAN_REACTION({first_interaction}ms)")
        
        # 5. Session too short with form submission
        session_time = features.get('timing_total_interaction', 0)
        if session_time < 500 and click_count > 0:
            failures.append(f"INSTANT_SUBMISSION({session_time}ms)")
        
        # 6. Perfect straight line mouse movement
        straight_ratio = features.get('mouse_straight_line_ratio', 0)
        if straight_ratio > 0.95 and mouse_count > 10:
            failures.append(f"PERFECT_STRAIGHT_MOUSE({straight_ratio:.2f})")
        
        # 7. Zero jitter with significant movement
        jitter = features.get('mouse_jitter_score', 0)
        if jitter < 0.005 and mouse_count > 15:
            failures.append(f"ZERO_JITTER({jitter:.4f})")
        
        # 8. Hard fail anomalies
        hard_fails = [a for a in anomalies if 'HARD_FAIL' in a]
        if len(hard_fails) >= 3:
            failures.append(f"MULTIPLE_HARD_FAILS({len(hard_fails)})")
        
        return len(failures) > 0, failures
    
    def _check_behavioral_requirements(self, features: Dict[str, float]) -> Tuple[float, List[str]]:
        """
        Check behavioral metrics against human requirements
        Returns penalty (0-0.6) and reasons
        """
        penalty = 0.0
        reasons = []
        req = self.HUMAN_REQUIREMENTS
        
        # Mouse movement count
        mouse_count = features.get('mouse_movement_count', 0)
        if mouse_count < req['min_mouse_movements']:
            p = 0.15 if mouse_count < req['min_mouse_movements'] * 0.5 else 0.08
            penalty += p
            reasons.append(f"Low mouse movements: {mouse_count} < {req['min_mouse_movements']} (-{p})")
        
        # Direction changes
        dir_changes = features.get('mouse_direction_changes', 0)
        if dir_changes < req['min_direction_changes']:
            p = 0.12 if dir_changes < req['min_direction_changes'] * 0.5 else 0.06
            penalty += p
            reasons.append(f"Low direction changes: {dir_changes} < {req['min_direction_changes']} (-{p})")
        
        # Straight line ratio (should be LOW for humans)
        straight_ratio = features.get('mouse_straight_line_ratio', 0)
        if straight_ratio > req['max_straight_line_ratio'] and mouse_count > 10:
            p = 0.15 if straight_ratio > 0.85 else 0.08
            penalty += p
            reasons.append(f"Too straight: {straight_ratio:.2f} > {req['max_straight_line_ratio']} (-{p})")
        
        # Jitter score (natural micro-movements)
        jitter = features.get('mouse_jitter_score', 0)
        if jitter < req['min_jitter_score'] and mouse_count > 10:
            p = 0.12 if jitter < req['min_jitter_score'] * 0.5 else 0.06
            penalty += p
            reasons.append(f"Low jitter: {jitter:.4f} < {req['min_jitter_score']} (-{p})")
        
        # Velocity standard deviation
        vel_std = features.get('mouse_velocity_std', 0)
        if vel_std < req['min_velocity_std'] and mouse_count > 10:
            p = 0.10 if vel_std < req['min_velocity_std'] * 0.5 else 0.05
            penalty += p
            reasons.append(f"Low velocity variance: {vel_std:.1f} < {req['min_velocity_std']} (-{p})")
        
        # Session time
        session_time = features.get('timing_total_interaction', 0)
        if session_time < req['min_session_time_ms']:
            p = 0.15 if session_time < req['min_session_time_ms'] * 0.5 else 0.08
            penalty += p
            reasons.append(f"Short session: {session_time}ms < {req['min_session_time_ms']}ms (-{p})")
        
        # First interaction time
        first_interaction = features.get('timing_first_interaction', -1)
        if first_interaction >= 0 and first_interaction < req['min_first_interaction_ms']:
            p = 0.12 if first_interaction < req['min_first_interaction_ms'] * 0.5 else 0.06
            penalty += p
            reasons.append(f"Fast reaction: {first_interaction}ms < {req['min_first_interaction_ms']}ms (-{p})")
        
        # Interaction gap consistency (should have variance)
        gap_std = features.get('timing_interaction_gap_std', 0)
        if gap_std < req['min_interaction_gap_std']:
            p = 0.10 if gap_std < req['min_interaction_gap_std'] * 0.5 else 0.05
            penalty += p
            reasons.append(f"Regular timing: gap_std={gap_std:.1f} < {req['min_interaction_gap_std']} (-{p})")
        
        # Scroll events
        scroll_count = features.get('scroll_event_count', 0)
        if scroll_count < req['min_scroll_events']:
            penalty += 0.05
            reasons.append(f"Low scrolls: {scroll_count} < {req['min_scroll_events']} (-0.05)")
        
        return min(penalty, 0.60), reasons
    
    def _check_entropy_requirements(self, features: Dict[str, float]) -> Tuple[float, List[str]]:
        """
        Check entropy/randomness metrics
        Low entropy = programmatic/bot behavior
        """
        penalty = 0.0
        reasons = []
        req = self.HUMAN_REQUIREMENTS
        
        # Timing gap entropy
        timing_entropy = features.get('timing_gap_entropy', 0.5)
        if timing_entropy < req['min_timing_entropy']:
            p = 0.15 if timing_entropy < 0.15 else 0.08
            penalty += p
            reasons.append(f"Low timing entropy: {timing_entropy:.2f} < {req['min_timing_entropy']} (-{p})")
        
        # Velocity entropy
        vel_entropy = features.get('mouse_velocity_entropy', 0.5)
        mouse_count = features.get('mouse_movement_count', 0)
        if vel_entropy < req['min_velocity_entropy'] and mouse_count > 10:
            p = 0.15 if vel_entropy < 0.15 else 0.08
            penalty += p
            reasons.append(f"Low velocity entropy: {vel_entropy:.2f} < {req['min_velocity_entropy']} (-{p})")
        
        # Scroll regularity (high = mechanical)
        scroll_regularity = features.get('scroll_interval_regularity', 0.5)
        scroll_count = features.get('scroll_event_count', 0)
        if scroll_regularity > req['max_scroll_regularity'] and scroll_count > 3:
            p = 0.10 if scroll_regularity > 0.92 else 0.05
            penalty += p
            reasons.append(f"Mechanical scrolling: regularity={scroll_regularity:.2f} (-{p})")
        
        # Combined low entropy (strong bot signal)
        if timing_entropy < 0.20 and vel_entropy < 0.20:
            penalty += 0.15
            reasons.append(f"Combined low entropy (bot pattern) (-0.15)")
        
        return min(penalty, 0.45), reasons
    
    def _calculate_anomaly_penalty(self, anomalies: List[str]) -> float:
        """Calculate penalty from detected anomalies"""
        penalty = 0.0
        
        for anomaly in anomalies:
            if 'HARD_FAIL' in anomaly:
                penalty += 0.10
            elif 'webdriver' in anomaly.lower():
                penalty += 0.15
            elif 'automation' in anomaly.lower():
                penalty += 0.12
            elif 'entropy' in anomaly.lower():
                penalty += 0.08
            elif 'straight' in anomaly.lower():
                penalty += 0.08
            elif 'instant' in anomaly.lower():
                penalty += 0.08
            else:
                penalty += 0.03
        
        return min(penalty, 0.40)
    
    def _calculate_bonuses(self, features: Dict[str, float]) -> Tuple[float, List[str]]:
        """
        Calculate positive signals that indicate human behavior
        """
        bonus = 0.0
        reasons = []
        
        # Rich mouse movement
        mouse_count = features.get('mouse_movement_count', 0)
        if mouse_count > 80:
            bonus += 0.08
            reasons.append(f"Rich mouse movement: {mouse_count} (+0.08)")
        
        # Good direction changes
        dir_changes = features.get('mouse_direction_changes', 0)
        if dir_changes > 20:
            bonus += 0.06
            reasons.append(f"Natural direction changes: {dir_changes} (+0.06)")
        
        # Good jitter (micro-movements)
        jitter = features.get('mouse_jitter_score', 0)
        if jitter > 0.04:
            bonus += 0.05
            reasons.append(f"Natural jitter: {jitter:.3f} (+0.05)")
        
        # High velocity variance
        vel_std = features.get('mouse_velocity_std', 0)
        if vel_std > 100:
            bonus += 0.05
            reasons.append(f"Variable velocity: std={vel_std:.1f} (+0.05)")
        
        # Good session time
        session_time = features.get('timing_total_interaction', 0)
        if session_time > 8000:
            bonus += 0.05
            reasons.append(f"Good session time: {session_time}ms (+0.05)")
        
        # High entropy
        timing_entropy = features.get('timing_gap_entropy', 0)
        if timing_entropy > 0.5:
            bonus += 0.06
            reasons.append(f"High timing entropy: {timing_entropy:.2f} (+0.06)")
        
        vel_entropy = features.get('mouse_velocity_entropy', 0)
        if vel_entropy > 0.5:
            bonus += 0.05
            reasons.append(f"High velocity entropy: {vel_entropy:.2f} (+0.05)")
        
        return min(bonus, 0.30), reasons
    
    def get_feature_importance(self, features: np.ndarray) -> Dict[str, float]:
        """Return feature values as importance (no ML model)"""
        feature_names = self.feature_extractor.get_feature_names()
        normalized = features / (np.max(np.abs(features)) + 1e-10)
        return dict(zip(feature_names, normalized))
    
    def is_model_loaded(self) -> bool:
        """No model in rule-based mode"""
        return False


# Global instance
bot_detector = BotDetector()
