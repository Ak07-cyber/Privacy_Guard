"""
Feature Engineering for Bot Detection
Transforms raw data into ML-ready features with rigorous behavioral analysis
Pure rule-based system - no ML dependency
"""

import numpy as np
import math
from typing import Dict, List, Any, Tuple
from app.api.models import VerificationRequest, EnvironmentalData, BehavioralData


class FeatureExtractor:
    """Extract features from verification request with hard behavioral thresholds"""
    
    # ===== HARD BEHAVIORAL THRESHOLDS (Human Baselines) =====
    # These are stricter thresholds for detecting Selenium bots
    HUMAN_BASELINES = {
        'min_mouse_movements': 15,      # Minimum mouse movements for human
        'min_mouse_clicks': 1,          # Minimum clicks for form interaction
        'min_scroll_events': 1,         # Minimum scrolls (reading behavior)
        'min_session_time_ms': 2000,    # Minimum 2 seconds on page
        'min_first_interaction_ms': 100, # Humans need at least 100ms to react
        'min_direction_changes': 5,     # Natural mouse movement has direction changes
        'min_jitter_score': 0.01,       # Humans have micro-movements/jitter
        'max_straight_line_ratio': 0.80, # Humans don't move in straight lines
        'min_velocity_variance': 25,    # Humans have variable mouse speed
        'min_timing_entropy': 0.20,     # Event timing should have randomness
        'min_movement_entropy': 0.20,   # Movement patterns should have randomness
    }
    
    # 20% threshold - below this is HARD BOT
    HARD_BOT_THRESHOLD = 0.20
    
    # Feature names for model training
    FEATURE_NAMES = [
        # Environmental Features
        'env_webdriver',
        'env_automation_flag_count',
        'env_has_plugins',
        'env_plugin_count',
        'env_screen_ratio',
        'env_color_depth',
        'env_device_pixel_ratio',
        'env_has_touch',
        'env_hardware_concurrency',
        'env_device_memory',
        'env_has_local_storage',
        'env_has_session_storage',
        'env_has_indexed_db',
        'env_canvas_hash_length',
        'env_webgl_hash_length',
        'env_audio_hash_length',
        'env_timezone_offset',
        'env_language_count',
        
        # Mouse Movement Features
        'mouse_movement_count',
        'mouse_total_distance',
        'mouse_avg_velocity',
        'mouse_max_velocity',
        'mouse_straight_line_ratio',
        'mouse_direction_changes',
        'mouse_pause_count',
        'mouse_jitter_score',
        'mouse_click_count',
        'mouse_velocity_std',
        'mouse_acceleration_std',
        
        # Keyboard Features
        'key_press_count',
        'key_avg_dwell_time',
        'key_avg_flight_time',
        'key_typing_speed',
        'key_error_rate',
        'key_rhythm_consistency',
        'key_dwell_time_std',
        'key_flight_time_std',
        
        # Scroll Features
        'scroll_event_count',
        'scroll_total_distance',
        'scroll_avg_velocity',
        'scroll_smoothness',
        'scroll_direction_changes',
        
        # Touch Features
        'touch_gesture_count',
        'touch_multi_touch_count',
        
        # Focus Features
        'focus_event_count',
        'focus_total_time',
        'focus_blur_count',
        'focus_visibility_changes',
        
        # Timing Features
        'timing_page_load',
        'timing_first_interaction',
        'timing_total_interaction',
        'timing_idle_period_count',
        'timing_avg_idle_duration',
        'timing_interaction_gap_std',
        
        # NEW: Entropy/Randomness Features (detect programmatic patterns)
        'timing_gap_entropy',           # Entropy of time gaps between events
        'mouse_velocity_entropy',       # Entropy of velocity distribution
        'mouse_position_entropy',       # Entropy of click/movement positions
        'scroll_interval_regularity',   # How regular are scroll intervals (high = bot)
        'click_interval_variance',      # Variance in click timing
        'movement_acceleration_entropy', # Entropy of acceleration changes
        
        # NEW: Hard Threshold Violation Flags (0 or 1)
        'hard_fail_mouse_movements',    # Below 20% of human baseline
        'hard_fail_clicks',             # Below 20% of human baseline
        'hard_fail_scrolls',            # Below 20% of human baseline
        'hard_fail_session_time',       # Below 20% of human baseline
        'hard_fail_instant_interaction', # Reacted faster than humanly possible
        'hard_fail_no_variance',        # Perfect mechanical precision
        'hard_fail_low_entropy',        # Programmatic event timing
    ]
    
    def extract_features(self, request: VerificationRequest) -> Tuple[np.ndarray, List[str]]:
        """Extract all features from verification request"""
        features = []
        anomalies = []
        
        # Environmental features
        env_features, env_anomalies = self._extract_environmental_features(request.environmental)
        features.extend(env_features)
        anomalies.extend(env_anomalies)
        
        # Behavioral features
        behav_features, behav_anomalies = self._extract_behavioral_features(request.behavioral)
        features.extend(behav_features)
        anomalies.extend(behav_anomalies)
        
        # NEW: Entropy/randomness features
        entropy_features, entropy_anomalies = self._extract_entropy_features(request.behavioral)
        features.extend(entropy_features)
        anomalies.extend(entropy_anomalies)
        
        # NEW: Hard threshold violation checks
        hard_fail_features, hard_fail_anomalies = self._check_hard_thresholds(request.behavioral)
        features.extend(hard_fail_features)
        anomalies.extend(hard_fail_anomalies)
        
        return np.array(features), anomalies
    
    def _calculate_entropy(self, values: List[float], bins: int = 10) -> float:
        """Calculate Shannon entropy of a distribution (0 = uniform/mechanical, 1 = random/human)"""
        if len(values) < 2:
            return 0.0
        
        # Normalize values
        arr = np.array(values)
        if np.std(arr) == 0:
            return 0.0  # All same values = no entropy
        
        # Create histogram and calculate entropy
        hist, _ = np.histogram(arr, bins=bins, density=True)
        hist = hist[hist > 0]  # Remove zeros
        if len(hist) == 0:
            return 0.0
        
        # Normalize to probability distribution
        hist = hist / hist.sum()
        entropy = -np.sum(hist * np.log2(hist + 1e-10))
        
        # Normalize to 0-1 range
        max_entropy = np.log2(bins)
        return min(1.0, entropy / max_entropy) if max_entropy > 0 else 0.0
    
    def _extract_environmental_features(self, data: EnvironmentalData) -> Tuple[List[float], List[str]]:
        """Extract features from environmental data"""
        features = []
        anomalies = []
        
        # Webdriver detection
        features.append(1.0 if data.features.webdriver else 0.0)
        if data.features.webdriver:
            anomalies.append("webdriver_detected")
        
        # Automation flags
        automation_count = len(data.features.automationFlags)
        features.append(float(automation_count))
        if automation_count > 0:
            anomalies.append(f"automation_flags:{','.join(data.features.automationFlags)}")
        
        # Plugin analysis
        has_plugins = len(data.browser.plugins) > 0
        features.append(1.0 if has_plugins else 0.0)
        features.append(float(len(data.browser.plugins)))
        
        # Screen analysis
        if data.screen.height > 0:
            screen_ratio = data.screen.width / data.screen.height
        else:
            screen_ratio = 0.0
        features.append(screen_ratio)
        features.append(float(data.screen.colorDepth))
        features.append(data.screen.devicePixelRatio)
        
        # Hardware
        features.append(1.0 if data.hardware.hasTouch else 0.0)
        features.append(float(data.hardware.hardwareConcurrency))
        features.append(float(data.hardware.deviceMemory or 0))
        
        # Storage
        features.append(1.0 if data.features.localStorage else 0.0)
        features.append(1.0 if data.features.sessionStorage else 0.0)
        features.append(1.0 if data.features.indexedDB else 0.0)
        
        if not data.features.localStorage and not data.features.sessionStorage:
            anomalies.append("no_storage_support")
        
        # Fingerprint hashes
        features.append(float(len(data.canvasHash)))
        features.append(float(len(data.webgl.hash)))
        features.append(float(len(data.audioHash)))
        
        if len(data.canvasHash) == 0 and len(data.webgl.hash) == 0:
            anomalies.append("missing_fingerprints")
        
        # Timezone
        features.append(float(data.timezone.offset))
        
        # Languages
        features.append(float(len(data.browser.languages)))
        
        return features, anomalies
    
    def _extract_behavioral_features(self, data: BehavioralData) -> Tuple[List[float], List[str]]:
        """Extract features from behavioral data"""
        features = []
        anomalies = []
        
        # Mouse features
        mouse = data.mouse
        features.append(float(len(mouse.movements)))
        features.append(mouse.movementStats.totalDistance)
        features.append(mouse.movementStats.averageVelocity)
        features.append(mouse.movementStats.maxVelocity)
        features.append(mouse.movementStats.straightLineRatio)
        features.append(float(mouse.movementStats.directionChanges))
        features.append(float(mouse.movementStats.pauseCount))
        features.append(mouse.movementStats.jitterScore)
        features.append(float(len(mouse.clicks)))
        
        # Calculate velocity standard deviation
        if len(mouse.movements) > 1:
            velocities = [m.velocity for m in mouse.movements]
            velocity_std = np.std(velocities)
            accelerations = [m.acceleration for m in mouse.movements]
            acceleration_std = np.std(accelerations)
        else:
            velocity_std = 0.0
            acceleration_std = 0.0
        features.append(velocity_std)
        features.append(acceleration_std)
        
        # Bot-like mouse behavior detection
        if len(mouse.movements) == 0:
            anomalies.append("no_mouse_movement")
        elif mouse.movementStats.straightLineRatio > 0.95:
            anomalies.append("perfectly_straight_mouse")
        elif mouse.movementStats.jitterScore < 0.01 and len(mouse.movements) > 10:
            anomalies.append("unnaturally_smooth_mouse")
        
        # Keyboard features
        keyboard = data.keyboard
        features.append(float(len(keyboard.keyPresses)))
        features.append(keyboard.typingStats.averageDwellTime)
        features.append(keyboard.typingStats.averageFlightTime)
        features.append(keyboard.typingStats.typingSpeed)
        features.append(keyboard.typingStats.errorRate)
        features.append(keyboard.typingStats.rhythmConsistency)
        
        # Calculate keystroke timing standard deviations
        if len(keyboard.keyPresses) > 1:
            dwell_times = [k.dwellTime for k in keyboard.keyPresses]
            flight_times = [k.flightTime for k in keyboard.keyPresses if k.flightTime > 0]
            dwell_std = np.std(dwell_times)
            flight_std = np.std(flight_times) if flight_times else 0.0
        else:
            dwell_std = 0.0
            flight_std = 0.0
        features.append(dwell_std)
        features.append(flight_std)
        
        # Bot-like keyboard behavior
        if keyboard.typingStats.rhythmConsistency > 0.99 and len(keyboard.keyPresses) > 10:
            anomalies.append("perfectly_consistent_typing")
        
        # Scroll features
        scroll = data.scroll
        features.append(float(len(scroll.events)))
        features.append(scroll.stats.totalScroll)
        features.append(scroll.stats.averageVelocity)
        features.append(scroll.stats.smoothness)
        features.append(float(scroll.stats.directionChanges))
        
        # Touch features
        touch = data.touch
        features.append(float(len(touch.gestures)))
        features.append(float(touch.multiTouchEvents))
        
        # Focus features
        focus = data.focus
        features.append(float(len(focus.focusEvents)))
        features.append(float(focus.totalFocusTime))
        features.append(float(focus.blurCount))
        features.append(float(focus.visibilityChanges))
        
        # Timing features
        timing = data.timing
        features.append(float(timing.pageLoadTime))
        features.append(float(timing.timeToFirstInteraction))
        features.append(float(timing.totalInteractionTime))
        features.append(float(len(timing.idlePeriods)))
        
        # Average idle duration
        if timing.idlePeriods:
            avg_idle = np.mean(timing.idlePeriods)
        else:
            avg_idle = 0.0
        features.append(avg_idle)
        
        # Interaction gap standard deviation
        if timing.interactionGaps:
            gap_std = np.std(timing.interactionGaps)
        else:
            gap_std = 0.0
        features.append(gap_std)
        
        # Timing anomalies
        if timing.timeToFirstInteraction == -1:
            anomalies.append("no_interaction")
        elif timing.timeToFirstInteraction < 100:
            anomalies.append("instant_interaction")
        
        return features, anomalies
    
    def get_feature_names(self) -> List[str]:
        """Get list of feature names"""
        return self.FEATURE_NAMES.copy()
    
    def _extract_entropy_features(self, data: BehavioralData) -> Tuple[List[float], List[str]]:
        """Extract entropy/randomness features to detect programmatic patterns"""
        features = []
        anomalies = []
        
        # 1. Timing gap entropy - how random are gaps between events
        timing = data.timing
        if timing.interactionGaps and len(timing.interactionGaps) > 2:
            timing_gap_entropy = self._calculate_entropy(timing.interactionGaps)
        else:
            timing_gap_entropy = 0.0
        features.append(timing_gap_entropy)
        
        # 2. Mouse velocity entropy - humans have varied speeds
        mouse = data.mouse
        if len(mouse.movements) > 5:
            velocities = [m.velocity for m in mouse.movements]
            mouse_velocity_entropy = self._calculate_entropy(velocities)
        else:
            mouse_velocity_entropy = 0.0
        features.append(mouse_velocity_entropy)
        
        # 3. Mouse position entropy - clicks should be distributed
        if len(mouse.clicks) > 2:
            click_positions = [c.x + c.y for c in mouse.clicks]  # Simple position hash
            mouse_position_entropy = self._calculate_entropy(click_positions)
        else:
            mouse_position_entropy = 0.0
        features.append(mouse_position_entropy)
        
        # 4. Scroll interval regularity - bots scroll at regular intervals
        scroll = data.scroll
        if len(scroll.events) > 2:
            scroll_times = [e.timestamp for e in scroll.events]
            scroll_intervals = np.diff(scroll_times)
            if len(scroll_intervals) > 1 and np.mean(scroll_intervals) > 0:
                # Coefficient of variation - low = regular/mechanical
                scroll_regularity = 1.0 - min(1.0, np.std(scroll_intervals) / (np.mean(scroll_intervals) + 1e-10))
            else:
                scroll_regularity = 1.0  # Suspicious - too regular
        else:
            scroll_regularity = 0.5  # Neutral
        features.append(scroll_regularity)
        
        # 5. Click interval variance - humans have variable click timing
        if len(mouse.clicks) > 2:
            click_times = [c.timestamp for c in mouse.clicks]
            click_intervals = np.diff(click_times)
            click_interval_variance = np.var(click_intervals) if len(click_intervals) > 1 else 0.0
        else:
            click_interval_variance = 0.0
        features.append(click_interval_variance)
        
        # 6. Movement acceleration entropy
        if len(mouse.movements) > 5:
            accelerations = [m.acceleration for m in mouse.movements]
            accel_entropy = self._calculate_entropy(accelerations)
        else:
            accel_entropy = 0.0
        features.append(accel_entropy)
        
        # Flag low entropy as suspicious
        if timing_gap_entropy < self.HUMAN_BASELINES['min_timing_entropy'] and len(timing.interactionGaps) > 5:
            anomalies.append("low_timing_entropy")
        
        if mouse_velocity_entropy < self.HUMAN_BASELINES['min_movement_entropy'] and len(mouse.movements) > 10:
            anomalies.append("low_movement_entropy")
        
        return features, anomalies
    
    def _check_hard_thresholds(self, data: BehavioralData) -> Tuple[List[float], List[str]]:
        """Check hard behavioral thresholds - below 20% of human baseline = HARD BOT"""
        features = []
        anomalies = []
        baselines = self.HUMAN_BASELINES
        threshold = self.HARD_BOT_THRESHOLD
        
        # 1. Mouse movements check
        mouse_count = len(data.mouse.movements)
        hard_fail_mouse = 1.0 if mouse_count < (baselines['min_mouse_movements'] * threshold) else 0.0
        features.append(hard_fail_mouse)
        if hard_fail_mouse:
            anomalies.append(f"HARD_FAIL:mouse_movements({mouse_count}<{int(baselines['min_mouse_movements'] * threshold)})")
        
        # 2. Click count check
        click_count = len(data.mouse.clicks)
        hard_fail_clicks = 1.0 if click_count < (baselines['min_mouse_clicks'] * threshold) else 0.0
        features.append(hard_fail_clicks)
        if hard_fail_clicks:
            anomalies.append(f"HARD_FAIL:clicks({click_count}<{int(baselines['min_mouse_clicks'] * threshold)})")
        
        # 3. Scroll events check
        scroll_count = len(data.scroll.events)
        hard_fail_scrolls = 1.0 if scroll_count < (baselines['min_scroll_events'] * threshold) else 0.0
        features.append(hard_fail_scrolls)
        if hard_fail_scrolls:
            anomalies.append(f"HARD_FAIL:scrolls({scroll_count}<{int(baselines['min_scroll_events'] * threshold)})")
        
        # 4. Session time check
        session_time = data.timing.totalInteractionTime
        hard_fail_session = 1.0 if session_time < (baselines['min_session_time_ms'] * threshold) else 0.0
        features.append(hard_fail_session)
        if hard_fail_session:
            anomalies.append(f"HARD_FAIL:session_time({session_time}ms<{int(baselines['min_session_time_ms'] * threshold)}ms)")
        
        # 5. Instant interaction check (reacted faster than humanly possible)
        first_interaction = data.timing.timeToFirstInteraction
        hard_fail_instant = 1.0 if (first_interaction >= 0 and first_interaction < baselines['min_first_interaction_ms'] * threshold) else 0.0
        features.append(hard_fail_instant)
        if hard_fail_instant:
            anomalies.append(f"HARD_FAIL:instant_interaction({first_interaction}ms<{int(baselines['min_first_interaction_ms'] * threshold)}ms)")
        
        # 6. No variance check - mechanical precision
        velocity_std = 0.0
        if len(data.mouse.movements) > 5:
            velocities = [m.velocity for m in data.mouse.movements]
            velocity_std = np.std(velocities)
        jitter = data.mouse.movementStats.jitterScore
        straight_ratio = data.mouse.movementStats.straightLineRatio
        
        no_variance_conditions = [
            velocity_std < baselines['min_velocity_variance'] and len(data.mouse.movements) > 10,
            jitter < baselines['min_jitter_score'] and len(data.mouse.movements) > 10,
            straight_ratio > baselines['max_straight_line_ratio'] and len(data.mouse.movements) > 10,
        ]
        hard_fail_variance = 1.0 if sum(no_variance_conditions) >= 2 else 0.0
        features.append(hard_fail_variance)
        if hard_fail_variance:
            anomalies.append(f"HARD_FAIL:mechanical_precision(vel_std={velocity_std:.1f},jitter={jitter:.3f},straight={straight_ratio:.2f})")
        
        # 7. Low entropy check - programmatic event timing
        timing_entropy = 0.0
        if data.timing.interactionGaps and len(data.timing.interactionGaps) > 5:
            timing_entropy = self._calculate_entropy(data.timing.interactionGaps)
        
        movement_entropy = 0.0
        if len(data.mouse.movements) > 10:
            velocities = [m.velocity for m in data.mouse.movements]
            movement_entropy = self._calculate_entropy(velocities)
        
        hard_fail_entropy = 1.0 if (timing_entropy < baselines['min_timing_entropy'] and movement_entropy < baselines['min_movement_entropy'] and len(data.mouse.movements) > 10) else 0.0
        features.append(hard_fail_entropy)
        if hard_fail_entropy:
            anomalies.append(f"HARD_FAIL:low_entropy(timing={timing_entropy:.2f},movement={movement_entropy:.2f})")
        
        return features, anomalies
    
    def count_hard_failures(self, anomalies: List[str]) -> int:
        """Count number of hard failures in anomalies list"""
        return sum(1 for a in anomalies if a.startswith("HARD_FAIL:"))


# Global instance
feature_extractor = FeatureExtractor()
