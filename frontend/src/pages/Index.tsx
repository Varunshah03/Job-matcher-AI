import { useState } from 'react';
import { FileUpload } from '@/components/FileUpload';
import { SkillsDisplay } from '@/components/SkillsDisplay';
import { JobResults } from '@/components/JobResults';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Brain, Briefcase, Sparkles, Zap, Target, Clock } from 'lucide-react';
import { mockJobs, extractSkillsFromResume, calculateJobMatches } from '@/data/mockJobs';
import { Job } from '@/components/JobCard';
import { toast } from '@/hooks/use-toast';

const Index = () => {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [extractedSkills, setExtractedSkills] = useState<string[]>([]);
  const [jobResults, setJobResults] = useState<Job[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isSearching, setIsSearching] = useState(false);

  const handleFileUpload = async (file: File) => {
    if (uploadedFile && file === uploadedFile) {
      // Remove file
      setUploadedFile(null);
      setExtractedSkills([]);
      setJobResults([]);
      return;
    }

    setIsUploading(true);
    setUploadedFile(file);
    
    try {
      // Simulate file processing delay
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      setIsExtracting(true);
      setIsUploading(false);
      
      // Simulate resume text extraction and skill parsing
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const mockResumeText = `
        Software Developer with 5+ years of experience in React, JavaScript, TypeScript, Node.js, 
        Python, AWS, Docker, PostgreSQL, and Git. Experience with HTML, CSS, and modern web development.
        Strong background in full-stack development and cloud technologies.
      `;
      
      const skills = extractSkillsFromResume(mockResumeText);
      setExtractedSkills(skills);
      setIsExtracting(false);
      
      toast({
        title: "Skills Extracted Successfully!",
        description: `Found ${skills.length} relevant skills in your resume.`,
      });
      
      // Start job matching
      setIsSearching(true);
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      const matchedJobs = calculateJobMatches(skills, mockJobs);
      setJobResults(matchedJobs);
      setIsSearching(false);
      
      toast({
        title: "Job Matching Complete!",
        description: `Found ${matchedJobs.length} potential job matches.`,
      });
      
    } catch (error) {
      toast({
        title: "Error Processing Resume",
        description: "Please try uploading your resume again.",
        variant: "destructive",
      });
      setIsUploading(false);
      setIsExtracting(false);
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
          {/* File Upload */}
          <FileUpload 
            onFileUpload={handleFileUpload}
            uploadedFile={uploadedFile}
            isUploading={isUploading}
          />

          {/* Skills Display */}
          {(uploadedFile || extractedSkills.length > 0) && (
            <SkillsDisplay 
              skills={extractedSkills}
              isLoading={isExtracting}
            />
          )}

          {/* Job Results */}
          {(extractedSkills.length > 0 || isSearching) && (
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
