"""
Bot Detection ML Model
Uses XGBoost for classification with fallback rule-based detection
"""

import numpy as np
from typing import Tuple, Dict, List, Optional, Any
import joblib
import os
from pathlib import Path

from app.core.config import settings
from app.features.extractor import FeatureExtractor


class BotDetector:
    """ML-based bot detection with rule-based fallback"""
    
    def __init__(self):
        self.model = None
        self.feature_extractor = FeatureExtractor()
        self.model_loaded = False
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the trained model from disk"""
        model_path = Path(settings.MODEL_PATH)
        
        if model_path.exists():
            try:
                self.model = joblib.load(model_path)
                self.model_loaded = True
                print(f"Model loaded from {model_path}")
            except Exception as e:
                print(f"Failed to load model: {e}")
                self.model_loaded = False
        else:
            print(f"Model not found at {model_path}, using rule-based detection")
            self.model_loaded = False
    
    def predict(self, features: np.ndarray, anomalies: List[str]) -> Tuple[bool, float, float]:
        """
        Predict if user is human or bot
        
        Returns:
            Tuple of (is_human, confidence, risk_score)
        """
        # If model is loaded, use ML prediction
        if self.model_loaded and self.model is not None:
            return self._ml_predict(features, anomalies)
        else:
            # Fallback to rule-based detection
            return self._rule_based_predict(features, anomalies)
    
    def _ml_predict(self, features: np.ndarray, anomalies: List[str]) -> Tuple[bool, float, float]:
        """ML-based prediction"""
        try:
            # Reshape for single prediction
            X = features.reshape(1, -1)
            
            # Get probability
            proba = self.model.predict_proba(X)[0]
            
            # Index 1 is probability of being human
            human_prob = proba[1] if len(proba) > 1 else proba[0]
            
            # Adjust based on anomalies
            anomaly_penalty = len(anomalies) * 0.1
            adjusted_prob = max(0, human_prob - anomaly_penalty)
            
            # Calculate risk score (inverse of human probability)
            risk_score = 1 - adjusted_prob
            
            # Determine if human based on threshold
            is_human = adjusted_prob >= settings.MODEL_THRESHOLD
            
            return is_human, adjusted_prob, risk_score
            
        except Exception as e:
            print(f"ML prediction error: {e}")
            return self._rule_based_predict(features, anomalies)
    
    def _rule_based_predict(self, features: np.ndarray, anomalies: List[str]) -> Tuple[bool, float, float]:
        """Rule-based bot detection fallback"""
        score = 1.0  # Start with human assumption
        
        feature_names = self.feature_extractor.get_feature_names()
        feature_dict = dict(zip(feature_names, features))
        
        # Critical bot indicators
        if feature_dict.get('env_webdriver', 0) > 0:
            score -= 0.5
        
        if feature_dict.get('env_automation_flag_count', 0) > 0:
            score -= 0.3
        
        # No mouse movement is highly suspicious
        if feature_dict.get('mouse_movement_count', 0) == 0:
            score -= 0.3
        
        # Perfect straight line mouse movement
        if feature_dict.get('mouse_straight_line_ratio', 0) > 0.95:
            score -= 0.2
        
        # No keyboard interaction with form
        if feature_dict.get('key_press_count', 0) == 0:
            # Not always suspicious, depends on context
            score -= 0.05
        
        # Perfect typing rhythm (bot-like)
        if feature_dict.get('key_rhythm_consistency', 0) > 0.99:
            score -= 0.2
        
        # Instant interaction (too fast)
        time_to_first = feature_dict.get('timing_first_interaction', 0)
        if time_to_first >= 0 and time_to_first < 100:
            score -= 0.3
        
        # No browser storage support
        if (feature_dict.get('env_has_local_storage', 1) == 0 and 
            feature_dict.get('env_has_session_storage', 1) == 0):
            score -= 0.1
        
        # Missing fingerprints
        if (feature_dict.get('env_canvas_hash_length', 0) == 0 and 
            feature_dict.get('env_webgl_hash_length', 0) == 0):
            score -= 0.2
        
        # Anomaly penalties
        for anomaly in anomalies:
            if 'webdriver' in anomaly:
                score -= 0.2
            elif 'automation' in anomaly:
                score -= 0.15
            elif 'no_interaction' in anomaly:
                score -= 0.1
            elif 'instant' in anomaly:
                score -= 0.15
            elif 'perfectly_straight' in anomaly:
                score -= 0.15
            elif 'unnaturally_smooth' in anomaly:
                score -= 0.1
            else:
                score -= 0.05
        
        # Positive signals
        if feature_dict.get('mouse_movement_count', 0) > 50:
            score += 0.1
        
        if feature_dict.get('mouse_direction_changes', 0) > 10:
            score += 0.1
        
        if feature_dict.get('mouse_jitter_score', 0) > 0.01:
            score += 0.05
        
        if feature_dict.get('timing_total_interaction', 0) > 5000:
            score += 0.05
        
        # Clamp score
        score = max(0, min(1, score))
        risk_score = 1 - score
        is_human = score >= settings.MODEL_THRESHOLD
        
        return is_human, score, risk_score
    
    def get_feature_importance(self, features: np.ndarray) -> Dict[str, float]:
        """Get feature importance for analysis"""
        feature_names = self.feature_extractor.get_feature_names()
        
        if self.model_loaded and hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
            return dict(zip(feature_names, importances))
        else:
            # Return normalized feature values as pseudo-importance
            normalized = features / (np.max(np.abs(features)) + 1e-10)
            return dict(zip(feature_names, normalized))
    
    def is_model_loaded(self) -> bool:
        """Check if ML model is loaded"""
        return self.model_loaded


# Global instance
bot_detector = BotDetector()
