/**
 * PassiveGuard SDK Type Definitions
 * Comprehensive types for bot detection system
 */

// ============================================
// Configuration Types
// ============================================

export interface PassiveGuardConfig {
  /** API endpoint for verification */
  apiEndpoint: string;
  /** Site key for identification */
  siteKey: string;
  /** Enable debug mode */
  debug?: boolean;
  /** Collection timeout in ms */
  collectionTimeout?: number;
  /** Enable behavioral tracking */
  enableBehavioral?: boolean;
  /** Enable environmental collection */
  enableEnvironmental?: boolean;
  /** Callback when challenge is needed */
  onChallenge?: (challenge: Challenge) => Promise<ChallengeResponse>;
  /** Callback on verification complete */
  onVerify?: (result: VerificationResult) => void;
  /** Privacy mode - limits data collection */
  privacyMode?: boolean;
}

// ============================================
// Environmental Data Types
// ============================================

export interface EnvironmentalData {
  /** Browser information */
  browser: BrowserInfo;
  /** Screen and display info */
  screen: ScreenInfo;
  /** Hardware capabilities */
  hardware: HardwareInfo;
  /** WebGL information */
  webgl: WebGLInfo;
  /** Canvas fingerprint (hashed) */
  canvasHash: string;
  /** Audio fingerprint (hashed) */
  audioHash: string;
  /** Timezone information */
  timezone: TimezoneInfo;
  /** Feature detection results */
  features: FeatureDetection;
  /** Collection timestamp */
  timestamp: number;
}

export interface BrowserInfo {
  userAgent: string;
  language: string;
  languages: string[];
  platform: string;
  vendor: string;
  cookiesEnabled: boolean;
  doNotTrack: string | null;
  plugins: PluginInfo[];
  mimeTypes: string[];
}

export interface PluginInfo {
  name: string;
  description: string;
  filename: string;
}

export interface ScreenInfo {
  width: number;
  height: number;
  availWidth: number;
  availHeight: number;
  colorDepth: number;
  pixelDepth: number;
  devicePixelRatio: number;
  orientation: string;
}

export interface HardwareInfo {
  hardwareConcurrency: number;
  deviceMemory: number | null;
  maxTouchPoints: number;
  hasTouch: boolean;
  hasPointer: boolean;
}

export interface WebGLInfo {
  vendor: string;
  renderer: string;
  version: string;
  shadingLanguageVersion: string;
  extensions: string[];
  hash: string;
}

export interface TimezoneInfo {
  offset: number;
  timezone: string;
  isDST: boolean;
}

export interface FeatureDetection {
  webdriver: boolean;
  automationFlags: string[];
  hasNotificationPermission: boolean;
  hasGeolocationPermission: boolean;
  localStorage: boolean;
  sessionStorage: boolean;
  indexedDB: boolean;
  webSocket: boolean;
  webWorker: boolean;
  serviceWorker: boolean;
}

// ============================================
// Behavioral Data Types
// ============================================

export interface BehavioralData {
  /** Mouse movement data */
  mouse: MouseData;
  /** Keyboard interaction data */
  keyboard: KeyboardData;
  /** Scroll behavior data */
  scroll: ScrollData;
  /** Touch/gesture data */
  touch: TouchData;
  /** Focus and visibility events */
  focus: FocusData;
  /** Interaction timing data */
  timing: TimingData;
}

export interface MouseData {
  movements: MouseMovement[];
  clicks: ClickEvent[];
  movementStats: MovementStats;
}

export interface MouseMovement {
  x: number;
  y: number;
  timestamp: number;
  velocity: number;
  acceleration: number;
  angle: number;
}

export interface ClickEvent {
  x: number;
  y: number;
  timestamp: number;
  button: number;
  target: string;
}

export interface MovementStats {
  totalDistance: number;
  averageVelocity: number;
  maxVelocity: number;
  straightLineRatio: number;
  directionChanges: number;
  pauseCount: number;
  jitterScore: number;
}

export interface KeyboardData {
  keyPresses: KeyPressEvent[];
  typingStats: TypingStats;
}

export interface KeyPressEvent {
  key: string; // Obfuscated for privacy
  keyDownTime: number;
  keyUpTime: number;
  dwellTime: number;
  flightTime: number;
}

export interface TypingStats {
  averageDwellTime: number;
  averageFlightTime: number;
  typingSpeed: number;
  errorRate: number;
  rhythmConsistency: number;
}

export interface ScrollData {
  events: ScrollEvent[];
  stats: ScrollStats;
}

export interface ScrollEvent {
  deltaX: number;
  deltaY: number;
  timestamp: number;
  velocity: number;
}

export interface ScrollStats {
  totalScroll: number;
  averageVelocity: number;
  smoothness: number;
  directionChanges: number;
}

export interface TouchData {
  gestures: GestureEvent[];
  multiTouchEvents: number;
  averagePressure: number;
}

export interface GestureEvent {
  type: 'tap' | 'swipe' | 'pinch' | 'rotate';
  timestamp: number;
  duration: number;
  touches: number;
}

export interface FocusData {
  focusEvents: FocusEvent[];
  totalFocusTime: number;
  blurCount: number;
  visibilityChanges: number;
}

export interface FocusEvent {
  type: 'focus' | 'blur' | 'visibilitychange';
  timestamp: number;
  duration?: number;
}

export interface TimingData {
  pageLoadTime: number;
  timeToFirstInteraction: number;
  totalInteractionTime: number;
  idlePeriods: number[];
  interactionGaps: number[];
}

// ============================================
// Verification Types
// ============================================

export interface VerificationRequest {
  siteKey: string;
  environmental: EnvironmentalData;
  behavioral: BehavioralData;
  challengeResponse?: ChallengeResponse;
  requestId: string;
  timestamp: number;
}

export interface VerificationResult {
  /** Is the user human */
  isHuman: boolean;
  /** Confidence score (0-1) */
  confidence: number;
  /** Risk score (0-1, higher = more risk) */
  riskScore: number;
  /** Verification token for backend validation */
  token: string;
  /** Token expiration timestamp */
  expiresAt: number;
  /** Challenge needed flag */
  challengeRequired: boolean;
  /** Challenge details if required */
  challenge?: Challenge;
  /** Detailed analysis (debug mode only) */
  analysis?: AnalysisDetails;
}

export interface AnalysisDetails {
  environmentalScore: number;
  behavioralScore: number;
  anomalies: string[];
  featureImportance: Record<string, number>;
}

// ============================================
// Challenge Types
// ============================================

export interface Challenge {
  id: string;
  type: ChallengeType;
  data: ChallengeData;
  timeout: number;
}

export type ChallengeType = 
  | 'mouse-follow'
  | 'click-target'
  | 'drag-drop'
  | 'typing-pattern'
  | 'scroll-pattern';

export interface ChallengeData {
  instructions: string;
  targetPoints?: Point[];
  expectedPattern?: string;
  difficulty: 'easy' | 'medium' | 'hard';
}

export interface Point {
  x: number;
  y: number;
}

export interface ChallengeResponse {
  challengeId: string;
  response: any;
  completionTime: number;
  accuracy: number;
}

// ============================================
// Event Types
// ============================================

export type PassiveGuardEvent = 
  | 'init'
  | 'collecting'
  | 'collected'
  | 'verifying'
  | 'verified'
  | 'challenge'
  | 'error';

export interface PassiveGuardEventData {
  event: PassiveGuardEvent;
  timestamp: number;
  data?: any;
}

export type EventCallback = (data: PassiveGuardEventData) => void;

// ============================================
// Error Types
// ============================================

export class PassiveGuardError extends Error {
  code: string;
  details?: any;

  constructor(message: string, code: string, details?: any) {
    super(message);
    this.name = 'PassiveGuardError';
    this.code = code;
    this.details = details;
  }
}

export type ErrorCode = 
  | 'INIT_FAILED'
  | 'COLLECTION_TIMEOUT'
  | 'NETWORK_ERROR'
  | 'INVALID_RESPONSE'
  | 'CHALLENGE_FAILED'
  | 'TOKEN_EXPIRED';
