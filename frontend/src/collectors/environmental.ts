/**
 * Environmental Data Collector
 * Collects browser, hardware, and environment fingerprint data
 * Privacy-focused: All identifiable data is hashed
 */

import {
  EnvironmentalData,
  BrowserInfo,
  ScreenInfo,
  HardwareInfo,
  WebGLInfo,
  TimezoneInfo,
  FeatureDetection,
  PluginInfo,
} from '../types';
import { hashString, generateCanvasFingerprint, generateAudioFingerprint } from '../utils/fingerprint';

export class EnvironmentalCollector {
  private privacyMode: boolean;

  constructor(privacyMode: boolean = false) {
    this.privacyMode = privacyMode;
  }

  /**
   * Collect all environmental data
   */
  async collect(): Promise<EnvironmentalData> {
    const [
      browser,
      screen,
      hardware,
      webgl,
      canvasHash,
      audioHash,
      timezone,
      features,
    ] = await Promise.all([
      this.collectBrowserInfo(),
      this.collectScreenInfo(),
      this.collectHardwareInfo(),
      this.collectWebGLInfo(),
      generateCanvasFingerprint(),
      generateAudioFingerprint(),
      this.collectTimezoneInfo(),
      this.detectFeatures(),
    ]);

    return {
      browser,
      screen,
      hardware,
      webgl,
      canvasHash,
      audioHash,
      timezone,
      features,
      timestamp: Date.now(),
    };
  }

  /**
   * Collect browser information
   */
  private collectBrowserInfo(): BrowserInfo {
    const nav = window.navigator;

    const plugins: PluginInfo[] = [];
    if (!this.privacyMode && nav.plugins) {
      for (let i = 0; i < Math.min(nav.plugins.length, 10); i++) {
        const plugin = nav.plugins[i];
        plugins.push({
          name: hashString(plugin.name),
          description: hashString(plugin.description),
          filename: hashString(plugin.filename),
        });
      }
    }

    const mimeTypes: string[] = [];
    if (!this.privacyMode && nav.mimeTypes) {
      for (let i = 0; i < Math.min(nav.mimeTypes.length, 10); i++) {
        mimeTypes.push(hashString(nav.mimeTypes[i].type));
      }
    }

    return {
      userAgent: this.privacyMode ? hashString(nav.userAgent) : nav.userAgent,
      language: nav.language,
      languages: [...(nav.languages || [])],
      platform: nav.platform,
      vendor: nav.vendor,
      cookiesEnabled: nav.cookieEnabled,
      doNotTrack: nav.doNotTrack,
      plugins,
      mimeTypes,
    };
  }

  /**
   * Collect screen and display information
   */
  private collectScreenInfo(): ScreenInfo {
    const screen = window.screen;
    
    return {
      width: screen.width,
      height: screen.height,
      availWidth: screen.availWidth,
      availHeight: screen.availHeight,
      colorDepth: screen.colorDepth,
      pixelDepth: screen.pixelDepth,
      devicePixelRatio: window.devicePixelRatio || 1,
      orientation: screen.orientation?.type || 'unknown',
    };
  }

  /**
   * Collect hardware capabilities
   */
  private collectHardwareInfo(): HardwareInfo {
    const nav = window.navigator as any;

    return {
      hardwareConcurrency: nav.hardwareConcurrency || 0,
      deviceMemory: nav.deviceMemory || null,
      maxTouchPoints: nav.maxTouchPoints || 0,
      hasTouch: 'ontouchstart' in window || nav.maxTouchPoints > 0,
      hasPointer: 'PointerEvent' in window,
    };
  }

  /**
   * Collect WebGL information for GPU fingerprinting
   */
  private collectWebGLInfo(): WebGLInfo {
    const defaultInfo: WebGLInfo = {
      vendor: 'unknown',
      renderer: 'unknown',
      version: 'unknown',
      shadingLanguageVersion: 'unknown',
      extensions: [],
      hash: '',
    };

    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      
      if (!gl) return defaultInfo;

      const glContext = gl as WebGLRenderingContext;
      const debugInfo = glContext.getExtension('WEBGL_debug_renderer_info');

      const vendor = debugInfo 
        ? glContext.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL)
        : glContext.getParameter(glContext.VENDOR);
      
      const renderer = debugInfo
        ? glContext.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL)
        : glContext.getParameter(glContext.RENDERER);

      const version = glContext.getParameter(glContext.VERSION);
      const shadingLanguageVersion = glContext.getParameter(glContext.SHADING_LANGUAGE_VERSION);
      
      const extensions = glContext.getSupportedExtensions() || [];

      const info: WebGLInfo = {
        vendor: this.privacyMode ? hashString(vendor) : vendor,
        renderer: this.privacyMode ? hashString(renderer) : renderer,
        version,
        shadingLanguageVersion,
        extensions: extensions.slice(0, 20),
        hash: '',
      };

      // Generate combined hash
      info.hash = hashString(`${vendor}|${renderer}|${version}|${extensions.join(',')}`);

      return info;
    } catch (e) {
      return defaultInfo;
    }
  }

  /**
   * Collect timezone information
   */
  private collectTimezoneInfo(): TimezoneInfo {
    const date = new Date();
    const offset = date.getTimezoneOffset();
    
    let timezone = 'unknown';
    try {
      timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    } catch (e) {
      // Fallback
    }

    // Detect DST
    const jan = new Date(date.getFullYear(), 0, 1);
    const jul = new Date(date.getFullYear(), 6, 1);
    const isDST = date.getTimezoneOffset() < Math.max(jan.getTimezoneOffset(), jul.getTimezoneOffset());

    return {
      offset,
      timezone,
      isDST,
    };
  }

  /**
   * Detect browser features and automation flags
   */
  private detectFeatures(): FeatureDetection {
    const nav = window.navigator as any;
    const win = window as any;

    // Detect webdriver and automation flags
    const automationFlags: string[] = [];

    if (nav.webdriver) automationFlags.push('webdriver');
    if (win.__nightmare) automationFlags.push('nightmare');
    if (win._phantom || win.phantom) automationFlags.push('phantom');
    if (win.__selenium_unwrapped) automationFlags.push('selenium');
    if (win.callPhantom || win._phantom) automationFlags.push('phantomjs');
    if (win.domAutomation || win.domAutomationController) automationFlags.push('domAutomation');
    if (document.documentElement.getAttribute('webdriver')) automationFlags.push('webdriver-attr');
    if (nav.plugins && nav.plugins.length === 0 && nav.userAgent.indexOf('HeadlessChrome') !== -1) {
      automationFlags.push('headless-chrome');
    }

    // Check for unusual properties
    try {
      if (Object.keys((window as any).chrome || {}).length === 0) {
        automationFlags.push('empty-chrome-object');
      }
    } catch (e) {}

    // Check permissions (non-blocking)
    let hasNotificationPermission = false;
    let hasGeolocationPermission = false;

    try {
      if ('Notification' in window) {
        hasNotificationPermission = Notification.permission === 'granted';
      }
    } catch (e) {}

    return {
      webdriver: nav.webdriver === true,
      automationFlags,
      hasNotificationPermission,
      hasGeolocationPermission,
      localStorage: this.testStorage('localStorage'),
      sessionStorage: this.testStorage('sessionStorage'),
      indexedDB: 'indexedDB' in window,
      webSocket: 'WebSocket' in window,
      webWorker: 'Worker' in window,
      serviceWorker: 'serviceWorker' in navigator,
    };
  }

  /**
   * Test storage availability
   */
  private testStorage(type: 'localStorage' | 'sessionStorage'): boolean {
    try {
      const storage = window[type];
      const testKey = '__passiveguard_test__';
      storage.setItem(testKey, 'test');
      storage.removeItem(testKey);
      return true;
    } catch (e) {
      return false;
    }
  }
}

export const createEnvironmentalCollector = (privacyMode: boolean = false) => {
  return new EnvironmentalCollector(privacyMode);
};
