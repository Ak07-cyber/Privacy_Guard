/**
 * PassiveGuard SDK - Main Entry Point
 * ML-based passive bot detection to replace CAPTCHA
 */

// Core
export { PassiveGuard } from './core/PassiveGuard';
export { default } from './core/PassiveGuard';

// Hooks
export { usePassiveGuard } from './hooks/usePassiveGuard';
export type { UsePassiveGuardOptions, UsePassiveGuardReturn } from './hooks/usePassiveGuard';

// Collectors
export { EnvironmentalCollector, createEnvironmentalCollector } from './collectors/environmental';
export { BehavioralCollector, createBehavioralCollector } from './collectors/behavioral';

// Utils
export { ApiClient, createApiClient } from './utils/api';
export type { ApiClientConfig } from './utils/api';

// Types
export * from './types';
