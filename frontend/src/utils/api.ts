/**
 * API Client for PassiveGuard Backend
 */

import { VerificationRequest, VerificationResult, PassiveGuardError } from '../types';

export interface ApiClientConfig {
  endpoint: string;
  timeout?: number;
  retries?: number;
}

export class ApiClient {
  private endpoint: string;
  private timeout: number;
  private retries: number;

  constructor(config: ApiClientConfig) {
    this.endpoint = config.endpoint.replace(/\/$/, ''); // Remove trailing slash
    this.timeout = config.timeout || 10000;
    this.retries = config.retries || 2;
  }

  /**
   * Send verification request to backend
   */
  async verify(request: VerificationRequest): Promise<VerificationResult> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= this.retries; attempt++) {
      try {
        const response = await this.fetchWithTimeout(
          `${this.endpoint}/api/v1/verify`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(request),
          }
        );

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new PassiveGuardError(
            errorData.message || `HTTP ${response.status}`,
            'NETWORK_ERROR',
            errorData
          );
        }

        const result: VerificationResult = await response.json();
        return result;
      } catch (error) {
        lastError = error as Error;
        
        // Don't retry on non-network errors
        if (error instanceof PassiveGuardError) {
          throw error;
        }

        // Wait before retry
        if (attempt < this.retries) {
          await this.delay(Math.pow(2, attempt) * 1000);
        }
      }
    }

    throw new PassiveGuardError(
      lastError?.message || 'Network request failed',
      'NETWORK_ERROR'
    );
  }

  /**
   * Validate token on backend
   */
  async validateToken(token: string, siteKey: string): Promise<boolean> {
    try {
      const response = await this.fetchWithTimeout(
        `${this.endpoint}/api/v1/validate`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ token, siteKey }),
        }
      );

      if (!response.ok) {
        return false;
      }

      const result = await response.json();
      return result.valid === true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Fetch with timeout
   */
  private async fetchWithTimeout(
    url: string,
    options: RequestInit
  ): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });
      return response;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  /**
   * Delay helper
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

export const createApiClient = (config: ApiClientConfig) => {
  return new ApiClient(config);
};
