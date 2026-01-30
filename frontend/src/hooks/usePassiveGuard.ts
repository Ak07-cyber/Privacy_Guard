/**
 * React Hook for PassiveGuard Integration
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { PassiveGuard } from '../core/PassiveGuard';
import {
  PassiveGuardConfig,
  VerificationResult,
  Challenge,
  PassiveGuardError,
} from '../types';

export interface UsePassiveGuardOptions extends Omit<PassiveGuardConfig, 'onChallenge' | 'onVerify'> {
  autoInit?: boolean;
}

export interface UsePassiveGuardReturn {
  /** Initialize the SDK */
  init: () => Promise<void>;
  /** Verify the user */
  verify: () => Promise<VerificationResult>;
  /** Get verification token */
  getToken: () => Promise<string>;
  /** Reset the SDK */
  reset: () => void;
  /** Initialization state */
  isInitialized: boolean;
  /** Loading state */
  isLoading: boolean;
  /** Last verification result */
  result: VerificationResult | null;
  /** Current challenge (if any) */
  challenge: Challenge | null;
  /** Error state */
  error: PassiveGuardError | null;
  /** Is user verified as human */
  isHuman: boolean;
  /** Risk score (0-1) */
  riskScore: number;
}

export function usePassiveGuard(options: UsePassiveGuardOptions): UsePassiveGuardReturn {
  const [isInitialized, setIsInitialized] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<VerificationResult | null>(null);
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [error, setError] = useState<PassiveGuardError | null>(null);

  const guardRef = useRef<PassiveGuard | null>(null);
  const challengeResolverRef = useRef<((response: any) => void) | null>(null);

  // Initialize PassiveGuard instance
  useEffect(() => {
    const config: PassiveGuardConfig = {
      ...options,
      onChallenge: async (ch: Challenge) => {
        setChallenge(ch);
        
        // Wait for challenge response
        return new Promise((resolve) => {
          challengeResolverRef.current = resolve;
        });
      },
      onVerify: (res: VerificationResult) => {
        setResult(res);
        setChallenge(null);
      },
    };

    guardRef.current = new PassiveGuard(config);

    // Auto-init if enabled
    if (options.autoInit !== false) {
      guardRef.current.init()
        .then(() => setIsInitialized(true))
        .catch((err: unknown) => {
          if (err instanceof PassiveGuardError) {
            setError(err);
          } else {
            setError(new PassiveGuardError(
              err instanceof Error ? err.message : 'Unknown error',
              'UNKNOWN_ERROR',
              err
            ));
          }
        });
    }

    return () => {
      guardRef.current?.destroy();
    };
  }, [options.apiEndpoint, options.siteKey]);

  const init = useCallback(async () => {
    if (!guardRef.current) return;
    
    setError(null);
    try {
      await guardRef.current.init();
      setIsInitialized(true);
    } catch (err) {
      setError(err as PassiveGuardError);
      throw err;
    }
  }, []);

  const verify = useCallback(async () => {
    if (!guardRef.current) {
      throw new PassiveGuardError('SDK not initialized', 'INIT_FAILED');
    }

    setIsLoading(true);
    setError(null);

    try {
      const verificationResult = await guardRef.current.verify();
      setResult(verificationResult);
      return verificationResult;
    } catch (err) {
      setError(err as PassiveGuardError);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getToken = useCallback(async () => {
    const verificationResult = await verify();
    return verificationResult.token;
  }, [verify]);

  const reset = useCallback(() => {
    guardRef.current?.reset();
    setResult(null);
    setChallenge(null);
    setError(null);
  }, []);

  // Respond to challenge
  const respondToChallenge = useCallback((response: any) => {
    if (challengeResolverRef.current) {
      challengeResolverRef.current(response);
      challengeResolverRef.current = null;
    }
  }, []);

  return {
    init,
    verify,
    getToken,
    reset,
    isInitialized,
    isLoading,
    result,
    challenge,
    error,
    isHuman: result?.isHuman ?? false,
    riskScore: result?.riskScore ?? 0,
  };
}

export default usePassiveGuard;
