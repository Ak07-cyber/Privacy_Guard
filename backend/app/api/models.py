"""
Pydantic models for API request/response
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============================================
# Environmental Data Models
# ============================================

class PluginInfo(BaseModel):
    name: str
    description: str
    filename: str


class BrowserInfo(BaseModel):
    userAgent: str
    language: str
    languages: List[str]
    platform: str
    vendor: str
    cookiesEnabled: bool
    doNotTrack: Optional[str] = None
    plugins: List[PluginInfo] = []
    mimeTypes: List[str] = []


class ScreenInfo(BaseModel):
    width: int
    height: int
    availWidth: int
    availHeight: int
    colorDepth: int
    pixelDepth: int
    devicePixelRatio: float
    orientation: str


class HardwareInfo(BaseModel):
    hardwareConcurrency: int
    deviceMemory: Optional[float] = None
    maxTouchPoints: int
    hasTouch: bool
    hasPointer: bool


class WebGLInfo(BaseModel):
    vendor: str
    renderer: str
    version: str
    shadingLanguageVersion: str
    extensions: List[str] = []
    hash: str


class TimezoneInfo(BaseModel):
    offset: int
    timezone: str
    isDST: bool


class FeatureDetection(BaseModel):
    webdriver: bool
    automationFlags: List[str] = []
    hasNotificationPermission: bool
    hasGeolocationPermission: bool
    localStorage: bool
    sessionStorage: bool
    indexedDB: bool
    webSocket: bool
    webWorker: bool
    serviceWorker: bool


class EnvironmentalData(BaseModel):
    browser: BrowserInfo
    screen: ScreenInfo
    hardware: HardwareInfo
    webgl: WebGLInfo
    canvasHash: str
    audioHash: str
    timezone: TimezoneInfo
    features: FeatureDetection
    timestamp: int


# ============================================
# Behavioral Data Models
# ============================================

class MouseMovement(BaseModel):
    x: float
    y: float
    timestamp: int
    velocity: float
    acceleration: float
    angle: float


class ClickEvent(BaseModel):
    x: float
    y: float
    timestamp: int
    button: int
    target: str


class MovementStats(BaseModel):
    totalDistance: float
    averageVelocity: float
    maxVelocity: float
    straightLineRatio: float
    directionChanges: int
    pauseCount: int
    jitterScore: float


class MouseData(BaseModel):
    movements: List[MouseMovement] = []
    clicks: List[ClickEvent] = []
    movementStats: MovementStats


class KeyPressEvent(BaseModel):
    key: str
    keyDownTime: int
    keyUpTime: int
    dwellTime: int
    flightTime: int


class TypingStats(BaseModel):
    averageDwellTime: float
    averageFlightTime: float
    typingSpeed: float
    errorRate: float
    rhythmConsistency: float


class KeyboardData(BaseModel):
    keyPresses: List[KeyPressEvent] = []
    typingStats: TypingStats


class ScrollEvent(BaseModel):
    deltaX: float
    deltaY: float
    timestamp: int
    velocity: float


class ScrollStats(BaseModel):
    totalScroll: float
    averageVelocity: float
    smoothness: float
    directionChanges: int


class ScrollData(BaseModel):
    events: List[ScrollEvent] = []
    stats: ScrollStats


class GestureEvent(BaseModel):
    type: str
    timestamp: int
    duration: int
    touches: int


class TouchData(BaseModel):
    gestures: List[GestureEvent] = []
    multiTouchEvents: int
    averagePressure: float


class FocusEvent(BaseModel):
    type: str
    timestamp: int
    duration: Optional[int] = None


class FocusData(BaseModel):
    focusEvents: List[FocusEvent] = []
    totalFocusTime: int
    blurCount: int
    visibilityChanges: int


class TimingData(BaseModel):
    pageLoadTime: int
    timeToFirstInteraction: int
    totalInteractionTime: int
    idlePeriods: List[int] = []
    interactionGaps: List[int] = []


class BehavioralData(BaseModel):
    mouse: MouseData
    keyboard: KeyboardData
    scroll: ScrollData
    touch: TouchData
    focus: FocusData
    timing: TimingData


# ============================================
# Challenge Models
# ============================================

class ChallengeResponse(BaseModel):
    challengeId: str
    response: Any
    completionTime: int
    accuracy: float


class Challenge(BaseModel):
    id: str
    type: str
    data: Dict[str, Any]
    timeout: int


# ============================================
# Request/Response Models
# ============================================

class VerificationRequest(BaseModel):
    siteKey: str
    environmental: EnvironmentalData
    behavioral: BehavioralData
    challengeResponse: Optional[ChallengeResponse] = None
    requestId: str
    timestamp: int


class AnalysisDetails(BaseModel):
    environmentalScore: float
    behavioralScore: float
    anomalies: List[str]
    featureImportance: Dict[str, float]


class VerificationResponse(BaseModel):
    isHuman: bool
    confidence: float
    riskScore: float
    token: str
    expiresAt: int
    challengeRequired: bool
    challenge: Optional[Challenge] = None
    analysis: Optional[AnalysisDetails] = None


class TokenValidationRequest(BaseModel):
    token: str
    siteKey: str


class TokenValidationResponse(BaseModel):
    valid: bool
    isHuman: Optional[bool] = None
    riskScore: Optional[float] = None
    expiresAt: Optional[int] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    model_loaded: bool
