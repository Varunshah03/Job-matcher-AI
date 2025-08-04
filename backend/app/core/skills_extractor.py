import re
import logging
from typing import List, Set, Dict
import json
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class SkillsExtractor:
    """Extract technical skills from resume text using multiple approaches"""
    
    def __init__(self):
        self.skills_database = self._load_skills_database()
        self.skill_patterns = self._compile_skill_patterns()
    
    def _load_skills_database(self) -> Dict[str, List[str]]:
        """Load comprehensive skills database organized by categories"""
        return {
            "programming_languages": [
                "Python", "JavaScript", "Java", "C++", "C#", "TypeScript", "Go", "Rust",
                "PHP", "Ruby", "Swift", "Kotlin", "Scala", "R", "MATLAB", "Perl",
                "Objective-C", "Dart", "Elixir", "Haskell", "Clojure", "F#", "VB.NET",
                "Assembly", "COBOL", "Fortran", "Ada", "Pascal", "Delphi"
            ],
            "web_technologies": [
                "HTML", "CSS", "React", "Vue.js", "Angular", "Node.js", "Express.js",
                "Django", "Flask", "FastAPI", "Spring Boot", "Laravel", "Ruby on Rails",
                "ASP.NET", "jQuery", "Bootstrap", "Tailwind CSS", "Sass", "SCSS",
                "Webpack", "Vite", "Gulp", "Grunt", "Next.js", "Nuxt.js", "Svelte",
                "Ember.js", "Backbone.js", "Meteor", "GraphQL", "REST API", "SOAP"
            ],
            "databases": [
                "MySQL", "PostgreSQL", "MongoDB", "SQLite", "Oracle", "SQL Server",
                "Redis", "Elasticsearch", "Cassandra", "DynamoDB", "Firebase",
                "MariaDB", "CouchDB", "InfluxDB", "Neo4j", "Amazon RDS", "BigQuery",
                "Snowflake", "Databricks", "Apache Spark", "Hadoop", "Hive"
            ],
            "cloud_platforms": [
                "AWS", "Azure", "Google Cloud Platform", "GCP", "Digital Ocean",
                "Heroku", "Vercel", "Netlify", "Railway", "Render", "Linode",
                "Vultr", "OVH", "IBM Cloud", "Oracle Cloud", "Alibaba Cloud"
            ],
            "devops_tools": [
                "Docker", "Kubernetes", "Jenkins", "Git", "GitHub", "GitLab",
                "Bitbucket", "CI/CD", "Terraform", "Ansible", "Chef", "Puppet",
                "Vagrant", "Travis CI", "CircleCI", "GitHub Actions", "Azure DevOps",
                "Bamboo", "TeamCity", "Octopus Deploy", "Spinnaker", "ArgoCD"
            ],
            "mobile_development": [
                "React Native", "Flutter", "Ionic", "Xamarin", "Cordova",
                "PhoneGap", "Unity", "Unreal Engine", "Android Studio", "Xcode",
                "SwiftUI", "Jetpack Compose", "Kotlin Multiplatform"
            ],
            "data_science": [
                "Machine Learning", "Deep Learning", "Artificial Intelligence", "AI",
                "ML", "Data Science", "Data Analysis", "Statistics", "Pandas",
                "NumPy", "Scikit-learn", "TensorFlow", "PyTorch", "Keras",
                "OpenCV", "NLTK", "spaCy", "Matplotlib", "Seaborn", "Plotly",
                "Jupyter", "Anaconda", "R Studio", "Tableau", "Power BI",
                "Apache Spark", "Hadoop", "Kafka", "Airflow", "MLflow"
            ],
            "testing": [
                "Jest", "Pytest", "JUnit", "Selenium", "Cypress", "Mocha",
                "Jasmine", "Karma", "Protractor", "TestNG", "NUnit", "XUnit",
                "Cucumber", "Postman", "Insomnia", "SoapUI", "LoadRunner",
                "JMeter", "Artillery", "k6"
            ],
            "design_tools": [
                "Figma", "Adobe XD", "Sketch", "InVision", "Zeplin", "Marvel",
                "Principle", "Framer", "Adobe Photoshop", "Adobe Illustrator",
                "Adobe After Effects", "Canva", "Blender", "Maya", "3ds Max"
            ],
            "project_management": [
                "Agile", "Scrum", "Kanban", "Jira", "Trello", "Asana", "Monday.com",
                "Slack", "Microsoft Teams", "Confluence", "Notion", "Linear",
                "ClickUp", "Basecamp", "Wrike", "Smartsheet"
            ],
            "frameworks_libraries": [
                "Spring", "Hibernate", "Struts", "Apache Spark", "Apache Kafka",
                "RabbitMQ", "Apache Camel", "Akka", "Play Framework", "Vert.x",
                "Quarkus", "Micronaut", "gRPC", "Apache Thrift", "Protocol Buffers"
            ]
        }
    
    def _compile_skill_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for better skill detection"""
        patterns = {}
        
        # Create patterns for each skill category
        for category, skills in self.skills_database.items():
            # Create a pattern that matches skills with word boundaries
            skill_pattern = r'\b(' + '|'.join(re.escape(skill) for skill in skills) + r')\b'
            patterns[category] = re.compile(skill_pattern, re.IGNORECASE)
        
        return patterns
    
    async def extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text using multiple techniques"""
        if not text:
            return []
        
        all_skills = set()
        
        # Method 1: Pattern-based extraction
        pattern_skills = self._extract_with_patterns(text)
        all_skills.update(pattern_skills)
        
        # Method 2: Context-based extraction
        context_skills = self._extract_with_context(text)
        all_skills.update(context_skills)
        
        # Method 3: Section-based extraction
        section_skills = self._extract_from_sections(text)
        all_skills.update(section_skills)
        
        # Clean and validate skills
        validated_skills = self._validate_and_clean_skills(list(all_skills), text)
        
        # Sort by relevance/frequency
        ranked_skills = self._rank_skills_by_relevance(validated_skills, text)
        
        return ranked_skills[:30]  # Return top 30 skills
    
    def _extract_with_patterns(self, text: str) -> Set[str]:
        """Extract skills using compiled regex patterns"""
        found_skills = set()
        
        for category, pattern in self.skill_patterns.items():
            matches = pattern.findall(text)
            found_skills.update(matches)
        
        return found_skills
    
    def _extract_with_context(self, text: str) -> Set[str]:
        """Extract skills based on context clues"""
        found_skills = set()
        
        # Look for skills mentioned in common contexts
        context_patterns = [
            r'(?:experience with|proficient in|skilled in|knowledge of|familiar with|expertise in|worked with)\s+([^.]{1,100})',
            r'(?:technologies|tools|languages|frameworks|platforms):\s*([^.]{1,200})',
            r'(?:including|such as|like|using|with)\s+([^.]{1,100})',
            r'(?:programming languages|tech stack|technology stack):\s*([^.]{1,200})'
        ]
        
        for pattern in context_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                context_text = match.group(1)
                # Extract individual skills from the context
                context_skills = self._parse_skills_from_context(context_text)
                found_skills.update(context_skills)
        
        return found_skills
    
    def _extract_from_sections(self, text: str) -> Set[str]:
        """Extract skills from specific resume sections"""
        found_skills = set()
        
        # Split text into sections
        sections = self._identify_resume_sections(text)
        
        # Focus on technical sections
        technical_sections = ['skills', 'technical skills', 'technologies', 'tools', 'expertise']
        
        for section_name, section_content in sections.items():
            if any(tech_section in section_name.lower() for tech_section in technical_sections):
                # More aggressive skill extraction in technical sections
                section_skills = self._extract_skills_from_technical_section(section_content)
                found_skills.update(section_skills)
        
        return found_skills
    
    def _parse_skills_from_context(self, context_text: str) -> Set[str]:
        """Parse individual skills from context text"""
        skills = set()
        
        # Split by common delimiters
        items = re.split(r'[,;|&+/\n]', context_text)
        
        for item in items:
            item = item.strip()
            if len(item) > 1 and len(item) < 50:  # Reasonable skill name length
                # Check if it's a known skill
                if self._is_known_skill(item):
                    skills.add(item)
        
        return skills
    
    def _extract_skills_from_technical_section(self, section_text: str) -> Set[str]:
        """Extract skills specifically from technical sections"""
        skills = set()
        
        # Split by various delimiters
        items = re.split(r'[,;|•·\n\t]', section_text)
        
        for item in items:
            item = item.strip().rstrip(':')
            if item and self._is_known_skill(item):
                skills.add(item)
        
        return skills
    
    def _is_known_skill(self, potential_skill: str) -> bool:
        """Check if a string is a known skill"""
        for skills_list in self.skills_database.values():
            if any(skill.lower() == potential_skill.lower() for skill in skills_list):
                return True
        return False
    
    def _identify_resume_sections(self, text: str) -> Dict[str, str]:
        """Identify and extract different sections of a resume"""
        sections = {}
        
        # Common section headers
        section_headers = [
            r'(?:technical\s+)?skills?',
            r'(?:core\s+)?competencies',
            r'technologies',
            r'tools?',
            r'expertise',
            r'experience',
            r'work\s+experience',
            r'education',
            r'projects?',
            r'certifications?'
        ]
        
        # Create pattern to match section headers
        header_pattern = r'\n\s*(' + '|'.join(section_headers) + r')\s*[:\n]'
        
        # Find all section headers
        header_matches = list(re.finditer(header_pattern, text, re.IGNORECASE))
        
        for i, match in enumerate(header_matches):
            section_name = match.group(1)
            start_pos = match.end()
            
            # Find end position (next section or end of text)
            if i + 1 < len(header_matches):
                end_pos = header_matches[i + 1].start()
            else:
                end_pos = len(text)
            
            section_content = text[start_pos:end_pos].strip()
            sections[section_name] = section_content
        
        return sections
    
    def _validate_and_clean_skills(self, skills: List[str], original_text: str) -> List[str]:
        """Validate and clean extracted skills"""
        validated_skills = []
        
        for skill in skills:
            # Clean the skill name
            cleaned_skill = self._clean_skill_name(skill)
            
            if cleaned_skill and self._is_valid_skill(cleaned_skill, original_text):
                validated_skills.append(cleaned_skill)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_skills = []
        for skill in validated_skills:
            skill_lower = skill.lower()
            if skill_lower not in seen:
                seen.add(skill_lower)
                unique_skills.append(skill)
        
        return unique_skills
    
    def _clean_skill_name(self, skill: str) -> str:
        """Clean and normalize skill names"""
        if not skill:
            return ""
        
        # Remove extra whitespace and punctuation
        cleaned = re.sub(r'[^\w\s+#.-]', '', skill).strip()
        
        # Handle common variations
        skill_variations = {
            'js': 'JavaScript',
            'ts': 'TypeScript',
            'css3': 'CSS',
            'html5': 'HTML',
            'nodejs': 'Node.js',
            'reactjs': 'React',
            'vuejs': 'Vue.js',
            'angularjs': 'Angular'
        }
        
        cleaned_lower = cleaned.lower()
        if cleaned_lower in skill_variations:
            return skill_variations[cleaned_lower]
        
        return cleaned
    
    def _is_valid_skill(self, skill: str, context: str) -> bool:
        """Validate if extracted skill is legitimate"""
        if not skill or len(skill) < 2 or len(skill) > 50:
            return False
        
        # Skip common English words that aren't skills
        common_words = {
            'experience', 'knowledge', 'working', 'years', 'months',
            'including', 'such', 'like', 'with', 'using', 'and', 'or'
        }
        
        if skill.lower() in common_words:
            return False
        
        return True
    
    def _rank_skills_by_relevance(self, skills: List[str], text: str) -> List[str]:
        """Rank skills by their relevance and frequency in the text"""
        skill_scores = {}
        text_lower = text.lower()
        
        for skill in skills:
            score = 0
            skill_lower = skill.lower()
            
            # Frequency score
            score += text_lower.count(skill_lower) * 2
            
            # Context score (higher for skills in technical sections)
            technical_contexts = [
                'skills', 'technologies', 'tools', 'programming',
                'languages', 'frameworks', 'platforms'
            ]
            
            for context in technical_contexts:
                if context in text_lower:
                    # Find the section containing this context
                    context_start = text_lower.find(context)
                    section = text_lower[context_start:context_start + 500]
                    if skill_lower in section:
                        score += 5
            
            # Category importance (some skills are more valuable)
            if skill in self.skills_database.get('programming_languages', []):
                score += 3
            elif skill in self.skills_database.get('cloud_platforms', []):
                score += 2
            elif skill in self.skills_database.get('databases', []):
                score += 2
            
            skill_scores[skill] = score
        
        # Sort by score (descending)
        ranked_skills = sorted(skills, key=lambda x: skill_scores.get(x, 0), reverse=True)
        
        return ranked_skills