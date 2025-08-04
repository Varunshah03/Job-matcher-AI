import { useState, useCallback } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Upload, File, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface FileUploadProps {
  onFileUpload: (file: File) => void;
  uploadedFile: File | null;
  isUploading: boolean;
}

export const FileUpload = ({ onFileUpload, uploadedFile, isUploading }: FileUploadProps) => {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    const validFile = files.find(file => 
      file.type === 'application/pdf' || 
      file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    );
    
    if (validFile) {
      onFileUpload(validFile);
    }
  }, [onFileUpload]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onFileUpload(file);
    }
  }, [onFileUpload]);

  return (
    <Card className={cn(
      "border-2 border-dashed transition-all duration-300",
      isDragOver ? "border-primary bg-primary/5" : "border-border",
      uploadedFile ? "border-success bg-success/5" : ""
    )}>
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
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => onFileUpload(uploadedFile)}
              disabled={isUploading}
            >
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
            <h3 className="text-lg font-semibold text-foreground mb-2">
              Upload Your Resume
            </h3>
            <p className="text-muted-foreground mb-6">
              Drag and drop your resume here, or click to browse
            </p>
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
                <Button 
                  variant="gradient" 
                  size="lg" 
                  asChild
                  disabled={isUploading}
                >
                  <span>
                    <Upload className="w-4 h-4 mr-2" />
                    {isUploading ? 'Uploading...' : 'Select Resume'}
                  </span>
                </Button>
              </label>
              <p className="text-sm text-muted-foreground">
                Supported formats: PDF, DOCX (Max 10MB)
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};