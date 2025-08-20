import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Building2, MapPin, Star, Clock, Search, Loader2, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useState } from 'react';

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
  // New field to prevent duplicates
  jobHash?: string; // Unique identifier based on title + company + location
}

interface JobCardProps {
  job: Job;
  onPlatformSearch?: (platform: string, jobData: Job) => Promise<any>; // Your scraper callback
}

// Platform configurations - only show button for available platform
const PLATFORM_CONFIG = {
  'indeed': {
    name: 'Indeed',
    color: 'bg-blue-600 hover:bg-blue-700 text-white',
    searchUrl: (job: Job) => {
      const params = new URLSearchParams();
      params.append('q', `${job.title} ${job.company}`.trim());
      if (job.location) params.append('l', job.location);
      return `https://www.indeed.com/jobs?${params.toString()}`;
    }
  },
  'linkedin': {
    name: 'LinkedIn', 
    color: 'bg-blue-700 hover:bg-blue-800 text-white',
    searchUrl: (job: Job) => {
      const params = new URLSearchParams();
      params.append('keywords', `${job.title} ${job.company}`.trim());
      if (job.location) params.append('location', job.location);
      return `https://www.linkedin.com/jobs/search/?${params.toString()}`;
    }
  },
  'glassdoor': {
    name: 'Glassdoor',
    color: 'bg-green-600 hover:bg-green-700 text-white',
    searchUrl: (job: Job) => {
      const params = new URLSearchParams();
      params.append('sc.keyword', `${job.title} ${job.company}`.trim());
      return `https://www.glassdoor.com/Job/jobs.htm?${params.toString()}`;
    }
  },
  'naukri': {
    name: 'Naukri',
    color: 'bg-purple-600 hover:bg-purple-700 text-white',
    searchUrl: (job: Job) => {
      const params = new URLSearchParams();
      params.append('qp', `${job.title} ${job.company}`.trim());
      if (job.location) params.append('qpl', job.location);
      return `https://www.naukri.com/jobs?${params.toString()}`;
    }
  },
  'monster': {
    name: 'Foundit',
    color: 'bg-orange-600 hover:bg-orange-700 text-white',
    searchUrl: (job: Job) => {
      const query = `${job.title} ${job.company}`.trim();
      return `https://www.foundit.in/jobs/${encodeURIComponent(query)}`;
    }
  },
  'dice': {
    name: 'Dice',
    color: 'bg-red-600 hover:bg-red-700 text-white',
    searchUrl: (job: Job) => {
      const params = new URLSearchParams();
      params.append('q', `${job.title} ${job.company}`.trim());
      if (job.location) params.append('location', job.location);
      return `https://www.dice.com/jobs?${params.toString()}`;
    }
  },
  'ziprecruiter': {
    name: 'ZipRecruiter',
    color: 'bg-indigo-600 hover:bg-indigo-700 text-white',
    searchUrl: (job: Job) => {
      const params = new URLSearchParams();
      params.append('search', `${job.title} ${job.company}`.trim());
      if (job.location) params.append('location', job.location);
      return `https://www.ziprecruiter.com/Jobs?${params.toString()}`;
    }
  },
  'himalayas': {
    name: 'Himalayas',
    color: 'bg-teal-600 hover:bg-teal-700 text-white',
    searchUrl: (job: Job) => {
      const query = `${job.title} ${job.company}`.trim();
      return `https://himalayas.app/jobs?q=${encodeURIComponent(query)}`;
    }
  },
  'careerbuilder': {
    name: 'CareerBuilder',
    color: 'bg-cyan-600 hover:bg-cyan-700 text-white',
    searchUrl: (job: Job) => {
      const params = new URLSearchParams();
      params.append('keywords', `${job.title} ${job.company}`.trim());
      if (job.location) params.append('location', job.location);
      return `https://www.careerbuilder.com/jobs?${params.toString()}`;
    }
  }
};

const getMatchColor = (score: number) => {
  if (score >= 80) return 'text-success bg-success/10';
  if (score >= 60) return 'text-warning bg-warning/10';
  return 'text-muted-foreground bg-muted';
};

const getMatchLabel = (score: number) => {
  if (score >= 80) return 'Excellent Match';
  if (score >= 60) return 'Good Match';
  return 'Fair Match';
};

// Function to generate job hash for duplicate detection
export const generateJobHash = (job: Job): string => {
  const normalizedTitle = job.title.toLowerCase().trim();
  const normalizedCompany = job.company.toLowerCase().trim();
  const normalizedLocation = job.location.toLowerCase().trim();
  
  return btoa(`${normalizedTitle}-${normalizedCompany}-${normalizedLocation}`);
};

// Check if URL is problematic
const isProblematicUrl = (url: string): boolean => {
  if (!url || url === '#' || url === '') return true;
  
  const problematicPatterns = [
    /\/job\/1$/,
    /\/job\/2$/,
    /jobs\?.*expired/,
    /viewjob\?jk=$/,
  ];

  return problematicPatterns.some(pattern => pattern.test(url));
};

export const JobCard = ({ job, onPlatformSearch }: JobCardProps) => {
  const [isSearching, setIsSearching] = useState(false);
  const [searchResult, setSearchResult] = useState<{ success: boolean; jobCount?: number; error?: string } | null>(null);

  // Get platform configuration
  const platformKey = job.source.toLowerCase() as keyof typeof PLATFORM_CONFIG;
  const platformConfig = PLATFORM_CONFIG[platformKey];

  // Check if original URL is problematic
  const urlIsProblematic = isProblematicUrl(job.url);

  // Handle the single search button click
  const handleSearchClick = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (!platformConfig) {
      console.error(`Platform configuration not found for: ${job.source}`);
      return;
    }

    setIsSearching(true);
    setSearchResult(null);

    try {
      // Always use platform search (never original URL to avoid bot detection)
      const searchUrl = platformConfig.searchUrl(job);
      
      // Open platform search immediately
      window.open(searchUrl, '_blank', 'noopener,noreferrer');

      // Run backend scraper to get real job count and data
      if (onPlatformSearch) {
        const scraperResult = await onPlatformSearch(platformKey, job);
        
        setSearchResult({
          success: scraperResult.success || true,
          jobCount: scraperResult.jobCount || 0,
          error: scraperResult.error
        });
      } else {
        // Fallback: just mark as successful search
        setSearchResult({
          success: true,
          jobCount: 0
        });
      }

    } catch (error) {
      console.error(`Error searching on ${platformConfig.name}:`, error);
      setSearchResult({
        success: false,
        error: 'Search failed'
      });
    } finally {
      setIsSearching(false);
    }
  };

  // Don't render if no platform configuration exists
  if (!platformConfig) {
    return null;
  }

  return (
    <Card className="group hover:shadow-lg transition-all duration-300">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-lg text-foreground group-hover:text-primary transition-colors line-clamp-2">
              {job.title}
            </h3>
            <div className="flex items-center gap-2 mt-1 text-muted-foreground">
              <Building2 className="w-4 h-4 shrink-0" />
              <span className="font-medium">{job.company}</span>
            </div>
            <div className="flex items-center gap-2 mt-1 text-muted-foreground">
              <MapPin className="w-4 h-4 shrink-0" />
              <span className="text-sm">{job.location}</span>
            </div>
          </div>
          
          <div className="text-right shrink-0">
            <div className={cn(
              "inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium",
              getMatchColor(job.matchScore)
            )}>
              <Star className="w-3 h-3" />
              {job.matchScore}%
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              {getMatchLabel(job.matchScore)}
            </div>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {job.salary && (
          <div className="text-sm">
            <span className="font-medium text-success">{job.salary}</span>
          </div>
        )}
        
        <p className="text-sm text-muted-foreground line-clamp-3">
          {job.description}
        </p>
        
        {job.requirements.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-foreground mb-2">Key Requirements:</h4>
            <div className="flex flex-wrap gap-1">
              {job.requirements.slice(0, 6).map((req, index) => (
                <Badge key={index} variant="outline" className="text-xs">
                  {req}
                </Badge>
              ))}
              {job.requirements.length > 6 && (
                <Badge variant="outline" className="text-xs">
                  +{job.requirements.length - 6} more
                </Badge>
              )}
            </div>
          </div>
        )}

        {/* Search Result Feedback */}
        {searchResult && !isSearching && (
          <div className={cn(
            "flex items-center gap-2 text-xs p-3 rounded-lg",
            searchResult.success 
              ? "text-green-700 bg-green-50 border border-green-200" 
              : "text-red-700 bg-red-50 border border-red-200"
          )}>
            {searchResult.success ? (
              <>
                <span>✓ Search opened on {platformConfig.name}</span>
                {searchResult.jobCount !== undefined && searchResult.jobCount > 0 && (
                  <span className="font-medium">• {searchResult.jobCount} jobs found</span>
                )}
              </>
            ) : (
              <>
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{searchResult.error || 'Search failed'}</span>
              </>
            )}
          </div>
        )}

        {/* Platform availability note */}
        <div className="flex items-center gap-2 text-xs text-muted-foreground bg-muted/30 p-2 rounded">
          <span>Available on:</span>
          <Badge variant="outline" className="text-xs">
            {platformConfig.name}
          </Badge>
        </div>
        
        {/* Single Search Button */}
        <div className="flex items-center justify-between pt-2 border-t">
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <div className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {job.postedDate}
            </div>
            <Badge variant="outline" className="text-xs">
              {job.source}
            </Badge>
          </div>
          
          {/* Single Platform Search Button */}
          <Button 
            size="sm"
            onClick={handleSearchClick}
            disabled={isSearching}
            className={cn(
              "transition-all duration-200 min-w-[140px]",
              platformConfig.color
            )}
          >
            {isSearching ? (
              <>
                <Loader2 className="w-3 h-3 mr-2 animate-spin" />
                Searching...
              </>
            ) : (
              <>
                <Search className="w-3 h-3 mr-2" />
                Search on {platformConfig.name}
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};