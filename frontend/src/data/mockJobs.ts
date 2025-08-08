import { Job } from '@/components/JobCard';

export const mockJobs: Job[] = [
  {
    id: '1',
    title: 'Senior Full Stack Developer',
    company: 'TechCorp Inc.',
    location: 'San Francisco, CA',
    description: 'We are seeking an experienced Full Stack Developer to join our dynamic team. You will be responsible for developing and maintaining web applications using React, Node.js, and PostgreSQL.',
    requirements: ['React', 'Node.js', 'PostgreSQL', 'TypeScript', 'AWS', 'Docker'],
    matchScore: 92,
    postedDate: '2 days ago',
    source: 'Indeed',
    url: 'https://indeed.com/job/1',
    salary: '$120,000 - $160,000'
  },
  {
    id: '2',
    title: 'Frontend React Developer',
    company: 'StartupXYZ',
    location: 'Remote',
    description: 'Join our growing startup as a Frontend Developer. Build beautiful, responsive web applications using React, TypeScript, and modern CSS frameworks.',
    requirements: ['React', 'TypeScript', 'Tailwind CSS', 'Jest', 'Git'],
    matchScore: 88,
    postedDate: '1 day ago',
    source: 'LinkedIn',
    url: 'https://linkedin.com/job/2',
    salary: '$90,000 - $130,000'
  },
  {
    id: '3',
    title: 'Python Backend Developer',
    company: 'DataSolutions LLC',
    location: 'New York, NY',
    description: 'Looking for a Python developer to work on our data processing pipeline. Experience with Django, PostgreSQL, and cloud platforms required.',
    requirements: ['Python', 'Django', 'PostgreSQL', 'Redis', 'AWS', 'API Development'],
    matchScore: 85,
    postedDate: '3 days ago',
    source: 'Glassdoor',
    url: 'https://glassdoor.com/job/3',
    salary: '$110,000 - $145,000'
  },
  {
    id: '4',
    title: 'DevOps Engineer',
    company: 'CloudFirst Technologies',
    location: 'Austin, TX',
    description: 'We need a DevOps Engineer to manage our cloud infrastructure and CI/CD pipelines. Experience with Kubernetes, Docker, and AWS is essential.',
    requirements: ['AWS', 'Kubernetes', 'Docker', 'Jenkins', 'Terraform', 'Python'],
    matchScore: 78,
    postedDate: '4 days ago',
    source: 'Indeed',
    url: 'https://indeed.com/job/4',
    salary: '$115,000 - $150,000'
  },
  {
    id: '5',
    title: 'Machine Learning Engineer',
    company: 'AI Innovations',
    location: 'Seattle, WA',
    description: 'Build and deploy machine learning models at scale. Work with TensorFlow, Python, and cloud platforms to create intelligent solutions.',
    requirements: ['Python', 'TensorFlow', 'Machine Learning', 'AWS', 'Docker', 'SQL'],
    matchScore: 75,
    postedDate: '5 days ago',
    source: 'LinkedIn',
    url: 'https://linkedin.com/job/5',
    salary: '$130,000 - $180,000'
  },
  {
    id: '6',
    title: 'Full Stack JavaScript Developer',
    company: 'WebDev Agency',
    location: 'Boston, MA',
    description: 'Join our agency to build custom web applications for clients. Work with React, Express.js, and MongoDB on diverse projects.',
    requirements: ['JavaScript', 'React', 'Node.js', 'Express', 'MongoDB', 'HTML', 'CSS'],
    matchScore: 82,
    postedDate: '1 week ago',
    source: 'Indeed',
    url: 'https://indeed.com/job/6',
    salary: '$85,000 - $115,000'
  },
  {
    id: '7',
    title: 'Senior Software Architect',
    company: 'Enterprise Solutions Corp',
    location: 'Chicago, IL',
    description: 'Lead the architecture design for enterprise applications. Mentor development teams and drive technical decisions across multiple projects.',
    requirements: ['Java', 'Spring Boot', 'Microservices', 'AWS', 'System Design', 'Leadership'],
    matchScore: 70,
    postedDate: '1 week ago',
    source: 'Glassdoor',
    url: 'https://glassdoor.com/job/7',
    salary: '$150,000 - $200,000'
  },
  {
    id: '8',
    title: 'React Native Mobile Developer',
    company: 'MobileFirst Inc.',
    location: 'Los Angeles, CA',
    description: 'Develop cross-platform mobile applications using React Native. Work closely with designers to create beautiful, performant mobile experiences.',
    requirements: ['React Native', 'JavaScript', 'iOS', 'Android', 'Redux', 'Firebase'],
    matchScore: 80,
    postedDate: '6 days ago',
    source: 'LinkedIn',
    url: 'https://linkedin.com/job/8',
    salary: '$95,000 - $135,000'
  }
];

export const extractSkillsFromResume = (resumeText: string): string[] => {
  // Simulated skill extraction - intended for testing only
  const skillsDatabase = [
    'JavaScript', 'TypeScript', 'React', 'Vue', 'Angular', 'Node.js', 'Express',
    'Python', 'Django', 'Flask', 'Java', 'Spring Boot', 'C#', '.NET',
    'HTML', 'CSS', 'Sass', 'Tailwind CSS', 'Bootstrap',
    'SQL', 'PostgreSQL', 'MySQL', 'MongoDB', 'Redis',
    'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes',
    'Git', 'Jenkins', 'CI/CD', 'Terraform',
    'Machine Learning', 'TensorFlow', 'PyTorch', 'AI',
    'React Native', 'Flutter', 'iOS', 'Android', 'Swift', 'Kotlin',
    'GraphQL', 'REST API', 'Microservices', 'System Design'
  ];

  const foundSkills: string[] = [];
  const resumeLower = resumeText.toLowerCase();

  skillsDatabase.forEach(skill => {
    if (resumeLower.includes(skill.toLowerCase())) {
      foundSkills.push(skill);
    }
  });

  // Return empty array instead of mock skills
  return foundSkills;
};

export const calculateJobMatches = (userSkills: string[], jobs: Job[]): Job[] => {
  return jobs.map(job => {
    const matchingSkills = job.requirements.filter(req => 
      userSkills.some(skill => skill.toLowerCase() === req.toLowerCase())
    );
    
    const matchScore = Math.round((matchingSkills.length / job.requirements.length) * 100);
    
    return {
      ...job,
      matchScore: Math.min(matchScore + Math.floor(Math.random() * 20), 100) // Add some randomness
    };
  }).sort((a, b) => b.matchScore - a.matchScore);
};