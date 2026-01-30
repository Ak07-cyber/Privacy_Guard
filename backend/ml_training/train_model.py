"""
ML Model Training Script for Bot Detection
Generates synthetic data and trains XGBoost classifier
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


# Feature names (must match FeatureExtractor)
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


def generate_human_sample() -> np.ndarray:
    """Generate synthetic human-like behavior data"""
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
    sample.append(np.random.randint(50, 500))  # movement_count
    sample.append(np.random.uniform(500, 5000))  # total_distance
    sample.append(np.random.uniform(100, 800))  # avg_velocity
    sample.append(np.random.uniform(500, 2000))  # max_velocity
    sample.append(np.random.uniform(0.1, 0.6))  # straight_line_ratio (not perfect)
    sample.append(np.random.randint(10, 100))  # direction_changes
    sample.append(np.random.randint(5, 50))  # pause_count
    sample.append(np.random.uniform(0.02, 0.2))  # jitter_score
    sample.append(np.random.randint(1, 20))  # click_count
    sample.append(np.random.uniform(50, 300))  # velocity_std
    sample.append(np.random.uniform(100, 1000))  # acceleration_std
    
    # Keyboard Features (humans have variable typing)
    sample.append(np.random.randint(0, 200))  # key_press_count
    sample.append(np.random.uniform(80, 200))  # avg_dwell_time
    sample.append(np.random.uniform(100, 300))  # avg_flight_time
    sample.append(np.random.uniform(150, 400))  # typing_speed
    sample.append(np.random.uniform(0.02, 0.15))  # error_rate
    sample.append(np.random.uniform(0.3, 0.85))  # rhythm_consistency (not perfect)
    sample.append(np.random.uniform(20, 80))  # dwell_time_std
    sample.append(np.random.uniform(30, 100))  # flight_time_std
    
    # Scroll Features
    sample.append(np.random.randint(5, 50))  # scroll_event_count
    sample.append(np.random.uniform(200, 3000))  # scroll_total_distance
    sample.append(np.random.uniform(100, 800))  # scroll_avg_velocity
    sample.append(np.random.uniform(0.3, 0.8))  # scroll_smoothness
    sample.append(np.random.randint(1, 10))  # scroll_direction_changes
    
    # Touch Features
    sample.append(np.random.randint(0, 20))  # touch_gesture_count
    sample.append(np.random.randint(0, 5))  # multi_touch_count
    
    # Focus Features
    sample.append(np.random.randint(1, 10))  # focus_event_count
    sample.append(np.random.randint(5000, 60000))  # focus_total_time
    sample.append(np.random.randint(0, 5))  # blur_count
    sample.append(np.random.randint(0, 3))  # visibility_changes
    
    # Timing Features
    sample.append(np.random.randint(500, 5000))  # page_load_time
    sample.append(np.random.randint(500, 5000))  # time_to_first_interaction
    sample.append(np.random.randint(5000, 120000))  # total_interaction_time
    sample.append(np.random.randint(0, 10))  # idle_period_count
    sample.append(np.random.uniform(1000, 10000))  # avg_idle_duration
    sample.append(np.random.uniform(100, 2000))  # interaction_gap_std
    
    return np.array(sample)


def generate_bot_sample() -> np.ndarray:
    """Generate synthetic bot-like behavior data"""
    sample = []
    
    # Environmental Features (bots often have automation flags)
    sample.append(np.random.choice([0, 1], p=[0.3, 0.7]))  # webdriver often true
    sample.append(np.random.choice([0, 1, 2, 3], p=[0.2, 0.4, 0.3, 0.1]))  # automation flags
    sample.append(np.random.choice([0, 1], p=[0.6, 0.4]))  # less likely to have plugins
    sample.append(np.random.randint(0, 3))  # fewer plugins
    sample.append(np.random.uniform(1.3, 1.9))  # screen_ratio
    sample.append(np.random.choice([24, 32]))  # color_depth
    sample.append(1)  # often default pixel ratio
    sample.append(0)  # usually no touch
    sample.append(np.random.choice([1, 2, 4]))  # often limited cores
    sample.append(np.random.choice([0, 2, 4]))  # often limited or no memory info
    sample.append(np.random.choice([0, 1], p=[0.3, 0.7]))  # may lack storage
    sample.append(np.random.choice([0, 1], p=[0.3, 0.7]))  # may lack storage
    sample.append(np.random.choice([0, 1], p=[0.2, 0.8]))  # indexed_db
    sample.append(np.random.choice([0, 8], p=[0.4, 0.6]))  # may lack fingerprint
    sample.append(np.random.choice([0, 8], p=[0.4, 0.6]))  # may lack fingerprint
    sample.append(np.random.choice([0, 8], p=[0.5, 0.5]))  # may lack fingerprint
    sample.append(0)  # often UTC timezone
    sample.append(1)  # usually single language
    
    # Mouse Movement Features (bots have mechanical movements)
    bot_type = np.random.choice(['no_mouse', 'perfect_mouse', 'scripted_mouse'])
    
    if bot_type == 'no_mouse':
        sample.append(0)  # no movements
        sample.append(0)  # no distance
        sample.append(0)  # no velocity
        sample.append(0)  # no max velocity
        sample.append(0)  # no ratio
        sample.append(0)  # no changes
        sample.append(0)  # no pauses
        sample.append(0)  # no jitter
        sample.append(np.random.randint(0, 2))  # maybe a click
        sample.append(0)  # no std
        sample.append(0)  # no std
    elif bot_type == 'perfect_mouse':
        sample.append(np.random.randint(10, 100))  # some movements
        sample.append(np.random.uniform(100, 1000))  # distance
        sample.append(np.random.uniform(200, 400))  # avg velocity (consistent)
        sample.append(np.random.uniform(300, 500))  # max velocity (close to avg)
        sample.append(np.random.uniform(0.9, 1.0))  # almost perfect straight line
        sample.append(np.random.randint(0, 5))  # few direction changes
        sample.append(0)  # no pauses
        sample.append(np.random.uniform(0, 0.01))  # no jitter
        sample.append(np.random.randint(1, 5))  # clicks
        sample.append(np.random.uniform(0, 20))  # very low std
        sample.append(np.random.uniform(0, 50))  # very low std
    else:  # scripted_mouse
        sample.append(np.random.randint(20, 80))  # movements
        sample.append(np.random.uniform(200, 800))  # distance
        sample.append(np.random.uniform(300, 600))  # velocity
        sample.append(np.random.uniform(400, 700))  # max velocity
        sample.append(np.random.uniform(0.7, 0.95))  # fairly straight
        sample.append(np.random.randint(2, 10))  # some changes
        sample.append(np.random.randint(0, 3))  # few pauses
        sample.append(np.random.uniform(0.005, 0.02))  # minimal jitter
        sample.append(np.random.randint(1, 5))  # clicks
        sample.append(np.random.uniform(10, 50))  # low std
        sample.append(np.random.uniform(20, 100))  # low std
    
    # Keyboard Features (bots have perfect or no typing)
    if np.random.random() < 0.5:
        # No typing
        sample.append(0)
        sample.append(0)
        sample.append(0)
        sample.append(0)
        sample.append(0)
        sample.append(0)
        sample.append(0)
        sample.append(0)
    else:
        # Perfect typing
        sample.append(np.random.randint(10, 100))  # key presses
        sample.append(np.random.uniform(50, 100))  # very consistent dwell
        sample.append(np.random.uniform(50, 100))  # very consistent flight
        sample.append(np.random.uniform(300, 600))  # fast typing
        sample.append(0)  # no errors
        sample.append(np.random.uniform(0.95, 1.0))  # perfect rhythm
        sample.append(np.random.uniform(0, 10))  # very low std
        sample.append(np.random.uniform(0, 10))  # very low std
    
    # Scroll Features
    sample.append(np.random.randint(0, 10))  # scroll events
    sample.append(np.random.uniform(0, 500))  # scroll distance
    sample.append(np.random.uniform(0, 200))  # scroll velocity
    sample.append(np.random.uniform(0.8, 1.0))  # very smooth (mechanical)
    sample.append(np.random.randint(0, 2))  # few direction changes
    
    # Touch Features (bots usually don't use touch)
    sample.append(0)
    sample.append(0)
    
    # Focus Features
    sample.append(np.random.randint(0, 2))  # minimal focus events
    sample.append(np.random.randint(100, 5000))  # short focus time
    sample.append(0)  # no blurs
    sample.append(0)  # no visibility changes
    
    # Timing Features (bots are often very fast)
    sample.append(np.random.randint(100, 1000))  # fast page load
    sample.append(np.random.choice([-1, np.random.randint(0, 100)]))  # instant or no interaction
    sample.append(np.random.randint(100, 5000))  # short total time
    sample.append(0)  # no idle periods
    sample.append(0)  # no idle duration
    sample.append(np.random.uniform(0, 50))  # very consistent gaps
    
    return np.array(sample)


def generate_training_data(n_samples: int = 10000, bot_ratio: float = 0.5) -> tuple:
    """Generate synthetic training data"""
    n_bots = int(n_samples * bot_ratio)
    n_humans = n_samples - n_bots
    
    # Generate samples
    human_samples = np.array([generate_human_sample() for _ in range(n_humans)])
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
    """Train XGBoost classifier"""
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Create model
    model = XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric='logloss',
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
    print("=" * 50)
    print("PassiveGuard Bot Detection Model Training")
    print("=" * 50)
    
    # Generate data
    print("\nGenerating synthetic training data...")
    X, y = generate_training_data(n_samples=20000, bot_ratio=0.5)
    print(f"Generated {len(X)} samples ({sum(y)} humans, {len(y) - sum(y)} bots)")
    
    # Train model
    print("\nTraining XGBoost classifier...")
    model = train_model(X, y)
    
    # Save model
    output_path = "models/bot_detector.joblib"
    save_model(model, output_path)
    
    print("\n" + "=" * 50)
    print("Training Complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
