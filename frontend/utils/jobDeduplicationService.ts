// src/utils/jobDeduplicationService.ts
export interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  description: string;
  requirements: string[];
  matchScore: number;
  postedDate: string;
  source: 'Indeed' | 'LinkedIn' | 'Glassdoor' | 'Naukri' | 'Monster' | 'Dice' | 'Ziprecruiter' | 'Himalayas' | 'Careerbuilder';
  url: string;
  salary?: string;
  jobHash?: string;
}

export class JobDeduplicationService {
  
  /**
   * Generate a unique hash for a job based on title, company, and location
   */
  static generateJobHash(job: Job): string {
    // Normalize strings for comparison
    const normalizedTitle = this.normalizeString(job.title);
    const normalizedCompany = this.normalizeString(job.company);
    const normalizedLocation = this.normalizeString(job.location);
    
    // Create hash from normalized data
    const hashString = `${normalizedTitle}-${normalizedCompany}-${normalizedLocation}`;
    return btoa(hashString).replace(/[^a-zA-Z0-9]/g, '');
  }

  /**
   * Normalize string for comparison (remove special chars, lowercase, trim)
   */
  private static normalizeString(str: string): string {
    return str
      .toLowerCase()
      .trim()
      .replace(/[^\w\s]/g, '') // Remove special characters
      .replace(/\s+/g, ' ')    // Replace multiple spaces with single space
      .replace(/\b(inc|llc|ltd|corp|corporation|company|co)\b/g, '') // Remove company suffixes
      .trim();
  }

  /**
   * Check if two jobs are duplicates based on similarity
   */
  static areJobsDuplicate(job1: Job, job2: Job, threshold: number = 0.8): boolean {
    // Quick hash comparison first
    const hash1 = this.generateJobHash(job1);
    const hash2 = this.generateJobHash(job2);
    
    if (hash1 === hash2) {
      return true;
    }

    // More detailed similarity check
    const titleSimilarity = this.calculateSimilarity(job1.title, job2.title);
    const companySimilarity = this.calculateSimilarity(job1.company, job2.company);
    const locationSimilarity = this.calculateSimilarity(job1.location, job2.location);

    // Jobs are duplicates if title and company are very similar, and location is similar
    return (
      titleSimilarity >= threshold &&
      companySimilarity >= threshold &&
      locationSimilarity >= 0.6 // More lenient for location
    );
  }

  /**
   * Calculate string similarity using Levenshtein distance
   */
  private static calculateSimilarity(str1: string, str2: string): number {
    const normalized1 = this.normalizeString(str1);
    const normalized2 = this.normalizeString(str2);

    if (normalized1 === normalized2) return 1;
    if (normalized1.length === 0 || normalized2.length === 0) return 0;

    const distance = this.levenshteinDistance(normalized1, normalized2);
    const maxLength = Math.max(normalized1.length, normalized2.length);
    
    return 1 - (distance / maxLength);
  }

  /**
   * Calculate Levenshtein distance between two strings
   */
  private static levenshteinDistance(str1: string, str2: string): number {
    const matrix = Array(str2.length + 1).fill(null).map(() => Array(str1.length + 1).fill(null));

    for (let i = 0; i <= str1.length; i++) matrix[0][i] = i;
    for (let j = 0; j <= str2.length; j++) matrix[j][0] = j;

    for (let j = 1; j <= str2.length; j++) {
      for (let i = 1; i <= str1.length; i++) {
        const cost = str1[i - 1] === str2[j - 1] ? 0 : 1;
        matrix[j][i] = Math.min(
          matrix[j][i - 1] + 1,     // insertion
          matrix[j - 1][i] + 1,     // deletion
          matrix[j - 1][i - 1] + cost // substitution
        );
      }
    }

    return matrix[str2.length][str1.length];
  }

  /**
   * Remove duplicate jobs from an array, keeping the best match score
   */
  static removeDuplicates(jobs: Job[]): Job[] {
    const uniqueJobs: Job[] = [];
    const seenHashes = new Set<string>();

    // First pass: group by exact hash
    const jobGroups = new Map<string, Job[]>();
    
    jobs.forEach(job => {
      const hash = this.generateJobHash(job);
      job.jobHash = hash;
      
      if (!jobGroups.has(hash)) {
        jobGroups.set(hash, []);
      }
      jobGroups.get(hash)!.push(job);
    });

    // Second pass: for each group, keep the job with highest match score
    jobGroups.forEach((groupJobs, hash) => {
      if (groupJobs.length === 1) {
        uniqueJobs.push(groupJobs[0]);
      } else {
        // Multiple jobs with same hash - keep the one with highest match score
        const bestJob = groupJobs.reduce((best, current) => 
          current.matchScore > best.matchScore ? current : best
        );
        
        // Add platform availability info
        const platforms = [...new Set(groupJobs.map(job => job.source))];
        bestJob.availablePlatforms = platforms;
        
        uniqueJobs.push(bestJob);
      }
    });

    // Third pass: check for similar jobs that might have different hashes
    const finalUniqueJobs: Job[] = [];
    
    uniqueJobs.forEach(job => {
      const isDuplicate = finalUniqueJobs.some(existingJob => 
        this.areJobsDuplicate(job, existingJob, 0.85)
      );
      
      if (!isDuplicate) {
        finalUniqueJobs.push(job);
      }
    });

    return finalUniqueJobs;
  }

  /**
   * Find potential duplicates in a job array
   */
  static findDuplicates(jobs: Job[]): { original: Job; duplicates: Job[] }[] {
    const duplicateGroups: { original: Job; duplicates: Job[] }[] = [];
    const processed = new Set<string>();

    jobs.forEach((job, index) => {
      if (processed.has(job.id)) return;

      const duplicates = jobs
        .slice(index + 1)
        .filter(otherJob => 
          !processed.has(otherJob.id) && 
          this.areJobsDuplicate(job, otherJob)
        );

      if (duplicates.length > 0) {
        duplicateGroups.push({
          original: job,
          duplicates
        });

        // Mark all as processed
        processed.add(job.id);
        duplicates.forEach(dup => processed.add(dup.id));
      }
    });

    return duplicateGroups;
  }

  /**
   * Merge duplicate jobs, combining their information
   */
  static mergeDuplicateJobs(jobs: Job[]): Job[] {
    const mergedJobs: Job[] = [];
    const duplicateGroups = this.findDuplicates(jobs);
    const processedIds = new Set<string>();

    // Process duplicate groups
    duplicateGroups.forEach(group => {
      const allJobs = [group.original, ...group.duplicates];
      
      // Keep the job with the highest match score as base
      const bestJob = allJobs.reduce((best, current) => 
        current.matchScore > best.matchScore ? current : best
      );

      // Combine information from all duplicates
      const mergedJob: Job = {
        ...bestJob,
        // Combine platforms where job is available
        availablePlatforms: [...new Set(allJobs.map(job => job.source))],
        // Use the most recent posting date
        postedDate: allJobs
          .map(job => new Date(job.postedDate))
          .sort((a, b) => b.getTime() - a.getTime())[0]
          .toISOString().split('T')[0],
        // Combine requirements
        requirements: [...new Set(allJobs.flatMap(job => job.requirements))],
        // Use best salary if available
        salary: allJobs.find(job => job.salary)?.salary || bestJob.salary
      };

      mergedJobs.push(mergedJob);
      
      // Mark all jobs in this group as processed
      allJobs.forEach(job => processedIds.add(job.id));
    });

    // Add non-duplicate jobs
    jobs.forEach(job => {
      if (!processedIds.has(job.id)) {
        mergedJobs.push(job);
      }
    });

    return mergedJobs;
  }

  /**
   * Get deduplication statistics
   */
  static getDeduplicationStats(originalJobs: Job[], deduplicatedJobs: Job[]) {
    const duplicatesRemoved = originalJobs.length - deduplicatedJobs.length;
    const duplicateGroups = this.findDuplicates(originalJobs);
    
    return {
      originalCount: originalJobs.length,
      uniqueCount: deduplicatedJobs.length,
      duplicatesRemoved,
      duplicateGroups: duplicateGroups.length,
      deduplicationRate: (duplicatesRemoved / originalJobs.length) * 100
    };
  }
}

// React Hook for easy use in components
export const useJobDeduplication = () => {
  const removeDuplicates = (jobs: Job[]) => {
    return JobDeduplicationService.removeDuplicates(jobs);
  };

  const mergeDuplicates = (jobs: Job[]) => {
    return JobDeduplicationService.mergeDuplicateJobs(jobs);
  };

  const findDuplicates = (jobs: Job[]) => {
    return JobDeduplicationService.findDuplicates(jobs);
  };

  const getStats = (originalJobs: Job[], deduplicatedJobs: Job[]) => {
    return JobDeduplicationService.getDeduplicationStats(originalJobs, deduplicatedJobs);
  };

  return {
    removeDuplicates,
    mergeDuplicates,
    findDuplicates,
    getStats
  };
};

// Usage example for your JobResults component:
/*
import { useJobDeduplication } from '@/utils/jobDeduplicationService';

const JobResults = ({ jobs }) => {
  const { removeDuplicates, getStats } = useJobDeduplication();
  
  const uniqueJobs = removeDuplicates(jobs);
  const stats = getStats(jobs, uniqueJobs);
  
  console.log(`Removed ${stats.duplicatesRemoved} duplicates`);
  
  return (
    <div>
      {uniqueJobs.map(job => (
        <JobCard key={job.id} job={job} />
      ))}
    </div>
  );
};
*/