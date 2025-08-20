// src/utils/jobUrlService.ts
export interface JobSearchOptions {
  title: string;
  company: string;
  location?: string;
}

export class JobUrlService {
  // Check if a URL is likely to be expired or invalid
  static isProblematicUrl(url: string): boolean {
    if (!url || url === '#' || url === '') return true;
    
    const problematicPatterns = [
      /indeed\.com\/job\/1$/,
      /linkedin\.com\/job\/2$/,
      /jobs\?.*expired/,
      /viewjob\?jk=$/,
      // Add patterns from your original errors
      /indeed\.com\/job\/[\w-]+$/,
      /linkedin\.com\/jobs\/view\/\d+$/
    ];

    return problematicPatterns.some(pattern => pattern.test(url));
  }

  // Simple URL validation without CORS issues
  static async validateJobUrl(url: string): Promise<{ isValid: boolean; error?: string }> {
    try {
      // Basic URL format validation only (avoid CORS issues)
      const urlObj = new URL(url);
      
      // Check for obviously invalid domains
      const invalidDomains = ['localhost', '127.0.0.1', 'example.com'];
      if (invalidDomains.some(domain => urlObj.hostname.includes(domain))) {
        return { isValid: false, error: 'Invalid domain' };
      }

      // For now, just validate format - avoid fetch to prevent CORS
      return { isValid: true };

    } catch (error) {
      return { isValid: false, error: 'Invalid URL format' };
    }
  }

  // Generate alternative search URLs
  static getAlternativeSearchUrls(options: JobSearchOptions) {
    const { title, company, location } = options;
    
    return {
      google: this.generateGoogleJobSearch(title, company, location),
      indeed: this.generateIndeedSearch(title, company, location),
      linkedin: this.generateLinkedInSearch(title, company, location),
      glassdoor: this.generateGlassdoorSearch(title, company, location),
      companyWebsite: this.generateCompanyWebsiteSearch(title, company),
    };
  }

  // Google job search
  private static generateGoogleJobSearch(title: string, company: string, location?: string): string {
    const query = [
      `"${title}"`,
      company ? `"${company}"` : '',
      location ? `"${location}"` : '',
      'jobs',
      'career'
    ].filter(Boolean).join(' ');

    return `https://www.google.com/search?q=${encodeURIComponent(query)}&ibp=htl;jobs`;
  }

  // Indeed search
  private static generateIndeedSearch(title: string, company: string, location?: string): string {
    const params = new URLSearchParams();
    params.append('q', `${title} ${company}`.trim());
    if (location) params.append('l', location);
    
    return `https://www.indeed.com/jobs?${params.toString()}`;
  }

  // LinkedIn search
  private static generateLinkedInSearch(title: string, company: string, location?: string): string {
    const keywords = `${title} ${company}`.trim();
    const params = new URLSearchParams();
    params.append('keywords', keywords);
    if (location) params.append('location', location);
    
    return `https://www.linkedin.com/jobs/search/?${params.toString()}`;
  }

  // Glassdoor search
  private static generateGlassdoorSearch(title: string, company: string, location?: string): string {
    const params = new URLSearchParams();
    params.append('sc.keyword', `${title} ${company}`.trim());
    
    return `https://www.glassdoor.com/Job/jobs.htm?${params.toString()}`;
  }

  // Company website search
  private static generateCompanyWebsiteSearch(title: string, company: string): string {
    const cleanCompany = company.toLowerCase()
      .replace(/[^a-z0-9\s]/g, '')
      .replace(/\s+/g, '');
    
    const query = `site:${cleanCompany}.com "${title}" jobs career`;
    
    return `https://www.google.com/search?q=${encodeURIComponent(query)}`;
  }

  // Open URL safely with fallback
  static async openJobUrlSafely(url: string, fallbackOptions: JobSearchOptions): Promise<void> {
    try {
      // Check if URL is problematic
      if (this.isProblematicUrl(url)) {
        console.warn('Problematic URL detected, using fallback search');
        this.openFallbackSearch(fallbackOptions);
        return;
      }

      // Try to open the original URL
      window.open(url, '_blank', 'noopener,noreferrer');
      
    } catch (error) {
      console.error('Error opening job URL:', error);
      this.openFallbackSearch(fallbackOptions);
    }
  }

  // Open fallback search when original URL fails
  private static openFallbackSearch(options: JobSearchOptions): void {
    const alternatives = this.getAlternativeSearchUrls(options);
    
    // Show user a choice or automatically open Google search
    const userChoice = confirm(
      `The job link appears to be expired or unavailable. Would you like to search for "${options.title}" at ${options.company} instead?`
    );

    if (userChoice) {
      window.open(alternatives.google, '_blank', 'noopener,noreferrer');
    }
  }

  // Get multiple search options for user to choose from
  static getSearchOptions(options: JobSearchOptions) {
    const alternatives = this.getAlternativeSearchUrls(options);
    
    return [
      { name: 'Google Jobs', url: alternatives.google, icon: 'Search' },
      { name: 'Indeed', url: alternatives.indeed, icon: 'ExternalLink' },
      { name: 'LinkedIn', url: alternatives.linkedin, icon: 'ExternalLink' },
      { name: 'Glassdoor', url: alternatives.glassdoor, icon: 'ExternalLink' },
      { name: 'Company Website', url: alternatives.companyWebsite, icon: 'Building2' },
    ];
  }
}