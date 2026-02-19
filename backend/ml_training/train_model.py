"""
ML Model Training Script for Bot Detection
Generates synthetic data with ADVERSARIAL bot samples and trains XGBoost classifier
Includes noise injection to make model robust against Selenium automation
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from xgboost import XGBClassifier
import joblib
import os
from pathlib import Path
import json


# Feature names (must match FeatureExtractor - UPDATED with new features)
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
    
    # NEW: Entropy/Randomness Features
    'timing_gap_entropy',
    'mouse_velocity_entropy',
    'mouse_position_entropy',
    'scroll_interval_regularity',
    'click_interval_variance',
    'movement_acceleration_entropy',
    
    # NEW: Hard Threshold Violation Flags
    'hard_fail_mouse_movements',
    'hard_fail_clicks',
    'hard_fail_scrolls',
    'hard_fail_session_time',
    'hard_fail_instant_interaction',
    'hard_fail_no_variance',
    'hard_fail_low_entropy',
]


def calculate_entropy_score(values, is_human=True):
    """Simulate entropy calculation - humans have higher entropy"""
    if is_human:
        return np.random.uniform(0.4, 0.9)  # High entropy for humans
    else:
        return np.random.uniform(0.05, 0.35)  # Low entropy for bots


def generate_human_sample() -> np.ndarray:
    """Generate synthetic human-like behavior data with realistic entropy"""
    sample = []
    
    # Environmental Features (humans have normal browsers)
    sample.append(0)  # webdriver = False
    sample.append(0)  # automation flags = 0
    sample.append(np.random.choice([0, 1], p=[0.1, 0.9]))  # has_plugins
    sample.append(np.random.randint(0, 10))  # plugin_count
    sample.append(np.random.uniform(1.3, 1.9))  # screen_ratio (common ratios)
    sample.append(np.random.choice([24, 32]))  # color_depth
    sample.append(np.random.choice([1, 1.5, 2, 2.5, 3]))  # device_pixel_ratio
    sample.append(np.random.choice([0, 1], p=[0.3, 0.7]))  # has_touch
    sample.append(np.random.choice([2, 4, 6, 8, 12, 16]))  # hardware_concurrency
    sample.append(np.random.choice([2, 4, 8, 16]))  # device_memory
    sample.append(1)  # has_local_storage
    sample.append(1)  # has_session_storage
    sample.append(1)  # has_indexed_db
    sample.append(np.random.randint(6, 10))  # canvas_hash_length
    sample.append(np.random.randint(6, 10))  # webgl_hash_length
    sample.append(np.random.randint(6, 10))  # audio_hash_length
    sample.append(np.random.randint(-720, 720))  # timezone_offset
    sample.append(np.random.randint(1, 5))  # language_count
    
    # Mouse Movement Features (humans have natural, imperfect movements)
    sample.append(np.random.randint(50, 500))  # movement_count (higher minimum)
    sample.append(np.random.uniform(500, 5000))  # total_distance
    sample.append(np.random.uniform(100, 800))  # avg_velocity
    sample.append(np.random.uniform(500, 2000))  # max_velocity
    sample.append(np.random.uniform(0.1, 0.5))  # straight_line_ratio (NOT straight - stricter)
    sample.append(np.random.randint(15, 150))  # direction_changes (higher minimum)
    sample.append(np.random.randint(5, 50))  # pause_count
    sample.append(np.random.uniform(0.03, 0.25))  # jitter_score (higher minimum)
    sample.append(np.random.randint(2, 20))  # click_count (at least 2)
    sample.append(np.random.uniform(60, 350))  # velocity_std (higher minimum)
    sample.append(np.random.uniform(100, 1000))  # acceleration_std
    
    # Keyboard Features (humans have variable typing)
    sample.append(np.random.randint(0, 200))  # key_press_count
    sample.append(np.random.uniform(80, 200))  # avg_dwell_time
    sample.append(np.random.uniform(100, 300))  # avg_flight_time
    sample.append(np.random.uniform(150, 400))  # typing_speed
    sample.append(np.random.uniform(0.02, 0.15))  # error_rate
    sample.append(np.random.uniform(0.3, 0.80))  # rhythm_consistency (NOT perfect - stricter)
    sample.append(np.random.uniform(20, 80))  # dwell_time_std
    sample.append(np.random.uniform(30, 100))  # flight_time_std
    
    # Scroll Features (humans scroll naturally)
    sample.append(np.random.randint(5, 50))  # scroll_event_count
    sample.append(np.random.uniform(200, 3000))  # scroll_total_distance
    sample.append(np.random.uniform(100, 800))  # scroll_avg_velocity
    sample.append(np.random.uniform(0.25, 0.70))  # scroll_smoothness (NOT too smooth)
    sample.append(np.random.randint(1, 10))  # scroll_direction_changes
    
    # Touch Features
    sample.append(np.random.randint(0, 20))  # touch_gesture_count
    sample.append(np.random.randint(0, 5))  # multi_touch_count
    
    # Focus Features
    sample.append(np.random.randint(1, 10))  # focus_event_count
    sample.append(np.random.randint(5000, 60000))  # focus_total_time
    sample.append(np.random.randint(0, 5))  # blur_count
    sample.append(np.random.randint(0, 3))  # visibility_changes
    
    # Timing Features (humans take time)
    sample.append(np.random.randint(500, 5000))  # page_load_time
    sample.append(np.random.randint(300, 5000))  # time_to_first_interaction (min 300ms)
    sample.append(np.random.randint(5000, 120000))  # total_interaction_time (min 5s)
    sample.append(np.random.randint(1, 10))  # idle_period_count
    sample.append(np.random.uniform(1000, 10000))  # avg_idle_duration
    sample.append(np.random.uniform(200, 2500))  # interaction_gap_std (higher variance)
    
    # NEW: Entropy Features (humans have HIGH entropy)
    sample.append(np.random.uniform(0.45, 0.95))  # timing_gap_entropy
    sample.append(np.random.uniform(0.45, 0.90))  # mouse_velocity_entropy
    sample.append(np.random.uniform(0.40, 0.85))  # mouse_position_entropy
    sample.append(np.random.uniform(0.15, 0.55))  # scroll_interval_regularity (LOW for humans)
    sample.append(np.random.uniform(5000, 50000))  # click_interval_variance (HIGH for humans)
    sample.append(np.random.uniform(0.40, 0.85))  # movement_acceleration_entropy
    
    # NEW: Hard Fail Flags (all 0 for humans)
    sample.append(0)  # hard_fail_mouse_movements
    sample.append(0)  # hard_fail_clicks
    sample.append(0)  # hard_fail_scrolls
    sample.append(0)  # hard_fail_session_time
    sample.append(0)  # hard_fail_instant_interaction
    sample.append(0)  # hard_fail_no_variance
    sample.append(0)  # hard_fail_low_entropy
    
    return np.array(sample)


def generate_bot_sample() -> np.ndarray:
    """
    Generate synthetic bot-like behavior data with ADVERSARIAL samples
    Includes 'smart bots' that try to mimic human behavior (Selenium stealth)
    """
    sample = []
    
    # Choose bot type with weighted distribution
    # 30% basic bots, 40% smart bots (Selenium stealth), 30% scripted bots
    bot_type = np.random.choice(
        ['basic_bot', 'selenium_stealth', 'scripted_bot', 'speed_bot', 'no_interaction'],
        p=[0.20, 0.35, 0.20, 0.15, 0.10]
    )
    
    # Environmental Features - varies by bot sophistication
    if bot_type == 'selenium_stealth':
        # Stealth bots try to hide webdriver flag (undetected-chromedriver)
        sample.append(np.random.choice([0, 1], p=[0.7, 0.3]))  # Often hides webdriver
        sample.append(np.random.choice([0, 1], p=[0.6, 0.4]))  # May hide automation flags
    else:
        sample.append(np.random.choice([0, 1], p=[0.2, 0.8]))  # webdriver usually true
        sample.append(np.random.choice([0, 1, 2, 3], p=[0.15, 0.45, 0.30, 0.10]))  # automation flags
    
    sample.append(np.random.choice([0, 1], p=[0.5, 0.5]))  # plugins
    sample.append(np.random.randint(0, 5))  # plugin_count
    sample.append(np.random.uniform(1.3, 1.9))  # screen_ratio
    sample.append(np.random.choice([24, 32]))  # color_depth
    sample.append(1)  # device_pixel_ratio (often default)
    sample.append(0)  # usually no touch
    sample.append(np.random.choice([1, 2, 4, 8]))  # hardware_concurrency
    sample.append(np.random.choice([0, 2, 4, 8]))  # device_memory
    sample.append(np.random.choice([0, 1], p=[0.2, 0.8]))  # local_storage
    sample.append(np.random.choice([0, 1], p=[0.2, 0.8]))  # session_storage
    sample.append(np.random.choice([0, 1], p=[0.15, 0.85]))  # indexed_db
    sample.append(np.random.choice([0, 8], p=[0.3, 0.7]))  # canvas_hash
    sample.append(np.random.choice([0, 8], p=[0.3, 0.7]))  # webgl_hash
    sample.append(np.random.choice([0, 8], p=[0.4, 0.6]))  # audio_hash
    sample.append(0)  # timezone (often UTC)
    sample.append(1)  # language_count
    
    # ===== BOT-TYPE SPECIFIC BEHAVIORAL FEATURES =====
    
    if bot_type == 'no_interaction':
        # Bot that just submits form without interaction
        _add_no_interaction_features(sample)
    
    elif bot_type == 'basic_bot':
        # Basic automation - minimal or perfect mouse movements
        _add_basic_bot_features(sample)
    
    elif bot_type == 'selenium_stealth':
        # ADVERSARIAL: Smart bot trying to mimic human behavior
        # This is the key type we need to detect!
        _add_selenium_stealth_features(sample)
    
    elif bot_type == 'scripted_bot':
        # Scripted mouse/keyboard with some variation
        _add_scripted_bot_features(sample)
    
    elif bot_type == 'speed_bot':
        # Very fast automation
        _add_speed_bot_features(sample)
    
    return np.array(sample)


def _add_no_interaction_features(sample):
    """Bot with zero or minimal interaction"""
    # Mouse - zero
    sample.extend([0, 0, 0, 0, 0, 0, 0, 0, np.random.randint(0, 1), 0, 0])
    
    # Keyboard - zero
    sample.extend([0, 0, 0, 0, 0, 0, 0, 0])
    
    # Scroll - zero
    sample.extend([0, 0, 0, 0, 0])
    
    # Touch - zero
    sample.extend([0, 0])
    
    # Focus - minimal
    sample.extend([np.random.randint(0, 1), np.random.randint(100, 1000), 0, 0])
    
    # Timing - instant
    sample.extend([
        np.random.randint(100, 500),  # page_load
        np.random.choice([-1, np.random.randint(0, 50)]),  # first_interaction (instant or none)
        np.random.randint(50, 500),  # total_time (very short)
        0, 0, 0  # no idle
    ])
    
    # Entropy - zero (no events to measure)
    sample.extend([0, 0, 0, 0.5, 0, 0])
    
    # Hard fail flags - MANY
    sample.extend([1, 1, 1, 1, 1, 0, 1])  # Multiple hard fails


def _add_basic_bot_features(sample):
    """Basic automation with obvious patterns"""
    # Mouse - perfect straight lines
    sample.append(np.random.randint(10, 50))  # low movement count
    sample.append(np.random.uniform(100, 500))  # short distance
    sample.append(np.random.uniform(200, 400))  # consistent velocity
    sample.append(np.random.uniform(250, 450))  # max close to avg
    sample.append(np.random.uniform(0.85, 0.99))  # very straight
    sample.append(np.random.randint(0, 5))  # few direction changes
    sample.append(0)  # no pauses
    sample.append(np.random.uniform(0, 0.008))  # no jitter
    sample.append(np.random.randint(1, 3))  # few clicks
    sample.append(np.random.uniform(0, 25))  # very low velocity std
    sample.append(np.random.uniform(0, 50))  # very low accel std
    
    # Keyboard - zero or perfect
    if np.random.random() < 0.5:
        sample.extend([0, 0, 0, 0, 0, 0, 0, 0])
    else:
        sample.extend([
            np.random.randint(10, 50),  # key presses
            np.random.uniform(40, 80),  # very consistent dwell
            np.random.uniform(40, 80),  # very consistent flight
            np.random.uniform(400, 800),  # fast typing
            0,  # no errors
            np.random.uniform(0.95, 1.0),  # perfect rhythm
            np.random.uniform(0, 8),  # very low std
            np.random.uniform(0, 8),  # very low std
        ])
    
    # Scroll - mechanical
    sample.extend([
        np.random.randint(0, 5),  # few scrolls
        np.random.uniform(0, 300),  # short distance
        np.random.uniform(0, 150),  # low velocity
        np.random.uniform(0.85, 1.0),  # very smooth (mechanical)
        np.random.randint(0, 2),  # no direction changes
    ])
    
    # Touch
    sample.extend([0, 0])
    
    # Focus
    sample.extend([np.random.randint(0, 2), np.random.randint(500, 5000), 0, 0])
    
    # Timing
    sample.extend([
        np.random.randint(100, 1000),
        np.random.randint(0, 150),  # very fast first interaction
        np.random.randint(500, 3000),  # short session
        0, 0,
        np.random.uniform(0, 30),  # very consistent gaps
    ])
    
    # Entropy - LOW (mechanical)
    sample.extend([
        np.random.uniform(0.05, 0.25),  # low timing entropy
        np.random.uniform(0.05, 0.20),  # low velocity entropy
        np.random.uniform(0.05, 0.25),  # low position entropy
        np.random.uniform(0.80, 0.98),  # HIGH regularity (mechanical)
        np.random.uniform(0, 500),  # low click variance
        np.random.uniform(0.05, 0.20),  # low accel entropy
    ])
    
    # Hard fail flags
    sample.extend([
        1,  # hard_fail_mouse_movements
        np.random.choice([0, 1]),
        1,  # hard_fail_scrolls
        1,  # hard_fail_session_time
        1,  # hard_fail_instant_interaction
        1,  # hard_fail_no_variance
        1,  # hard_fail_low_entropy
    ])


def _add_selenium_stealth_features(sample):
    """
    ADVERSARIAL: Selenium with stealth trying to mimic human
    This bot adds random delays, varied movements, but still has telltale patterns:
    - Timing events are too regular (low entropy)
    - Movement patterns lack true randomness
    - Velocity variations follow programmatic distributions
    """
    # Mouse - tries to look human but has patterns
    sample.append(np.random.randint(30, 120))  # reasonable movement count
    sample.append(np.random.uniform(300, 1500))  # reasonable distance
    sample.append(np.random.uniform(150, 500))  # varied velocity
    sample.append(np.random.uniform(400, 900))  # max velocity
    sample.append(np.random.uniform(0.45, 0.75))  # tries to not be straight (but still straighter than human)
    sample.append(np.random.randint(5, 25))  # adds some direction changes
    sample.append(np.random.randint(1, 8))  # adds some pauses
    sample.append(np.random.uniform(0.008, 0.025))  # adds small jitter (but less than human)
    sample.append(np.random.randint(2, 8))  # several clicks
    sample.append(np.random.uniform(25, 80))  # some velocity variation (but less than human)
    sample.append(np.random.uniform(30, 150))  # some accel variation
    
    # Keyboard - tries to look human
    if np.random.random() < 0.3:
        sample.extend([0, 0, 0, 0, 0, 0, 0, 0])
    else:
        sample.extend([
            np.random.randint(20, 100),
            np.random.uniform(70, 140),  # tries varied dwell
            np.random.uniform(80, 180),  # tries varied flight
            np.random.uniform(200, 450),
            np.random.uniform(0, 0.05),  # maybe small errors
            np.random.uniform(0.75, 0.92),  # tries imperfect rhythm
            np.random.uniform(8, 30),  # some std but lower than human
            np.random.uniform(10, 40),
        ])
    
    # Scroll - tries to look natural
    sample.extend([
        np.random.randint(3, 15),  # some scrolls
        np.random.uniform(150, 800),
        np.random.uniform(100, 400),
        np.random.uniform(0.55, 0.80),  # tries to not be too smooth
        np.random.randint(1, 5),
    ])
    
    # Touch
    sample.extend([0, 0])
    
    # Focus
    sample.extend([np.random.randint(1, 5), np.random.randint(3000, 20000), np.random.randint(0, 2), 0])
    
    # Timing - adds delays but still detectable patterns
    sample.extend([
        np.random.randint(500, 2000),
        np.random.randint(150, 800),  # tries slower first interaction
        np.random.randint(3000, 15000),  # longer session
        np.random.randint(0, 3),
        np.random.uniform(500, 3000),
        np.random.uniform(50, 200),  # some gap variation but less than human
    ])
    
    # ===== KEY DETECTION SIGNALS: LOW ENTROPY =====
    # This is where stealth bots fail - their "randomness" is programmatic
    sample.extend([
        np.random.uniform(0.15, 0.40),  # LOW timing entropy (programmatic delays)
        np.random.uniform(0.18, 0.42),  # LOW velocity entropy (programmatic movement)
        np.random.uniform(0.15, 0.38),  # LOW position entropy (click targets predictable)
        np.random.uniform(0.60, 0.85),  # MEDIUM-HIGH regularity (still somewhat mechanical)
        np.random.uniform(500, 5000),  # LOW-MEDIUM click variance
        np.random.uniform(0.15, 0.40),  # LOW acceleration entropy
    ])
    
    # Hard fail flags - some may pass, but entropy usually fails
    sample.extend([
        np.random.choice([0, 1], p=[0.6, 0.4]),  # might pass mouse count
        0,  # clicks usually pass
        np.random.choice([0, 1], p=[0.7, 0.3]),  # might pass scrolls
        np.random.choice([0, 1], p=[0.7, 0.3]),  # might pass session time
        np.random.choice([0, 1], p=[0.6, 0.4]),  # might pass instant check
        np.random.choice([0, 1], p=[0.4, 0.6]),  # often fails variance
        np.random.choice([0, 1], p=[0.3, 0.7]),  # usually fails entropy
    ])


def _add_scripted_bot_features(sample):
    """Scripted bot with some variation"""
    # Mouse
    sample.append(np.random.randint(20, 80))
    sample.append(np.random.uniform(200, 1000))
    sample.append(np.random.uniform(250, 550))
    sample.append(np.random.uniform(350, 650))
    sample.append(np.random.uniform(0.60, 0.88))  # somewhat straight
    sample.append(np.random.randint(3, 15))
    sample.append(np.random.randint(0, 4))
    sample.append(np.random.uniform(0.005, 0.018))
    sample.append(np.random.randint(1, 6))
    sample.append(np.random.uniform(15, 55))
    sample.append(np.random.uniform(25, 120))
    
    # Keyboard
    if np.random.random() < 0.4:
        sample.extend([0, 0, 0, 0, 0, 0, 0, 0])
    else:
        sample.extend([
            np.random.randint(15, 80),
            np.random.uniform(55, 110),
            np.random.uniform(60, 130),
            np.random.uniform(350, 650),
            0,
            np.random.uniform(0.88, 0.97),
            np.random.uniform(5, 20),
            np.random.uniform(5, 25),
        ])
    
    # Scroll
    sample.extend([
        np.random.randint(1, 8),
        np.random.uniform(50, 500),
        np.random.uniform(80, 350),
        np.random.uniform(0.70, 0.92),
        np.random.randint(0, 3),
    ])
    
    # Touch
    sample.extend([0, 0])
    
    # Focus
    sample.extend([np.random.randint(0, 3), np.random.randint(1000, 10000), 0, 0])
    
    # Timing
    sample.extend([
        np.random.randint(200, 1500),
        np.random.randint(50, 300),
        np.random.randint(1000, 8000),
        0,
        0,
        np.random.uniform(20, 100),
    ])
    
    # Entropy - LOW
    sample.extend([
        np.random.uniform(0.10, 0.32),
        np.random.uniform(0.12, 0.30),
        np.random.uniform(0.10, 0.30),
        np.random.uniform(0.72, 0.92),
        np.random.uniform(100, 2000),
        np.random.uniform(0.10, 0.28),
    ])
    
    # Hard fail flags
    sample.extend([
        np.random.choice([0, 1], p=[0.4, 0.6]),
        np.random.choice([0, 1], p=[0.6, 0.4]),
        np.random.choice([0, 1], p=[0.4, 0.6]),
        np.random.choice([0, 1], p=[0.5, 0.5]),
        np.random.choice([0, 1], p=[0.3, 0.7]),
        np.random.choice([0, 1], p=[0.3, 0.7]),
        1,  # usually fails entropy
    ])


def _add_speed_bot_features(sample):
    """Very fast automation bot"""
    # Mouse - minimal fast movement
    sample.append(np.random.randint(5, 30))
    sample.append(np.random.uniform(50, 300))
    sample.append(np.random.uniform(500, 1200))  # very fast
    sample.append(np.random.uniform(600, 1500))
    sample.append(np.random.uniform(0.80, 0.98))  # very straight
    sample.append(np.random.randint(0, 4))
    sample.append(0)
    sample.append(np.random.uniform(0, 0.005))
    sample.append(np.random.randint(1, 3))
    sample.append(np.random.uniform(0, 20))
    sample.append(np.random.uniform(0, 40))
    
    # Keyboard - very fast
    if np.random.random() < 0.5:
        sample.extend([0, 0, 0, 0, 0, 0, 0, 0])
    else:
        sample.extend([
            np.random.randint(10, 60),
            np.random.uniform(20, 50),  # very short dwell
            np.random.uniform(20, 50),  # very short flight
            np.random.uniform(600, 1200),  # very fast typing
            0,
            np.random.uniform(0.96, 1.0),
            np.random.uniform(0, 5),
            np.random.uniform(0, 5),
        ])
    
    # Scroll - fast or none
    sample.extend([
        np.random.randint(0, 3),
        np.random.uniform(0, 200),
        np.random.uniform(300, 800),
        np.random.uniform(0.90, 1.0),
        0,
    ])
    
    # Touch
    sample.extend([0, 0])
    
    # Focus
    sample.extend([np.random.randint(0, 1), np.random.randint(100, 2000), 0, 0])
    
    # Timing - VERY FAST
    sample.extend([
        np.random.randint(50, 300),
        np.random.randint(0, 80),  # instant interaction
        np.random.randint(200, 2000),  # very short session
        0, 0,
        np.random.uniform(0, 20),
    ])
    
    # Entropy - very low
    sample.extend([
        np.random.uniform(0.02, 0.18),
        np.random.uniform(0.02, 0.15),
        np.random.uniform(0.02, 0.15),
        np.random.uniform(0.88, 0.99),
        np.random.uniform(0, 300),
        np.random.uniform(0.02, 0.15),
    ])
    
    # Hard fail flags - ALL FAIL
    sample.extend([1, 1, 1, 1, 1, 1, 1])


def generate_training_data(n_samples: int = 10000, bot_ratio: float = 0.5) -> tuple:
    """
    Generate synthetic training data with adversarial bot samples
    Increased bot ratio to help model learn adversarial patterns
    """
    n_bots = int(n_samples * bot_ratio)
    n_humans = n_samples - n_bots
    
    print(f"  Generating {n_humans} human samples...")
    human_samples = np.array([generate_human_sample() for _ in range(n_humans)])
    
    print(f"  Generating {n_bots} bot samples (including adversarial stealth bots)...")
    bot_samples = np.array([generate_bot_sample() for _ in range(n_bots)])
    
    # Combine and create labels
    X = np.vstack([human_samples, bot_samples])
    y = np.hstack([np.ones(n_humans), np.zeros(n_bots)])  # 1 = human, 0 = bot
    
    # Shuffle
    indices = np.random.permutation(len(X))
    X = X[indices]
    y = y[indices]
    
    return X, y


def train_model(X: np.ndarray, y: np.ndarray) -> XGBClassifier:
    """Train XGBoost classifier with optimized parameters for bot detection"""
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Create model with stricter parameters
    model = XGBClassifier(
        n_estimators=200,       # More trees for complex patterns
        max_depth=8,            # Deeper trees to capture adversarial patterns
        learning_rate=0.08,     # Slightly lower for better generalization
        subsample=0.85,
        colsample_bytree=0.85,
        min_child_weight=3,     # Prevent overfitting
        gamma=0.1,              # Minimum loss reduction for split
        reg_alpha=0.1,          # L1 regularization
        reg_lambda=1.0,         # L2 regularization
        random_state=42,
        eval_metric='logloss',
        use_label_encoder=False,
    )
    
    # Train
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=True,
    )
    
    # Evaluate
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    print("\n" + "=" * 50)
    print("Model Evaluation")
    print("=" * 50)
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Bot', 'Human']))
    
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    print(f"\nROC AUC Score: {roc_auc_score(y_test, y_proba):.4f}")
    
    # Cross-validation
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
    print(f"\nCross-validation scores: {cv_scores}")
    print(f"Mean CV accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
    
    return model


def save_model(model: XGBClassifier, output_path: str) -> None:
    """Save trained model"""
    # Create directory if needed
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Save model
    joblib.dump(model, output_path)
    print(f"\nModel saved to {output_path}")
    
    # Save feature importance (convert numpy float32 to Python float)
    importance = {k: float(v) for k, v in zip(FEATURE_NAMES, model.feature_importances_)}
    importance_sorted = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
    
    importance_path = str(Path(output_path).parent / "feature_importance.json")
    with open(importance_path, 'w') as f:
        json.dump(importance_sorted, f, indent=2)
    print(f"Feature importance saved to {importance_path}")
    
    # Print top features
    print("\nTop 10 Important Features:")
    for i, (name, imp) in enumerate(list(importance_sorted.items())[:10]):
        print(f"  {i+1}. {name}: {imp:.4f}")


def main():
    """Main training function"""
    print("=" * 60)
    print("PassiveGuard Bot Detection Model Training")
    print("With ADVERSARIAL Bot Samples (Selenium Stealth Detection)")
    print("=" * 60)
    
    # Generate data - more samples for better adversarial detection
    print("\nGenerating synthetic training data...")
    X, y = generate_training_data(n_samples=30000, bot_ratio=0.55)  # Slightly more bots
    print(f"Generated {len(X)} samples ({int(sum(y))} humans, {int(len(y) - sum(y))} bots)")
    
    # Train model
    print("\nTraining XGBoost classifier...")
    model = train_model(X, y)
    
    # Save model
    output_path = "models/bot_detector.joblib"
    save_model(model, output_path)
    
    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)
    print("\nKey improvements:")
    print("  - Adversarial 'Selenium stealth' bot samples added")
    print("  - Entropy-based features for detecting programmatic patterns")
    print("  - Hard threshold violation flags")
    print("  - Stricter human behavioral baselines")
    print("\nExpected Selenium detection rate: <20% human score")


if __name__ == "__main__":
    main()
