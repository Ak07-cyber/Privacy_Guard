/**
 * Behavioral Data Collector
 * Tracks user interaction patterns for bot detection
 * Captures mouse movements, keyboard patterns, scrolling, and timing
 */

import {
  BehavioralData,
  MouseData,
  MouseMovement,
  ClickEvent,
  MovementStats,
  KeyboardData,
  KeyPressEvent,
  TypingStats,
  ScrollData,
  ScrollEvent,
  ScrollStats,
  TouchData,
  GestureEvent,
  FocusData,
  FocusEvent,
  TimingData,
} from '../types';

export class BehavioralCollector {
  private isCollecting: boolean = false;
  private startTime: number = 0;

  // Mouse data
  private mouseMovements: MouseMovement[] = [];
  private mouseClicks: ClickEvent[] = [];
  private lastMousePosition: { x: number; y: number; time: number } | null = null;

  // Keyboard data
  private keyPresses: KeyPressEvent[] = [];
  private keyDownTimes: Map<string, number> = new Map();
  private lastKeyUpTime: number = 0;

  // Scroll data
  private scrollEvents: ScrollEvent[] = [];
  private lastScrollTime: number = 0;

  // Touch data
  private touchGestures: GestureEvent[] = [];
  private touchStart: { x: number; y: number; time: number } | null = null;

  // Focus data
  private focusEvents: FocusEvent[] = [];
  private focusStartTime: number = 0;

  // Timing data
  private firstInteractionTime: number | null = null;
  private idlePeriods: number[] = [];
  private lastActivityTime: number = 0;

  // Configuration
  private maxMouseMovements: number = 500;
  private maxKeyPresses: number = 100;
  private maxScrollEvents: number = 100;
  private sampleRate: number = 50; // ms between samples

  // Event handlers (bound)
  private boundHandlers: Map<string, EventListener> = new Map();

  constructor() {
    this.bindHandlers();
  }

  /**
   * Bind event handlers
   */
  private bindHandlers(): void {
    this.boundHandlers.set('mousemove', this.handleMouseMove.bind(this) as EventListener);
    this.boundHandlers.set('click', this.handleClick.bind(this) as EventListener);
    this.boundHandlers.set('keydown', this.handleKeyDown.bind(this) as EventListener);
    this.boundHandlers.set('keyup', this.handleKeyUp.bind(this) as EventListener);
    this.boundHandlers.set('scroll', this.handleScroll.bind(this) as EventListener);
    this.boundHandlers.set('touchstart', this.handleTouchStart.bind(this) as EventListener);
    this.boundHandlers.set('touchend', this.handleTouchEnd.bind(this) as EventListener);
    this.boundHandlers.set('focus', this.handleFocus.bind(this) as EventListener);
    this.boundHandlers.set('blur', this.handleBlur.bind(this) as EventListener);
    this.boundHandlers.set('visibilitychange', this.handleVisibilityChange.bind(this) as EventListener);
  }

  /**
   * Start collecting behavioral data
   */
  start(): void {
    if (this.isCollecting) return;

    this.isCollecting = true;
    this.startTime = Date.now();
    this.focusStartTime = this.startTime;
    this.lastActivityTime = this.startTime;

    // Add event listeners
    document.addEventListener('mousemove', this.boundHandlers.get('mousemove')!, { passive: true });
    document.addEventListener('click', this.boundHandlers.get('click')!, { passive: true });
    document.addEventListener('keydown', this.boundHandlers.get('keydown')!, { passive: true });
    document.addEventListener('keyup', this.boundHandlers.get('keyup')!, { passive: true });
    window.addEventListener('scroll', this.boundHandlers.get('scroll')!, { passive: true });
    document.addEventListener('touchstart', this.boundHandlers.get('touchstart')!, { passive: true });
    document.addEventListener('touchend', this.boundHandlers.get('touchend')!, { passive: true });
    window.addEventListener('focus', this.boundHandlers.get('focus')!);
    window.addEventListener('blur', this.boundHandlers.get('blur')!);
    document.addEventListener('visibilitychange', this.boundHandlers.get('visibilitychange')!);
  }

  /**
   * Stop collecting and return data
   */
  stop(): BehavioralData {
    this.isCollecting = false;

    // Remove event listeners
    document.removeEventListener('mousemove', this.boundHandlers.get('mousemove')!);
    document.removeEventListener('click', this.boundHandlers.get('click')!);
    document.removeEventListener('keydown', this.boundHandlers.get('keydown')!);
    document.removeEventListener('keyup', this.boundHandlers.get('keyup')!);
    window.removeEventListener('scroll', this.boundHandlers.get('scroll')!);
    document.removeEventListener('touchstart', this.boundHandlers.get('touchstart')!);
    document.removeEventListener('touchend', this.boundHandlers.get('touchend')!);
    window.removeEventListener('focus', this.boundHandlers.get('focus')!);
    window.removeEventListener('blur', this.boundHandlers.get('blur')!);
    document.removeEventListener('visibilitychange', this.boundHandlers.get('visibilitychange')!);

    return this.getData();
  }

  /**
   * Get collected behavioral data
   */
  getData(): BehavioralData {
    return {
      mouse: this.getMouseData(),
      keyboard: this.getKeyboardData(),
      scroll: this.getScrollData(),
      touch: this.getTouchData(),
      focus: this.getFocusData(),
      timing: this.getTimingData(),
    };
  }

  /**
   * Handle mouse movement
   */
  private handleMouseMove(event: MouseEvent): void {
    if (!this.isCollecting) return;
    if (this.mouseMovements.length >= this.maxMouseMovements) return;

    const now = Date.now();
    
    // Sample rate limiting
    if (this.lastMousePosition && now - this.lastMousePosition.time < this.sampleRate) {
      return;
    }

    this.recordActivity(now);

    const x = event.clientX;
    const y = event.clientY;
    
    let velocity = 0;
    let acceleration = 0;
    let angle = 0;

    if (this.lastMousePosition) {
      const dx = x - this.lastMousePosition.x;
      const dy = y - this.lastMousePosition.y;
      const dt = (now - this.lastMousePosition.time) / 1000; // seconds
      
      const distance = Math.sqrt(dx * dx + dy * dy);
      velocity = dt > 0 ? distance / dt : 0;
      
      // Calculate angle in degrees
      angle = Math.atan2(dy, dx) * (180 / Math.PI);
      
      // Calculate acceleration from previous movement
      if (this.mouseMovements.length > 0) {
        const lastMovement = this.mouseMovements[this.mouseMovements.length - 1];
        acceleration = dt > 0 ? (velocity - lastMovement.velocity) / dt : 0;
      }
    }

    this.mouseMovements.push({
      x,
      y,
      timestamp: now,
      velocity,
      acceleration,
      angle,
    });

    this.lastMousePosition = { x, y, time: now };
  }

  /**
   * Handle click events
   */
  private handleClick(event: MouseEvent): void {
    if (!this.isCollecting) return;

    this.recordActivity(Date.now());

    // Get target element info (sanitized)
    let target = 'unknown';
    if (event.target instanceof HTMLElement) {
      target = event.target.tagName.toLowerCase();
      if (event.target.id) {
        target += `#${event.target.id.substring(0, 20)}`;
      }
    }

    this.mouseClicks.push({
      x: event.clientX,
      y: event.clientY,
      timestamp: Date.now(),
      button: event.button,
      target,
    });
  }

  /**
   * Handle key down
   */
  private handleKeyDown(event: KeyboardEvent): void {
    if (!this.isCollecting) return;
    if (this.keyPresses.length >= this.maxKeyPresses) return;

    const now = Date.now();
    this.recordActivity(now);

    // Store key down time (use code instead of key for privacy)
    const keyId = this.obfuscateKey(event.code);
    if (!this.keyDownTimes.has(keyId)) {
      this.keyDownTimes.set(keyId, now);
    }
  }

  /**
   * Handle key up
   */
  private handleKeyUp(event: KeyboardEvent): void {
    if (!this.isCollecting) return;
    if (this.keyPresses.length >= this.maxKeyPresses) return;

    const now = Date.now();
    const keyId = this.obfuscateKey(event.code);
    const keyDownTime = this.keyDownTimes.get(keyId);

    if (keyDownTime) {
      const dwellTime = now - keyDownTime;
      const flightTime = this.lastKeyUpTime > 0 ? keyDownTime - this.lastKeyUpTime : 0;

      this.keyPresses.push({
        key: keyId,
        keyDownTime,
        keyUpTime: now,
        dwellTime,
        flightTime,
      });

      this.keyDownTimes.delete(keyId);
      this.lastKeyUpTime = now;
    }
  }

  /**
   * Obfuscate key for privacy
   */
  private obfuscateKey(code: string): string {
    // Categorize keys instead of storing actual keys
    if (code.startsWith('Key')) return 'letter';
    if (code.startsWith('Digit')) return 'digit';
    if (code.startsWith('Arrow')) return 'arrow';
    if (code === 'Space') return 'space';
    if (code === 'Backspace' || code === 'Delete') return 'delete';
    if (code === 'Enter') return 'enter';
    if (code === 'Tab') return 'tab';
    if (code.startsWith('Shift') || code.startsWith('Control') || code.startsWith('Alt')) return 'modifier';
    return 'other';
  }

  /**
   * Handle scroll events
   */
  private handleScroll(event: Event): void {
    if (!this.isCollecting) return;
    if (this.scrollEvents.length >= this.maxScrollEvents) return;

    const now = Date.now();

    // Sample rate limiting for scroll
    if (now - this.lastScrollTime < this.sampleRate) {
      return;
    }

    this.recordActivity(now);

    const scrollY = window.scrollY;
    const scrollX = window.scrollX;
    
    let deltaY = 0;
    let deltaX = 0;
    let velocity = 0;

    if (this.scrollEvents.length > 0) {
      const lastScroll = this.scrollEvents[this.scrollEvents.length - 1];
      deltaY = scrollY - (lastScroll.deltaY || 0);
      deltaX = scrollX - (lastScroll.deltaX || 0);
      
      const dt = (now - this.lastScrollTime) / 1000;
      const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
      velocity = dt > 0 ? distance / dt : 0;
    }

    this.scrollEvents.push({
      deltaX: scrollX,
      deltaY: scrollY,
      timestamp: now,
      velocity,
    });

    this.lastScrollTime = now;
  }

  /**
   * Handle touch start
   */
  private handleTouchStart(event: TouchEvent): void {
    if (!this.isCollecting) return;

    this.recordActivity(Date.now());

    if (event.touches.length > 0) {
      const touch = event.touches[0];
      this.touchStart = {
        x: touch.clientX,
        y: touch.clientY,
        time: Date.now(),
      };
    }
  }

  /**
   * Handle touch end
   */
  private handleTouchEnd(event: TouchEvent): void {
    if (!this.isCollecting || !this.touchStart) return;

    const now = Date.now();
    const duration = now - this.touchStart.time;

    // Determine gesture type based on movement and duration
    let gestureType: GestureEvent['type'] = 'tap';
    
    if (event.changedTouches.length > 0) {
      const touch = event.changedTouches[0];
      const dx = touch.clientX - this.touchStart.x;
      const dy = touch.clientY - this.touchStart.y;
      const distance = Math.sqrt(dx * dx + dy * dy);

      if (distance > 50) {
        gestureType = 'swipe';
      }
    }

    this.touchGestures.push({
      type: gestureType,
      timestamp: now,
      duration,
      touches: event.touches.length + 1,
    });

    this.touchStart = null;
  }

  /**
   * Handle focus event
   */
  private handleFocus(): void {
    if (!this.isCollecting) return;

    const now = Date.now();
    this.focusStartTime = now;
    
    this.focusEvents.push({
      type: 'focus',
      timestamp: now,
    });
  }

  /**
   * Handle blur event
   */
  private handleBlur(): void {
    if (!this.isCollecting) return;

    const now = Date.now();
    const duration = now - this.focusStartTime;

    this.focusEvents.push({
      type: 'blur',
      timestamp: now,
      duration,
    });
  }

  /**
   * Handle visibility change
   */
  private handleVisibilityChange(): void {
    if (!this.isCollecting) return;

    this.focusEvents.push({
      type: 'visibilitychange',
      timestamp: Date.now(),
    });
  }

  /**
   * Record activity for idle detection
   */
  private recordActivity(timestamp: number): void {
    if (this.firstInteractionTime === null) {
      this.firstInteractionTime = timestamp;
    }

    // Track idle periods (gaps > 2 seconds)
    const gap = timestamp - this.lastActivityTime;
    if (gap > 2000 && this.lastActivityTime > 0) {
      this.idlePeriods.push(gap);
    }

    this.lastActivityTime = timestamp;
  }

  /**
   * Calculate mouse movement statistics
   */
  private calculateMovementStats(): MovementStats {
    const movements = this.mouseMovements;
    
    if (movements.length < 2) {
      return {
        totalDistance: 0,
        averageVelocity: 0,
        maxVelocity: 0,
        straightLineRatio: 0,
        directionChanges: 0,
        pauseCount: 0,
        jitterScore: 0,
      };
    }

    let totalDistance = 0;
    let maxVelocity = 0;
    let velocitySum = 0;
    let directionChanges = 0;
    let pauseCount = 0;
    let jitterSum = 0;
    let lastAngle: number | null = null;

    for (let i = 1; i < movements.length; i++) {
      const prev = movements[i - 1];
      const curr = movements[i];

      const dx = curr.x - prev.x;
      const dy = curr.y - prev.y;
      const distance = Math.sqrt(dx * dx + dy * dy);

      totalDistance += distance;
      velocitySum += curr.velocity;
      maxVelocity = Math.max(maxVelocity, curr.velocity);

      // Direction changes (angle difference > 45 degrees)
      if (lastAngle !== null) {
        const angleDiff = Math.abs(curr.angle - lastAngle);
        if (angleDiff > 45 && angleDiff < 315) {
          directionChanges++;
        }
      }
      lastAngle = curr.angle;

      // Pause detection (very low velocity)
      if (curr.velocity < 10) {
        pauseCount++;
      }

      // Jitter detection (small rapid movements)
      if (distance < 5 && curr.velocity > 0) {
        jitterSum++;
      }
    }

    // Calculate straight line ratio
    const first = movements[0];
    const last = movements[movements.length - 1];
    const straightLineDistance = Math.sqrt(
      Math.pow(last.x - first.x, 2) + Math.pow(last.y - first.y, 2)
    );
    const straightLineRatio = totalDistance > 0 ? straightLineDistance / totalDistance : 0;

    return {
      totalDistance,
      averageVelocity: velocitySum / (movements.length - 1),
      maxVelocity,
      straightLineRatio,
      directionChanges,
      pauseCount,
      jitterScore: jitterSum / movements.length,
    };
  }

  /**
   * Calculate typing statistics
   */
  private calculateTypingStats(): TypingStats {
    const presses = this.keyPresses;

    if (presses.length < 2) {
      return {
        averageDwellTime: 0,
        averageFlightTime: 0,
        typingSpeed: 0,
        errorRate: 0,
        rhythmConsistency: 0,
      };
    }

    let dwellSum = 0;
    let flightSum = 0;
    let deleteCount = 0;
    const dwellTimes: number[] = [];
    const flightTimes: number[] = [];

    for (const press of presses) {
      dwellSum += press.dwellTime;
      dwellTimes.push(press.dwellTime);
      
      if (press.flightTime > 0) {
        flightSum += press.flightTime;
        flightTimes.push(press.flightTime);
      }

      if (press.key === 'delete') {
        deleteCount++;
      }
    }

    const avgDwell = dwellSum / presses.length;
    const avgFlight = flightTimes.length > 0 ? flightSum / flightTimes.length : 0;

    // Calculate rhythm consistency (lower variance = more consistent)
    let dwellVariance = 0;
    for (const dwell of dwellTimes) {
      dwellVariance += Math.pow(dwell - avgDwell, 2);
    }
    dwellVariance = Math.sqrt(dwellVariance / dwellTimes.length);
    const rhythmConsistency = avgDwell > 0 ? 1 - Math.min(dwellVariance / avgDwell, 1) : 0;

    // Calculate typing speed (keys per minute)
    const totalTime = presses.length > 0 
      ? (presses[presses.length - 1].keyUpTime - presses[0].keyDownTime) / 1000 / 60
      : 0;
    const typingSpeed = totalTime > 0 ? presses.length / totalTime : 0;

    return {
      averageDwellTime: avgDwell,
      averageFlightTime: avgFlight,
      typingSpeed,
      errorRate: presses.length > 0 ? deleteCount / presses.length : 0,
      rhythmConsistency,
    };
  }

  /**
   * Calculate scroll statistics
   */
  private calculateScrollStats(): ScrollStats {
    const events = this.scrollEvents;

    if (events.length < 2) {
      return {
        totalScroll: 0,
        averageVelocity: 0,
        smoothness: 0,
        directionChanges: 0,
      };
    }

    let totalScroll = 0;
    let velocitySum = 0;
    let directionChanges = 0;
    let lastDirection: 'up' | 'down' | null = null;
    const velocities: number[] = [];

    for (let i = 1; i < events.length; i++) {
      const prev = events[i - 1];
      const curr = events[i];

      const deltaY = curr.deltaY - prev.deltaY;
      totalScroll += Math.abs(deltaY);
      velocitySum += curr.velocity;
      velocities.push(curr.velocity);

      const currentDirection = deltaY > 0 ? 'down' : 'up';
      if (lastDirection && currentDirection !== lastDirection) {
        directionChanges++;
      }
      lastDirection = currentDirection;
    }

    // Calculate smoothness (lower velocity variance = smoother)
    const avgVelocity = velocitySum / (events.length - 1);
    let velocityVariance = 0;
    for (const v of velocities) {
      velocityVariance += Math.pow(v - avgVelocity, 2);
    }
    velocityVariance = Math.sqrt(velocityVariance / velocities.length);
    const smoothness = avgVelocity > 0 ? 1 - Math.min(velocityVariance / avgVelocity, 1) : 0;

    return {
      totalScroll,
      averageVelocity: avgVelocity,
      smoothness,
      directionChanges,
    };
  }

  /**
   * Get mouse data
   */
  private getMouseData(): MouseData {
    return {
      movements: this.mouseMovements.slice(-100), // Last 100 movements
      clicks: this.mouseClicks,
      movementStats: this.calculateMovementStats(),
    };
  }

  /**
   * Get keyboard data
   */
  private getKeyboardData(): KeyboardData {
    return {
      keyPresses: this.keyPresses,
      typingStats: this.calculateTypingStats(),
    };
  }

  /**
   * Get scroll data
   */
  private getScrollData(): ScrollData {
    return {
      events: this.scrollEvents.slice(-50), // Last 50 events
      stats: this.calculateScrollStats(),
    };
  }

  /**
   * Get touch data
   */
  private getTouchData(): TouchData {
    let totalPressure = 0;
    let multiTouchCount = 0;

    for (const gesture of this.touchGestures) {
      if (gesture.touches > 1) multiTouchCount++;
    }

    return {
      gestures: this.touchGestures,
      multiTouchEvents: multiTouchCount,
      averagePressure: this.touchGestures.length > 0 ? totalPressure / this.touchGestures.length : 0,
    };
  }

  /**
   * Get focus data
   */
  private getFocusData(): FocusData {
    let totalFocusTime = 0;
    let blurCount = 0;
    let visibilityChanges = 0;

    for (const event of this.focusEvents) {
      if (event.type === 'blur') {
        blurCount++;
        totalFocusTime += event.duration || 0;
      }
      if (event.type === 'visibilitychange') {
        visibilityChanges++;
      }
    }

    // Add current focus time if still focused
    if (this.focusStartTime > 0) {
      totalFocusTime += Date.now() - this.focusStartTime;
    }

    return {
      focusEvents: this.focusEvents,
      totalFocusTime,
      blurCount,
      visibilityChanges,
    };
  }

  /**
   * Get timing data
   */
  private getTimingData(): TimingData {
    const now = Date.now();
    
    // Calculate interaction gaps
    const interactionGaps: number[] = [];
    let lastTime = this.startTime;
    
    for (const movement of this.mouseMovements) {
      const gap = movement.timestamp - lastTime;
      if (gap > 100) {
        interactionGaps.push(gap);
      }
      lastTime = movement.timestamp;
    }

    return {
      pageLoadTime: this.startTime - performance.timing.navigationStart,
      timeToFirstInteraction: this.firstInteractionTime 
        ? this.firstInteractionTime - this.startTime 
        : -1,
      totalInteractionTime: now - this.startTime,
      idlePeriods: this.idlePeriods,
      interactionGaps: interactionGaps.slice(-20),
    };
  }

  /**
   * Reset collector
   */
  reset(): void {
    this.mouseMovements = [];
    this.mouseClicks = [];
    this.lastMousePosition = null;
    this.keyPresses = [];
    this.keyDownTimes.clear();
    this.lastKeyUpTime = 0;
    this.scrollEvents = [];
    this.lastScrollTime = 0;
    this.touchGestures = [];
    this.touchStart = null;
    this.focusEvents = [];
    this.focusStartTime = 0;
    this.firstInteractionTime = null;
    this.idlePeriods = [];
    this.lastActivityTime = 0;
  }
}

export const createBehavioralCollector = () => {
  return new BehavioralCollector();
};
