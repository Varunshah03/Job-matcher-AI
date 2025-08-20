// src/services/scraperIntegrationService.ts
import {ReactDOM, useState } from "react"

export interface ScraperJobRequest {
  title: string;
  company: string;
  location?: string;
  skills?: string[];
  platform: string;
  userId?: string;
}

export interface ScraperJobResponse {
  platform: string;
  jobs: ScrapedJob[];
  totalFound: number;
  searchTime: number;
  success: boolean;
  error?: string;
}

export interface ScrapedJob {
  id: string;
  title: string;
  company: string;
  location: string;
  url: string;
  description: string;
  salary?: string;
  postedDate: string;
  requirements: string[];
  platform: string;
}

export class ScraperIntegrationService {
  private static readonly API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  
  // Platform-specific scraper endpoints
  private static readonly SCRAPER_ENDPOINTS = {
    linkedin: '/api/scrapers/linkedin/search',
    indeed: '/api/scrapers/indeed/search',
    glassdoor: '/api/scrapers/glassdoor/search',
    naukri: '/api/scrapers/naukri/search',
    foundit: '/api/scrapers/foundit/search',
    dice: '/api/scrapers/dice/search',
    ziprecruiter: '/api/scrapers/ziprecruiter/search',
    himalayas: '/api/scrapers/himalayas/search',
    careerbuilder: '/api/scrapers/careerbuilder/search'
  };

  /**
   * Search for jobs on a specific platform using your scrapers
   */
  static async searchJobsOnPlatform(
    platform: string, 
    jobRequest: ScraperJobRequest
  ): Promise<ScraperJobResponse> {
    try {
      const endpoint = this.SCRAPER_ENDPOINTS[platform as keyof typeof this.SCRAPER_ENDPOINTS];
      
      if (!endpoint) {
        throw new Error(`Scraper not available for platform: ${platform}`);
      }

      const response = await fetch(`${this.API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.getAuthToken()}`, // Your auth token
        },
        body: JSON.stringify({
          ...jobRequest,
          platform,
          timestamp: new Date().toISOString()
        })
      });

      if (!response.ok) {
        throw new Error(`Scraper API error: ${response.status}`);
      }

      const data = await response.json();
      return data;

    } catch (error) {
      console.error(`Error scraping ${platform}:`, error);
      return {
        platform,
        jobs: [],
        totalFound: 0,
        searchTime: 0,
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Search across multiple platforms simultaneously
   */
  static async searchJobsOnMultiplePlatforms(
    platforms: string[],
    jobRequest: ScraperJobRequest
  ): Promise<ScraperJobResponse[]> {
    const promises = platforms.map(platform => 
      this.searchJobsOnPlatform(platform, jobRequest)
    );

    try {
      const results = await Promise.allSettled(promises);
      
      return results.map((result, index) => {
        if (result.status === 'fulfilled') {
          return result.value;
        } else {
          return {
            platform: platforms[index],
            jobs: [],
            totalFound: 0,
            searchTime: 0,
            success: false,
            error: result.reason?.message || 'Search failed'
          };
        }
      });
    } catch (error) {
      console.error('Error in multi-platform search:', error);
      return platforms.map(platform => ({
        platform,
        jobs: [],
        totalFound: 0,
        searchTime: 0,
        success: false,
        error: 'Multi-platform search failed'
      }));
    }
  }

  /**
   * Get real-time job availability across platforms
   */
  static async checkJobAvailability(
    title: string,
    company: string,
    platforms: string[]
  ): Promise<Record<string, number>> {
    const jobRequest: ScraperJobRequest = {
      title,
      company,
      platform: 'multi'
    };

    const results = await this.searchJobsOnMultiplePlatforms(platforms, jobRequest);
    
    const availability: Record<string, number> = {};
    results.forEach(result => {
      availability[result.platform] = result.totalFound;
    });

    return availability;
  }

  /**
   * Your scraper status monitoring
   */
  static async getScraperStatus(): Promise<Record<string, boolean>> {
    try {
      const response = await fetch(`${this.API_BASE_URL}/api/scrapers/status`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${this.getAuthToken()}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to get scraper status');
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting scraper status:', error);
      return {};
    }
  }

  /**
   * Analytics for your scrapers
   */
  static async getScraperAnalytics(timeframe: 'day' | 'week' | 'month' = 'day') {
    try {
      const response = await fetch(`${this.API_BASE_URL}/api/scrapers/analytics?timeframe=${timeframe}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${this.getAuthToken()}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to get scraper analytics');
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting scraper analytics:', error);
      return null;
    }
  }

  // Helper method to get auth token
  private static getAuthToken(): string {
    // Replace with your actual token retrieval logic
    return localStorage.getItem('authToken') || '';
  }

  /**
   * Queue job search for background processing
   */
  static async queueJobSearch(
    jobRequest: ScraperJobRequest,
    platforms: string[],
    priority: 'low' | 'normal' | 'high' = 'normal'
  ): Promise<string> {
    try {
      const response = await fetch(`${this.API_BASE_URL}/api/scrapers/queue`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.getAuthToken()}`
        },
        body: JSON.stringify({
          jobRequest,
          platforms,
          priority,
          queuedAt: new Date().toISOString()
        })
      });

      if (!response.ok) {
        throw new Error('Failed to queue job search');
      }

      const data = await response.json();
      return data.queueId;
    } catch (error) {
      console.error('Error queuing job search:', error);
      throw error;
    }
  }

  /**
   * Get queued search results
   */
  static async getQueuedResults(queueId: string): Promise<ScraperJobResponse[]> {
    try {
      const response = await fetch(`${this.API_BASE_URL}/api/scrapers/queue/${queueId}/results`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${this.getAuthToken()}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to get queued results');
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting queued results:', error);
      return [];
    }
  }
}

// React Hook for easy use in components
export const useScraperIntegration = () => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<ScraperJobResponse[]>([]);
  const [error, setError] = useState<string | null>(null);

  const searchOnPlatform = async (platform: string, jobRequest: ScraperJobRequest) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await ScraperIntegrationService.searchJobsOnPlatform(platform, jobRequest);
      setResults([result]);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
      return null;
    } finally {
      setLoading(false);
    }
  };

  const searchOnMultiplePlatforms = async (platforms: string[], jobRequest: ScraperJobRequest) => {
    setLoading(true);
    setError(null);
    
    try {
      const results = await ScraperIntegrationService.searchJobsOnMultiplePlatforms(platforms, jobRequest);
      setResults(results);
      return results;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Multi-platform search failed');
      return [];
    } finally {
      setLoading(false);
    }
  };

  return {
    loading,
    results,
    error,
    searchOnPlatform,
    searchOnMultiplePlatforms,
    clearResults: () => setResults([]),
    clearError: () => setError(null)
  };
};

// Example of how to integrate with your backend scrapers
export const SCRAPER_CONFIG = {
  // Your FastAPI backend endpoints
  linkedin: {
    endpoint: '/api/scrapers/linkedin',
    rateLimit: '100/hour',
    authentication: 'required'
  },
  indeed: {
    endpoint: '/api/scrapers/indeed',
    rateLimit: '200/hour',
    authentication: 'optional'
  },
  glassdoor: {
    endpoint: '/api/scrapers/glassdoor',
    rateLimit: '150/hour',
    authentication: 'required'
  },
  naukri: {
    endpoint: '/api/scrapers/naukri',
    rateLimit: '100/hour',
    authentication: 'required'
  },
  foundit: {
    endpoint: '/api/scrapers/foundit',
    rateLimit: '120/hour',
    authentication: 'optional'
  },
  dice: {
    endpoint: '/api/scrapers/dice',
    rateLimit: '80/hour',
    authentication: 'required'
  },
  ziprecruiter: {
    endpoint: '/api/scrapers/ziprecruiter',
    rateLimit: '100/hour',
    authentication: 'required'
  },
  himalayas: {
    endpoint: '/api/scrapers/himalayas',
    rateLimit: '200/hour',
    authentication: 'optional'
  },
  careerbuilder: {
    endpoint: '/api/scrapers/careerbuilder',
    rateLimit: '100/hour',
    authentication: 'required'
  }
};