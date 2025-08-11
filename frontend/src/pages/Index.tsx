import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileUpload } from '@/components/FileUpload';
import JobResults from '@/components/JobResults';
import { Brain, Sparkles, Zap, Target, Clock } from 'lucide-react';
import { toast } from '@/hooks/use-toast';

interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  description: string;
  requirements: string[];
  skills: string[];
  match_score: number;
  posted_date: string;
  source: string;
  url: string;
  salary?: string;
  jobType?: string;
  experienceLevel?: string;
}

interface JobResponse {
  id: string;
  title: string;
  company: string;
  location: string;
  description: string;
  requirements: string[];
  skills: string[];
  match_score: number;
  posted_date: string;
  source: string;
  url: string;
  salary?: string;
  job_type?: string;
  experience_level?: string;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const Index = () => {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [jobResults, setJobResults] = useState<Job[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const navigate = useNavigate();

  const transformJobResponse = (jobs: JobResponse[]): Job[] => {
    return jobs.map(job => ({
      id: job.id,
      title: job.title,
      company: job.company,
      location: job.location,
      description: job.description,
      requirements: job.requirements,
      skills: job.skills,
      match_score: job.match_score,
      posted_date: job.posted_date,
      source: job.source,
      url: job.url,
      salary: job.salary,
      jobType: job.job_type,
      experienceLevel: job.experience_level,
    }));
  };

  const handleFileUpload = async (file: File | null) => {
    if (!file) {
      setUploadedFile(null);
      setJobResults([]);
      navigate('/', { replace: true });
      return;
    }

    setIsUploading(true);
    setUploadedFile(file);
    setIsUploading(false);
  };

  const handleSkillsExtracted = async (skills: string[]) => {
    if (skills.length === 0) {
      toast({
        title: "No Skills Extracted",
        description: "No valid skills found in your resume.",
        variant: "destructive",
      });
      return;
    }

    toast({
      title: "Skills Extracted Successfully!",
      description: `Found ${skills.length} relevant skills in your resume.`,
    });

    setIsSearching(true);
    try {
      console.log('Sending skills to /api/search-jobs:', skills);
      const response = await fetch(`${API_URL}/api/search-jobs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          skills,
          location: 'Remote',
          max_jobs: 20,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('API Error:', response.status, errorText);
        throw new Error(`Search failed: ${response.statusText}`);
      }

      const data: JobResponse[] = await response.json();
      console.log('API Response:', data);
      const transformedJobs = transformJobResponse(data);
      console.log('Transformed Jobs:', transformedJobs);
      
      if (transformedJobs.length === 0) {
        toast({
          title: "No Jobs Found",
          description: "No matching jobs found for your skills. Try modifying your resume.",
          variant: "destructive",
        });
      } else {
        setJobResults(transformedJobs);
        toast({
          title: "Job Search Complete!",
          description: `Found ${transformedJobs.length} potential job matches.`,
        });
        navigate('/jobmatch');
      }
    } catch (error) {
      console.error('Error in handleSkillsExtracted:', error);
      toast({
        title: "Error Searching Jobs",
        description: "Failed to fetch job listings. Please try again.",
        variant: "destructive",
      });
      setJobResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      {/* Header */}
      <header className="border-b bg-background/80 backdrop-blur-sm sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-primary to-primary-hover rounded-lg flex items-center justify-center">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-foreground">Job Matcher AI</h1>
                <p className="text-sm text-muted-foreground">Find your dream job effortlessly</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      {!uploadedFile && (
        <section className="py-16">
          <div className="container mx-auto px-4 text-center">
            <div className="max-w-4xl mx-auto">
              <div className="inline-flex items-center gap-2 bg-primary/10 text-primary px-4 py-2 rounded-full text-sm font-medium mb-6">
                <Sparkles className="w-4 h-4" />
                AI-Powered Job Matching
              </div>
              <h2 className="text-4xl md:text-6xl font-bold text-foreground mb-6">
                Find Your Perfect Job with{' '}
                <span className="bg-gradient-to-r from-primary to-primary-hover bg-clip-text text-transparent">
                  AI Intelligence
                </span>
              </h2>
              <p className="text-xl text-muted-foreground mb-8 leading-relaxed">
                Upload your resume and let our AI analyze your skills to find the most relevant job opportunities 
                from top platforms like Indeed, LinkedIn, and Glassdoor.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
                <div className="flex flex-col items-center text-center p-6">
                  <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mb-4">
                    <Zap className="w-8 h-8 text-primary" />
                  </div>
                  <h3 className="font-semibold text-lg mb-2">Smart Analysis</h3>
                  <p className="text-muted-foreground">AI extracts skills and experience from your resume automatically</p>
                </div>
                <div className="flex flex-col items-center text-center p-6">
                  <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mb-4">
                    <Target className="w-8 h-8 text-primary" />
                  </div>
                  <h3 className="font-semibold text-lg mb-2">Perfect Matches</h3>
                  <p className="text-muted-foreground">Get jobs ranked by compatibility with your unique skill set</p>
                </div>
                <div className="flex flex-col items-center text-center p-6">
                  <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mb-4">
                    <Clock className="w-8 h-8 text-primary" />
                  </div>
                  <h3 className="font-semibold text-lg mb-2">Save Time</h3>
                  <p className="text-muted-foreground">No more manual searching across multiple job boards</p>
                </div>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Main Content */}
      <main className="container mx-auto px-4 pb-16">
        <div className="max-w-4xl mx-auto space-y-8">
          <FileUpload 
            onFileUpload={handleFileUpload}
            uploadedFile={uploadedFile}
            isUploading={isUploading}
            onSkillsExtracted={handleSkillsExtracted}
          />
          {(jobResults.length > 0 || isSearching) && (
            <JobResults 
              jobs={jobResults}
              isLoading={isSearching}
            />
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t bg-muted/30 py-8">
        <div className="container mx-auto px-4 text-center">
          <p className="text-muted-foreground">
            Powered by AI • Connecting talent with opportunity
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Index;