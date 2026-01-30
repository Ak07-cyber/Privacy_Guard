"""
Feature Engineering for Bot Detection
Transforms raw data into ML-ready features
"""

import numpy as np
from typing import Dict, List, Any, Tuple
from app.api.models import VerificationRequest, EnvironmentalData, BehavioralData


class FeatureExtractor:
    """Extract features from verification request for ML model"""
    
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
        
        return np.array(features), anomalies
    
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


# Global instance
feature_extractor = FeatureExtractor()
