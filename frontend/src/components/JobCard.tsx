import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Building2, MapPin, ExternalLink, Star, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  description: string;
  requirements: string[];
  matchScore: number;
  postedDate: string;
  source: 'Indeed' | 'LinkedIn' | 'Glassdoor';
  url: string;
  salary?: string;
}

interface JobCardProps {
  job: Job;
}

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

export const JobCard = ({ job }: JobCardProps) => {
  return (
    <Card className="group hover:shadow-lg transition-all duration-300 cursor-pointer">
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
          
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => window.open(job.url, '_blank')}
            className="group-hover:bg-primary group-hover:text-primary-foreground transition-colors"
          >
            <ExternalLink className="w-3 h-3 mr-1" />
            Apply
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};