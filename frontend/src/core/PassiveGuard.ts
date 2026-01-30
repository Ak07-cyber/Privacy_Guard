/**
 * PassiveGuard - Main SDK Class
 * ML-based passive bot detection to replace CAPTCHA
 */

import {
  PassiveGuardConfig,
  VerificationRequest,
  VerificationResult,
  EnvironmentalData,
  BehavioralData,
  Challenge,
  ChallengeResponse,
  PassiveGuardEvent,
  PassiveGuardEventData,
  EventCallback,
  PassiveGuardError,
} from '../types';
import { EnvironmentalCollector } from '../collectors/environmental';
import { BehavioralCollector } from '../collectors/behavioral';
import { ApiClient } from '../utils/api';

export class PassiveGuard {
  private config: Required<PassiveGuardConfig>;
  private environmentalCollector: EnvironmentalCollector;
  private behavioralCollector: BehavioralCollector;
  private apiClient: ApiClient;
  private eventListeners: Map<PassiveGuardEvent, EventCallback[]> = new Map();
  private initialized: boolean = false;
  private requestId: string;
  private environmentalData: EnvironmentalData | null = null;

  constructor(config: PassiveGuardConfig) {
    // Set defaults
    this.config = {
      apiEndpoint: config.apiEndpoint,
      siteKey: config.siteKey,
      debug: config.debug ?? false,
      collectionTimeout: config.collectionTimeout ?? 30000,
      enableBehavioral: config.enableBehavioral ?? true,
      enableEnvironmental: config.enableEnvironmental ?? true,
      privacyMode: config.privacyMode ?? false,
      onChallenge: config.onChallenge ?? (async () => ({
        challengeId: '',
        response: null,
        completionTime: 0,
        accuracy: 0,
      })),
      onVerify: config.onVerify ?? (() => {}),
    };

    this.requestId = this.generateRequestId();
    this.environmentalCollector = new EnvironmentalCollector(this.config.privacyMode);
    this.behavioralCollector = new BehavioralCollector();
    this.apiClient = new ApiClient({
      endpoint: this.config.apiEndpoint,
      timeout: 10000,
      retries: 2,
    });
  }

  /**
   * Initialize the PassiveGuard SDK
   */
  async init(): Promise<void> {
    if (this.initialized) {
      this.log('Already initialized');
      return;
    }

    try {
      this.emit('init', {});

      // Start behavioral collection
      if (this.config.enableBehavioral) {
        this.behavioralCollector.start();
      }

      // Collect environmental data immediately
      if (this.config.enableEnvironmental) {
        this.emit('collecting', { type: 'environmental' });
        this.environmentalData = await this.environmentalCollector.collect();
        this.emit('collected', { type: 'environmental' });
      }

      this.initialized = true;
      this.log('Initialized successfully');
    } catch (error) {
      this.emit('error', { error });
      throw new PassiveGuardError(
        'Failed to initialize PassiveGuard',
        'INIT_FAILED',
        error
      );
    }
  }

  /**
   * Verify the current user
   */
  async verify(): Promise<VerificationResult> {
    if (!this.initialized) {
      await this.init();
    }

    try {
      this.emit('verifying', {});

      // Collect environmental data if not already done
      let environmental: EnvironmentalData;
      if (this.environmentalData && this.config.enableEnvironmental) {
        environmental = this.environmentalData;
      } else {
        environmental = await this.environmentalCollector.collect();
      }

      // Get behavioral data
      let behavioral: BehavioralData;
      if (this.config.enableBehavioral) {
        behavioral = this.behavioralCollector.getData();
      } else {
        behavioral = this.getEmptyBehavioralData();
      }

      // Prepare verification request
      const request: VerificationRequest = {
        siteKey: this.config.siteKey,
        environmental,
        behavioral,
        requestId: this.requestId,
        timestamp: Date.now(),
      };

      // Send to backend
      let result = await this.apiClient.verify(request);

      // Handle challenge if needed
      if (result.challengeRequired && result.challenge) {
        this.emit('challenge', { challenge: result.challenge });
        
        const challengeResponse = await this.handleChallenge(result.challenge);
        
        // Re-verify with challenge response
        request.challengeResponse = challengeResponse;
        result = await this.apiClient.verify(request);
      }

      this.emit('verified', { result });
      this.config.onVerify(result);

      return result;
    } catch (error) {
      this.emit('error', { error });
      
      if (error instanceof PassiveGuardError) {
        throw error;
      }
      
      throw new PassiveGuardError(
        'Verification failed',
        'NETWORK_ERROR',
        error
      );
    }
  }

  /**
   * Get verification token (shorthand for verify().token)
   */
  async getToken(): Promise<string> {
    const result = await this.verify();
    return result.token;
  }

  /**
   * Reset the collector (for new session)
   */
  reset(): void {
    this.requestId = this.generateRequestId();
    this.environmentalData = null;
    this.behavioralCollector.reset();
    
    if (this.config.enableBehavioral) {
      this.behavioralCollector.start();
    }

    this.log('Reset complete');
  }

  /**
   * Destroy the SDK instance
   */
  destroy(): void {
    this.behavioralCollector.stop();
    this.eventListeners.clear();
    this.initialized = false;
    this.log('Destroyed');
  }

  /**
   * Add event listener
   */
  on(event: PassiveGuardEvent, callback: EventCallback): void {
    const listeners = this.eventListeners.get(event) || [];
    listeners.push(callback);
    this.eventListeners.set(event, listeners);
  }

  /**
   * Remove event listener
   */
  off(event: PassiveGuardEvent, callback: EventCallback): void {
    const listeners = this.eventListeners.get(event) || [];
    const index = listeners.indexOf(callback);
    if (index > -1) {
      listeners.splice(index, 1);
      this.eventListeners.set(event, listeners);
    }
  }

  /**
   * Handle challenge interaction
   */
  private async handleChallenge(challenge: Challenge): Promise<ChallengeResponse> {
    return this.config.onChallenge(challenge);
  }

  /**
   * Emit event to listeners
   */
  private emit(event: PassiveGuardEvent, data: any): void {
    const eventData: PassiveGuardEventData = {
      event,
      timestamp: Date.now(),
      data,
    };

    const listeners = this.eventListeners.get(event) || [];
    for (const callback of listeners) {
      try {
        callback(eventData);
      } catch (error) {
        this.log('Event listener error:', error);
      }
    }
  }

  /**
   * Generate unique request ID
   */
  private generateRequestId(): string {
    return `pg_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`;
  }

  /**
   * Get empty behavioral data structure
   */
  private getEmptyBehavioralData(): BehavioralData {
    return {
      mouse: {
        movements: [],
        clicks: [],
        movementStats: {
          totalDistance: 0,
          averageVelocity: 0,
          maxVelocity: 0,
          straightLineRatio: 0,
          directionChanges: 0,
          pauseCount: 0,
          jitterScore: 0,
        },
      },
      keyboard: {
        keyPresses: [],
        typingStats: {
          averageDwellTime: 0,
          averageFlightTime: 0,
          typingSpeed: 0,
          errorRate: 0,
          rhythmConsistency: 0,
        },
      },
      scroll: {
        events: [],
        stats: {
          totalScroll: 0,
          averageVelocity: 0,
          smoothness: 0,
          directionChanges: 0,
        },
      },
      touch: {
        gestures: [],
        multiTouchEvents: 0,
        averagePressure: 0,
      },
      focus: {
        focusEvents: [],
        totalFocusTime: 0,
        blurCount: 0,
        visibilityChanges: 0,
      },
      timing: {
        pageLoadTime: 0,
        timeToFirstInteraction: -1,
        totalInteractionTime: 0,
        idlePeriods: [],
        interactionGaps: [],
      },
    };
  }

  /**
   * Debug logging
   */
  private log(...args: any[]): void {
    if (this.config.debug) {
      console.log('[PassiveGuard]', ...args);
    }
  }
}

// Default export
export default PassiveGuard;
