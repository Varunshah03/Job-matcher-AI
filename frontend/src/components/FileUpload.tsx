import { useState, useCallback } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Upload, File, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { SkillsDisplay } from './SkillsDisplay';

export interface FileUploadProps {
  onFileUpload: (file: File | null) => Promise<void>;
  uploadedFile: File | null;
  isUploading: boolean;
  onSkillsExtracted?: (skills: string[]) => Promise<void>;
}

interface UploadResponse {
  success: boolean;
  message: string;
  filename: string;
  extracted_text: string;
  skills: string[];
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const FileUpload = ({ onFileUpload, uploadedFile, isUploading }: FileUploadProps) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [skills, setSkills] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      setError(null);

      const files = Array.from(e.dataTransfer.files);
      const validFile = files.find(
        (file) =>
          file.type === 'application/pdf' ||
          file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      );

      if (validFile) {
        await handleUpload(validFile);
      } else {
        setError('Please upload a valid PDF or DOCX file.');
      }
    },
    []
  );

  const handleFileInput = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        await handleUpload(file);
      }
    },
    []
  );

  const handleUpload = async (file: File) => {
    setError(null);
    onFileUpload(file);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_URL}/api/upload-resume`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const data: UploadResponse = await response.json();
      if (data.success && Array.isArray(data.skills) && data.skills.every(skill => typeof skill === 'string' && skill.trim())) {
        setSkills(data.skills);
      } else {
        setError(data.message || 'No valid skills extracted from resume.');
      }
    } catch (err) {
      console.error('Upload error:', err);
      setError('Failed to upload resume. Please try again.');
    }
  };

  const handleRemoveFile = () => {
    onFileUpload(null);
    setSkills([]);
    setError(null);
  };

  return (
    <div className="space-y-6">
      <Card
        className={cn(
          'border-2 border-dashed transition-all duration-300',
          isDragOver ? 'border-primary bg-primary/5' : 'border-border',
          uploadedFile ? 'border-success bg-success/5' : ''
        )}
      >
        <CardContent className="p-8">
          {uploadedFile ? (
            <div className="text-center">
              <div className="flex items-center justify-center w-16 h-16 mx-auto mb-4 bg-success/10 rounded-full">
                <File className="w-8 h-8 text-success" />
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">
                Resume Uploaded Successfully
              </h3>
              <p className="text-muted-foreground mb-4">
                {uploadedFile.name} ({(uploadedFile.size / 1024 / 1024).toFixed(2)} MB)
              </p>
              <Button variant="outline" size="sm" onClick={handleRemoveFile} disabled={isUploading}>
                <X className="w-4 h-4 mr-2" />
                Remove File
              </Button>
            </div>
          ) : (
            <div
              className="text-center"
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <div className="flex items-center justify-center w-16 h-16 mx-auto mb-4 bg-primary/10 rounded-full">
                <Upload className="w-8 h-8 text-primary" />
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">Upload Your Resume</h3>
              <p className="text-muted-foreground mb-6">Drag and drop your resume here, or click to browse</p>
              <div className="space-y-4">
                <input
                  type="file"
                  accept=".pdf,.docx"
                  onChange={handleFileInput}
                  className="hidden"
                  id="resume-upload"
                  disabled={isUploading}
                />
                <label htmlFor="resume-upload">
                  <Button variant="gradient" size="lg" asChild disabled={isUploading}>
                    <span>
                      <Upload className="w-4 h-4 mr-2" />
                      {isUploading ? 'Uploading...' : 'Select Resume'}
                    </span>
                  </Button>
                </label>
                <p className="text-sm text-muted-foreground">Supported formats: PDF, DOCX (Max 10MB)</p>
              </div>
            </div>
          )}
          {error && (
            <p className="text-destructive mt-4 text-center">
              {error}
            </p>
          )}
        </CardContent>
      </Card>
      {skills.length > 0 && (
        <SkillsDisplay skills={skills} isLoading={isUploading} error={error} />
      )}
    </div>
  );
};