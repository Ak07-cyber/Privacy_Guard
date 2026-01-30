"""
API Routes for PassiveGuard
"""

from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timedelta
from typing import Dict, Any

from app.api.models import (
    VerificationRequest,
    VerificationResponse,
    TokenValidationRequest,
    TokenValidationResponse,
    HealthResponse,
    Challenge,
    AnalysisDetails,
)
from app.core import (
    settings,
    create_verification_token,
    verify_token,
    verify_site_key,
    generate_challenge_id,
)
from app.features import feature_extractor
from app.ml import bot_detector

router = APIRouter()


@router.post("/verify", response_model=VerificationResponse)
async def verify_user(request: VerificationRequest) -> VerificationResponse:
    """
    Verify if the user is human or bot
    
    Analyzes environmental and behavioral data to detect bots.
    Returns verification result with token for protected API access.
    """
    # Validate site key
    if not verify_site_key(request.siteKey):
        raise HTTPException(status_code=400, detail="Invalid site key")
    
    # Extract features from request
    features, anomalies = feature_extractor.extract_features(request)
    
    # Get prediction
    is_human, confidence, risk_score = bot_detector.predict(features, anomalies)
    
    # Check if challenge is needed
    challenge_required = False
    challenge = None
    
    if not is_human and confidence < settings.CHALLENGE_THRESHOLD:
        # Very uncertain - require challenge
        challenge_required = True
        challenge = Challenge(
            id=generate_challenge_id(),
            type="mouse-follow",
            data={
                "instructions": "Please follow the moving target with your mouse",
                "difficulty": "easy",
            },
            timeout=settings.CHALLENGE_TIMEOUT,
        )
    
    # If challenge response provided, verify it
    if request.challengeResponse:
        # Validate challenge response
        challenge_valid = _verify_challenge_response(request.challengeResponse)
        if challenge_valid:
            # Boost confidence
            confidence = min(1.0, confidence + 0.3)
            is_human = confidence >= settings.MODEL_THRESHOLD
            challenge_required = False
            challenge = None
    
    # Generate token
    token_data = {
        "request_id": request.requestId,
        "site_key": request.siteKey,
        "is_human": is_human,
        "confidence": confidence,
        "risk_score": risk_score,
    }
    token = create_verification_token(token_data)
    expires_at = int((datetime.utcnow() + timedelta(minutes=settings.TOKEN_EXPIRE_MINUTES)).timestamp() * 1000)
    
    # Prepare analysis details (for debug mode)
    analysis = None
    if settings.DEBUG:
        feature_importance = bot_detector.get_feature_importance(features)
        
        # Calculate component scores
        env_features_count = 18  # Number of environmental features
        env_score = float(sum(features[:env_features_count])) / env_features_count
        behav_score = float(sum(features[env_features_count:])) / (len(features) - env_features_count)
        
        analysis = AnalysisDetails(
            environmentalScore=min(1.0, max(0.0, 0.5 + env_score * 0.1)),
            behavioralScore=min(1.0, max(0.0, 0.5 + behav_score * 0.001)),
            anomalies=anomalies,
            featureImportance=feature_importance,
        )
    
    return VerificationResponse(
        isHuman=is_human,
        confidence=confidence,
        riskScore=risk_score,
        token=token,
        expiresAt=expires_at,
        challengeRequired=challenge_required,
        challenge=challenge,
        analysis=analysis,
    )


@router.post("/validate", response_model=TokenValidationResponse)
async def validate_token(request: TokenValidationRequest) -> TokenValidationResponse:
    """
    Validate a verification token
    
    Used by backend services to verify tokens from frontend.
    """
    # Verify site key
    if not verify_site_key(request.siteKey):
        raise HTTPException(status_code=400, detail="Invalid site key")
    
    # Verify token
    payload = verify_token(request.token)
    
    if payload is None:
        return TokenValidationResponse(valid=False)
    
    # Check site key matches
    if payload.get("site_key") != request.siteKey:
        return TokenValidationResponse(valid=False)
    
    # Get expiration
    exp = payload.get("exp")
    if exp:
        expires_at = int(exp * 1000)  # Convert to milliseconds
    else:
        expires_at = None
    
    return TokenValidationResponse(
        valid=True,
        isHuman=payload.get("is_human"),
        riskScore=payload.get("risk_score"),
        expiresAt=expires_at,
    )


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version=settings.VERSION,
        model_loaded=bot_detector.is_model_loaded(),
    )


@router.get("/features")
async def get_features() -> Dict[str, Any]:
    """Get list of features used by the model (for documentation)"""
    return {
        "features": feature_extractor.get_feature_names(),
        "count": len(feature_extractor.get_feature_names()),
    }


def _verify_challenge_response(response) -> bool:
    """Verify challenge response"""
    # Basic validation
    if not response.challengeId:
        return False
    
    # Check completion time (not too fast)
    if response.completionTime < 500:
        return False
    
    # Check accuracy
    if response.accuracy < 0.5:
        return False
    
    return True
