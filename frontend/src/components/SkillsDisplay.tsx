import { useState, useEffect } from 'react';
import axios from 'axios';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { Brain, Code, Database, Globe, Smartphone, Wrench, Palette } from 'lucide-react';

interface SkillsDisplayProps {
  skills: string[];
  isLoading?: boolean;
  error?: string | null;
}

const getSkillIcon = (skill: string) => {
  const lowerSkill = skill.toLowerCase();
  
  if (['react', 'vue', 'angular', 'javascript', 'typescript', 'html', 'css', 'sass', 'tailwind', 'bootstrap'].includes(lowerSkill)) {
    return <Globe className="w-4 h-4" />;
  }
  if (['python', 'java', 'c++', 'c#', 'go', 'rust', 'php', 'ruby', 'c', 'swift', 'kotlin'].includes(lowerSkill)) {
    return <Code className="w-4 h-4" />;
  }
  if (['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 'oracle', 'elasticsearch'].includes(lowerSkill)) {
    return <Database className="w-4 h-4" />;
  }
  if (['ios', 'android', 'swift', 'kotlin', 'flutter', 'react native', 'ionic', 'xamarin'].includes(lowerSkill)) {
    return <Smartphone className="w-4 h-4" />;
  }
  if (['ai', 'ml', 'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'pandas', 'numpy', 'scikit-learn'].includes(lowerSkill)) {
    return <Brain className="w-4 h-4" />;
  }
  if (['figma', 'spline', 'sketch', 'adobe xd', 'invision', 'ui/ux design', 'wireframing', 'prototyping'].includes(lowerSkill)) {
    return <Palette className="w-4 h-4" />;
  }
  return <Wrench className="w-4 h-4" />;
};

const getSkillVariant = (index: number) => {
  const variants = ['default', 'secondary', 'outline'] as const;
  return variants[index % variants.length];
};

export const SkillsDisplay = ({ skills, isLoading = false, error }: SkillsDisplayProps) => {
  const [newSkill, setNewSkill] = useState('');
  const [localSkills, setLocalSkills] = useState<string[]>([]);
  const [errorMessage, setErrorMessage] = useState('');
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    // Normalize skills: remove duplicates, trim, and preserve original case
    const normalizedSkills = Array.from(new Set(skills.map(skill => skill.trim().toLowerCase())))
      .map(skill => skills.find(s => s.toLowerCase() === skill) || skill)
      .filter(skill => skill); // Remove empty strings
    setLocalSkills(normalizedSkills);
    if (isLoading) {
      const interval = setInterval(() => {
        setProgress((prev) => Math.min(prev + 20, 100));
      }, 1000);
      return () => clearInterval(interval);
    } else {
      setProgress(100);
    }
  }, [skills, isLoading]);

  const handleAddSkill = async () => {
    const trimmedSkill = newSkill.trim();
    if (!trimmedSkill) {
      setErrorMessage('Please enter a valid skill');
      return;
    }
    if (localSkills.some(skill => skill.toLowerCase() === trimmedSkill.toLowerCase())) {
      setErrorMessage('Skill already exists');
      return;
    }

    try {
      await axios.post('/api/add-user-skills', { skills: [trimmedSkill] });
      setLocalSkills([...localSkills, trimmedSkill]);
      setNewSkill('');
      setErrorMessage('');
    } catch (error) {
      setErrorMessage('Failed to add skill. Please try again.');
      console.error('Error adding skill:', error);
    }
  };

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-destructive" />
            Error Extracting Skills
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">{error}</p>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-primary" />
            Extracting Skills... ({progress}%)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Progress value={progress} className="mb-4" />
          <div className="flex flex-wrap gap-2">
            {localSkills.map((skill, index) => (
              <Badge key={skill} variant={getSkillVariant(index)} className="flex items-center gap-1">
                {getSkillIcon(skill)}
                {skill}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (localSkills.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-muted-foreground" />
            No Skills Detected
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Upload a resume to see extracted skills and get personalized job matches.
          </p>
        </CardContent>
      </Card>
    );
  }

  const skillCategories = {
    'Programming': localSkills.filter(skill => 
      ['python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust', 'php', 'ruby', 'c', 'swift', 'kotlin', 'r', 'scala', 'perl'].includes(skill.toLowerCase())
    ),
    'Frontend': localSkills.filter(skill => 
      ['react', 'vue.js', 'angular', 'html', 'css', 'sass', 'less', 'tailwind', 'bootstrap', 'jquery', 'ember.js', 'svelte'].includes(skill.toLowerCase())
    ),
    'Backend': localSkills.filter(skill => 
      ['node.js', 'express', 'django', 'flask', 'spring', 'laravel', 'ruby on rails', 'fastapi', 'asp.net', 'graphql'].includes(skill.toLowerCase())
    ),
    'Database': localSkills.filter(skill => 
      ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 'oracle', 'elasticsearch', 'cassandra', 'dynamodb'].includes(skill.toLowerCase())
    ),
    'Cloud & DevOps': localSkills.filter(skill => 
      ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git', 'github', 'gitlab', 'ansible', 'terraform', 'ci/cd', 'linux', 'bash'].includes(skill.toLowerCase())
    ),
    'UI/UX Design': localSkills.filter(skill => 
      ['figma', 'spline', 'sketch', 'adobe xd', 'invision', 'ui/ux design', 'wireframing', 'prototyping'].includes(skill.toLowerCase())
    ),
    'Data Science': localSkills.filter(skill => 
      ['machine learning', 'deep learning', 'tensorflow', 'pytorch', 'pandas', 'numpy', 'scikit-learn', 'r', 'data analysis', 'data visualization'].includes(skill.toLowerCase())
    ),
    'Marketing': localSkills.filter(skill => 
      ['seo', 'ppc', 'social media marketing', 'content marketing', 'email marketing', 'google analytics', 'google ads', 'marketing automation', 'cro', 'sem'].includes(skill.toLowerCase())
    ),
    'Mobile': localSkills.filter(skill => 
      ['react native', 'flutter', 'swift', 'kotlin', 'ionic', 'xamarin'].includes(skill.toLowerCase())
    ),
    'Finance': localSkills.filter(skill => 
      ['financial analysis', 'risk management', 'investment banking', 'accounting', 'tax planning'].includes(skill.toLowerCase())
    ),
    'Healthcare': localSkills.filter(skill => 
      ['patient care', 'medical coding', 'emr systems', 'clinical research', 'healthcare compliance'].includes(skill.toLowerCase())
    ),
    'Other': localSkills.filter(skill => {
      const categories = [
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust', 'php', 'ruby', 'c', 'swift', 'kotlin', 'r', 'scala', 'perl',
        'react', 'vue.js', 'angular', 'html', 'css', 'sass', 'less', 'tailwind', 'bootstrap', 'jquery', 'ember.js', 'svelte',
        'node.js', 'express', 'django', 'flask', 'spring', 'laravel', 'ruby on rails', 'fastapi', 'asp.net', 'graphql',
        'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 'oracle', 'elasticsearch', 'cassandra', 'dynamodb',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git', 'github', 'gitlab', 'ansible', 'terraform', 'ci/cd', 'linux', 'bash',
        'figma', 'spline', 'sketch', 'adobe xd', 'invision', 'ui/ux design', 'wireframing', 'prototyping',
        'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'pandas', 'numpy', 'scikit-learn', 'r', 'data analysis', 'data visualization',
        'seo', 'ppc', 'social media marketing', 'content marketing', 'email marketing', 'google analytics', 'google ads', 'marketing automation', 'cro', 'sem',
        'react native', 'flutter', 'swift', 'kotlin', 'ionic', 'xamarin',
        'financial analysis', 'risk management', 'investment banking', 'accounting', 'tax planning',
        'patient care', 'medical coding', 'emr systems', 'clinical research', 'healthcare compliance'
      ];
      return !categories.includes(skill.toLowerCase());
    })
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-primary" />
          Extracted Skills ({localSkills.length})
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <h4 className="text-sm font-medium text-muted-foreground mb-2">Add New Skill</h4>
          <div className="flex gap-2">
            <Input
              value={newSkill}
              onChange={(e) => setNewSkill(e.target.value)}
              placeholder="Enter a new skill (e.g., Financial Analysis)"
              className="max-w-md"
            />
            <Button onClick={handleAddSkill}>Add Skill</Button>
          </div>
          {errorMessage && <p className="text-destructive text-sm mt-2">{errorMessage}</p>}
        </div>
        {Object.entries(skillCategories).map(([category, categorySkills]) => {
          if (categorySkills.length === 0) return null;
          
          return (
            <div key={category}>
              <h4 className="text-sm font-medium text-muted-foreground mb-2">{category}</h4>
              <div className="flex flex-wrap gap-2">
                {categorySkills.map((skill, index) => (
                  <Badge 
                    key={skill} 
                    variant={getSkillVariant(index)}
                    className="flex items-center gap-1"
                  >
                    {getSkillIcon(skill)}
                    {skill}
                  </Badge>
                ))}
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
};