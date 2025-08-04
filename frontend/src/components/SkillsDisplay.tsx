import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Brain, Code, Database, Globe, Smartphone, Wrench } from 'lucide-react';

interface SkillsDisplayProps {
  skills: string[];
  isLoading?: boolean;
}

const getSkillIcon = (skill: string) => {
  const lowerSkill = skill.toLowerCase();
  
  if (['react', 'vue', 'angular', 'javascript', 'typescript', 'html', 'css'].includes(lowerSkill)) {
    return <Globe className="w-4 h-4" />;
  }
  if (['python', 'java', 'c++', 'c#', 'go', 'rust', 'php'].includes(lowerSkill)) {
    return <Code className="w-4 h-4" />;
  }
  if (['sql', 'mysql', 'postgresql', 'mongodb', 'redis'].includes(lowerSkill)) {
    return <Database className="w-4 h-4" />;
  }
  if (['ios', 'android', 'swift', 'kotlin', 'flutter', 'react native'].includes(lowerSkill)) {
    return <Smartphone className="w-4 h-4" />;
  }
  if (['ai', 'ml', 'machine learning', 'artificial intelligence', 'deep learning'].includes(lowerSkill)) {
    return <Brain className="w-4 h-4" />;
  }
  return <Wrench className="w-4 h-4" />;
};

const getSkillVariant = (index: number) => {
  const variants = ['default', 'secondary', 'outline'] as const;
  return variants[index % variants.length];
};

export const SkillsDisplay = ({ skills, isLoading = false }: SkillsDisplayProps) => {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-primary" />
            Extracting Skills...
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse">
                <div className="h-4 bg-muted rounded w-3/4 mb-2"></div>
                <div className="flex gap-2">
                  {[1, 2, 3, 4].map((j) => (
                    <div key={j} className="h-6 bg-muted rounded w-16"></div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (skills.length === 0) {
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

  // Group skills by category for better display
  const skillCategories = {
    'Programming': skills.filter(skill => 
      ['python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust', 'php', 'ruby'].includes(skill.toLowerCase())
    ),
    'Frontend': skills.filter(skill => 
      ['react', 'vue', 'angular', 'html', 'css', 'sass', 'tailwind'].includes(skill.toLowerCase())
    ),
    'Backend': skills.filter(skill => 
      ['node.js', 'express', 'django', 'flask', 'spring', 'laravel'].includes(skill.toLowerCase())
    ),
    'Database': skills.filter(skill => 
      ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch'].includes(skill.toLowerCase())
    ),
    'Cloud & DevOps': skills.filter(skill => 
      ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git'].includes(skill.toLowerCase())
    ),
    'Other': skills.filter(skill => {
      const categories = ['python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust', 'php', 'ruby',
                         'react', 'vue', 'angular', 'html', 'css', 'sass', 'tailwind',
                         'node.js', 'express', 'django', 'flask', 'spring', 'laravel',
                         'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
                         'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git'];
      return !categories.includes(skill.toLowerCase());
    })
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-primary" />
          Extracted Skills ({skills.length})
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
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