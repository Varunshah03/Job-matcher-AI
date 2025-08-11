import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { JobCard, Job } from './JobCard';
import { Briefcase, Filter, Search, SortAsc } from 'lucide-react';

interface JobResultsProps {
  jobs: Job[];
  isLoading?: boolean;
}

const JobResults = ({ jobs, isLoading = false }: JobResultsProps) => {
  const [sortBy, setSortBy] = useState('match');
  const [filterBySource, setFilterBySource] = useState('all');

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="w-5 h-5 text-primary animate-spin" />
            Searching for Jobs...
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse">
                <div className="border rounded-lg p-6 space-y-3">
                  <div className="flex justify-between">
                    <div className="space-y-2">
                      <div className="h-5 bg-muted rounded w-64"></div>
                      <div className="h-4 bg-muted rounded w-48"></div>
                      <div className="h-4 bg-muted rounded w-32"></div>
                    </div>
                    <div className="h-8 bg-muted rounded w-20"></div>
                  </div>
                  <div className="h-4 bg-muted rounded w-full"></div>
                  <div className="h-4 bg-muted rounded w-3/4"></div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (jobs.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Briefcase className="w-5 h-5 text-muted-foreground" />
            No Jobs Found
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Briefcase className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">
              Upload a resume to discover personalized job opportunities.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Filter and sort jobs
  let filteredJobs = jobs;
  
  if (filterBySource !== 'all') {
    filteredJobs = jobs.filter(job => job.source.toLowerCase() === filterBySource.toLowerCase());
  }

  const sortedJobs = [...filteredJobs].sort((a, b) => {
    switch (sortBy) {
      case 'match':
        return b.match_score - a.match_score;
      case 'date':
        // Handle non-date strings like "2 days ago"
        const dateA = a.posted_date.includes('ago') ? new Date() : new Date(a.posted_date);
        const dateB = b.posted_date.includes('ago') ? new Date() : new Date(b.posted_date);
        return dateB.getTime() - dateA.getTime();
      case 'company':
        return a.company.localeCompare(b.company);
      default:
        return b.match_score - a.match_score;
    }
  });

  const averageMatch = Math.round(jobs.reduce((sum, job) => sum + job.match_score, 0) / jobs.length);
  const highMatches = jobs.filter(job => job.match_score >= 80).length;

  return (
    <div className="space-y-6">
      {/* Results Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Briefcase className="w-5 h-5 text-primary" />
            Job Search Results
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-primary/5 rounded-lg">
              <div className="text-2xl font-bold text-primary">{jobs.length}</div>
              <div className="text-sm text-muted-foreground">Total Jobs</div>
            </div>
            <div className="text-center p-4 bg-success/5 rounded-lg">
              <div className="text-2xl font-bold text-success">{highMatches}</div>
              <div className="text-sm text-muted-foreground">High Matches (80%+)</div>
            </div>
            <div className="text-center p-4 bg-warning/5 rounded-lg">
              <div className="text-2xl font-bold text-warning">{averageMatch}%</div>
              <div className="text-sm text-muted-foreground">Average Match</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Filters and Sorting */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-muted-foreground" />
              <Select value={filterBySource} onValueChange={setFilterBySource}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Filter by source" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Sources</SelectItem>
                  <SelectItem value="indeed">Indeed</SelectItem>
                  <SelectItem value="linkedin">LinkedIn</SelectItem>
                  <SelectItem value="glassdoor">Glassdoor</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex items-center gap-2">
              <SortAsc className="w-4 h-4 text-muted-foreground" />
              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="match">Match Score</SelectItem>
                  <SelectItem value="date">Date Posted</SelectItem>
                  <SelectItem value="company">Company</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Job Listings */}
      <div className="grid gap-4">
        {sortedJobs.map((job) => (
          <JobCard key={job.id} job={job} />
        ))}
      </div>
    </div>
  );
};

export default JobResults;
