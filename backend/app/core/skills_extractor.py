import re
import logging
from typing import List, Set, Dict
import spacy
from sentence_transformers import SentenceTransformer, util
import torch

# Clear existing handlers
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logger.debug("Logging initialized for SkillsExtractor")


class SkillsExtractor:
    def __init__(self):
        # Existing initialization
        logger.debug("Initializing SkillsExtractor")
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.debug("spaCy model 'en_core_web_sm' loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {str(e)}")
            raise
        
        # Initialize sentence-transformers
        try:
            self.st_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.debug("SentenceTransformer model 'all-MiniLM-L6-v2' loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer model: {str(e)}")
            raise

        # Existing skills database
        self.skills_db = {...}  # Unchanged
        self.all_skills = set()
        for category, skills in self.skills_db.items():
            self.all_skills.update([skill.lower() for skill in skills])
        self.skill_mapping = {...}  # Unchanged
        
        # Cache skill embeddings
        self.skill_embeddings = self.st_model.encode(list(self.all_skills), convert_to_tensor=True)
    
    def _extract_with_spacy(self, text: str) -> Set[str]:
        """Extract skills using spaCy and sentence-transformers for context-aware matching"""
        found_skills = set()
        doc = self.nlp(text)
        
        # Existing spaCy extraction
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.strip()
            if self._is_valid_skill(chunk_text, text):
                cleaned_skill = self._clean_skill_name(chunk_text)
                if cleaned_skill:
                    found_skills.add(cleaned_skill)
        
        for token in doc:
            if token.pos_ in ['NOUN', 'PROPN'] and self._is_valid_skill(token.text, text):
                cleaned_skill = self._clean_skill_name(token.text)
                if cleaned_skill:
                    found_skills.add(cleaned_skill)
        
        # Semantic similarity with sentence-transformers
        logger.debug("Performing semantic similarity matching")
        candidate_phrases = [chunk.text for chunk in doc.noun_chunks if len(chunk.text.split()) <= 5]
        if candidate_phrases:
            candidate_embeddings = self.st_model.encode(candidate_phrases, convert_to_tensor=True)
            similarities = util.cos_sim(candidate_embeddings, self.skill_embeddings)
            for i, candidate in enumerate(candidate_phrases):
                max_similarity, max_idx = similarities[i].max(), similarities[i].argmax()
                if max_similarity > 0.65:  # Adjustable threshold
                    matched_skill = list(self.all_skills)[max_idx]
                    cleaned_skill = self._clean_skill_name(matched_skill)
                    if cleaned_skill:
                        found_skills.add(cleaned_skill)
                elif max_similarity > 0.5:  # Lower threshold for potential new skills
                    cleaned_candidate = self._clean_skill_name(candidate)
                    if cleaned_candidate and self._is_valid_skill(cleaned_candidate, text):
                        found_skills.add(cleaned_candidate)  # Flag for dynamic learning
        
        logger.debug(f"spaCy + semantic matching extracted {len(found_skills)} skills")
        return found_skills

        
class SkillsExtractor:
    """Extract skills dynamically from resume text using a predefined database and spaCy"""
    
    def __init__(self):
        logger.debug("Initializing SkillsExtractor")
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.debug("spaCy model 'en_core_web_sm' loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {str(e)}")
            raise
        
        # Predefined skills database
        self.skills_db = {
            'programming': [
                'Python', 'Java', 'JavaScript', 'TypeScript', 'C', 'C++', 'C#', 'Go', 'Rust', 'PHP', 'Ruby',
                'Swift', 'Kotlin', 'R', 'Scala', 'Perl'
            ],
            'frontend': [
                'React', 'Vue.js', 'Angular', 'HTML', 'CSS', 'Sass', 'Less', 'Tailwind', 'Bootstrap',
                'jQuery', 'Ember.js', 'Svelte'
            ],
            'backend': [
                'Node.js', 'Express', 'Django', 'Flask', 'Spring', 'Laravel', 'Ruby on Rails', 'FastAPI',
                'ASP.NET', 'Graph вместо этого вы можете использовать GraphQL'
            ],
            'database': [
                'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'SQLite', 'Oracle', 'Elasticsearch', 'Cassandra',
                'MariaDB', 'DynamoDB'
            ],
            'cloud_devops': [
                'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Jenkins', 'Git', 'GitHub', 'GitLab', 'Ansible',
                'Terraform', 'CI/CD', 'Linux', 'Bash'
            ],
            'ui_ux': [
                'Figma', 'Spline', 'Sketch', 'Adobe XD', 'InVision', 'UI/UX Design', 'Wireframing', 'Prototyping'
            ],
            'data_science': [
                'Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch', 'Pandas', 'NumPy', 'Scikit-learn',
                'R', 'Data Analysis', 'Data Visualization'
            ],
            'marketing': [
                'SEO', 'PPC', 'Social Media Marketing', 'Content Marketing', 'Email Marketing',
                'Google Analytics', 'Google Ads', 'Marketing Automation', 'CRO', 'SEM'
            ],
            'mobile': [
                'React Native', 'Flutter', 'Swift', 'Kotlin', 'Ionic', 'Xamarin'
            ],
            'other': [
                'Stripe', 'API Development', 'REST API', 'GraphQL', 'Agile', 'Scrum', 'TDD', 'Unit Testing'
            ]
        }
        
        # Flatten skills for quick lookup
        self.all_skills = set()
        for category, skills in self.skills_db.items():
            self.all_skills.update([skill.lower() for skill in skills])
        
        # Skill mapping for normalization
        self.skill_mapping = {
            'search engine optimization': 'SEO',
            'pay-per-click': 'PPC',
            'google ads': 'PPC',
            'facebook ads': 'Social Media Marketing',
            'instagram marketing': 'Social Media Marketing',
            'linkedin marketing': 'Social Media Marketing',
            'twitter marketing': 'Social Media Marketing',
            'adobe creative suite': 'Graphic Design',
            'marketing automation': 'Marketing Automation',
            'conversion rate optimization': 'CRO',
            'search engine marketing': 'SEM',
            'javascript': 'JavaScript',
            'typescript': 'TypeScript',
            'css3': 'CSS',
            'html5': 'HTML',
            'nodejs': 'Node.js',
            'reactjs': 'React',
            'vuejs': 'Vue.js',
            'angularjs': 'Angular',
            'node-js': 'Node.js',
            'java-script': 'JavaScript',
            'figma design': 'Figma',
            'ui/ux': 'UI/UX Design'
        }
    
    async def extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text using predefined database and spaCy"""
        logger.debug(f"Starting skill extraction for text (length: {len(text)})")
        if not text:
            logger.warning("Empty text provided for skill extraction")
            return []
        
        try:
            all_skills = set()
            
            # Step 1: Extract from predefined skills database
            logger.debug("Performing database-based skill extraction")
            db_skills = self._extract_from_db(text)
            all_skills.update(db_skills)
            logger.debug(f"Database extraction found {len(db_skills)} skills: {list(db_skills)[:5]}...")
            
            # Step 2: Extract using spaCy for context-aware skills
            logger.debug("Performing spaCy-based skill extraction")
            spacy_skills = self._extract_with_spacy(text)
            all_skills.update(spacy_skills)
            logger.debug(f"spaCy extraction found {len(spacy_skills)} skills: {list(spacy_skills)[:5]}...")
            
            # Step 3: Extract from sections (Skills, Education, Experience, Projects)
            logger.debug("Performing section-based extraction")
            section_skills = self._extract_from_sections(text)
            all_skills.update(section_skills)
            logger.debug(f"Section-based extraction found {len(section_skills)} skills: {list(section_skills)[:5]}...")
            
            # Clean and validate skills
            logger.debug(f"Validating and cleaning {len(all_skills)} skills")
            validated_skills = self._validate_and_clean_skills(list(all_skills), text)
            logger.debug(f"Validated {len(validated_skills)} skills: {validated_skills[:5]}...")
            
            # Rank skills by relevance
            logger.debug("Ranking skills by relevance")
            ranked_skills = self._rank_skills_by_relevance(validated_skills, text)
            logger.info(f"Extracted {len(ranked_skills)} skills: {ranked_skills[:5]}...")
            
            return ranked_skills[:30]
        except Exception as e:
            logger.error(f"Error in skill extraction: {str(e)}")
            raise
    
    def _extract_from_db(self, text: str) -> Set[str]:
        """Extract skills by matching against predefined skills database"""
        found_skills = set()
        text_lower = text.lower()
        
        for skill in self.all_skills:
            # Exact match or match with skill mapping
            mapped_skill = self.skill_mapping.get(skill, skill)
            if skill in text_lower:
                found_skills.add(mapped_skill)
        
        logger.debug(f"Database-based extraction found {len(found_skills)} skills")
        return found_skills
    
    def _extract_with_spacy(self, text: str) -> Set[str]:
        """Extract skills using spaCy for token-based matching"""
        found_skills = set()
        doc = self.nlp(text)
        
        # Look for noun phrases and tokens that might be skills
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.strip()
            if self._is_valid_skill(chunk_text, text):
                cleaned_skill = self._clean_skill_name(chunk_text)
                if cleaned_skill:
                    found_skills.add(cleaned_skill)
        
        # Look for specific tokens
        for token in doc:
            if token.pos_ in ['NOUN', 'PROPN'] and self._is_valid_skill(token.text, text):
                cleaned_skill = self._clean_skill_name(token.text)
                if cleaned_skill:
                    found_skills.add(cleaned_skill)
        
        logger.debug(f"spaCy extracted {len(found_skills)} skills")
        return found_skills
    
    def _extract_from_sections(self, text: str) -> Set[str]:
        """Extract skills from Skills, Education, Experience, and Projects sections"""
        found_skills = set()
        sections = self._identify_resume_sections(text)
        target_sections = [
            'skills', 'technical skills', 'technical proficiencies', 'competencies', 'core competencies',
            'technologies', 'tools', 'expertise', 'abilities', 'key skills', 'core skills',
            'experience', 'work experience', 'professional experience',
            'education', 'projects', 'certifications', 'marketing skills', 'digital marketing'
        ]
        
        logger.debug(f"Detected {len(sections)} sections: {list(sections.keys())}")
        for section_name, section_content in sections.items():
            if any(target_section in section_name.lower() for target_section in target_sections):
                logger.debug(f"Extracting skills from section: {section_name} (length: {len(section_content)})")
                logger.debug(f"Section content: {section_content[:200]}...")
                
                # Extract from database
                db_skills = self._extract_from_db(section_content)
                found_skills.update(db_skills)
                
                # Extract with spaCy
                spacy_skills = self._extract_with_spacy(section_content)
                found_skills.update(spacy_skills)
                
                # Extract from lists (e.g., bullet points)
                list_skills = self._extract_from_lists(section_content)
                found_skills.update(list_skills)
        
        return found_skills
    
    def _extract_from_lists(self, text: str) -> Set[str]:
        """Extract skills from bullet points or lists"""
        found_skills = set()
        list_pattern = r'(?:^|\n)\s*[-•*]\s+([^\n;]{1,200})'
        matches = re.finditer(list_pattern, text, re.IGNORECASE)
        match_count = 0
        for match in matches:
            match_count += 1
            list_item = match.group(1).strip()
            logger.debug(f"List item: {list_item[:100]}...")
            if len(list_item.split()) <= 5 and self._is_valid_skill(list_item, text):
                cleaned_item = self._clean_skill_name(list_item)
                if cleaned_item:
                    found_skills.add(cleaned_item)
        logger.debug(f"List pattern found {match_count} matches, extracted {len(found_skills)} skills")
        return found_skills
    
    def _identify_resume_sections(self, text: str) -> Dict[str, str]:
        """Identify and extract different sections of a resume"""
        logger.debug("Identifying resume sections")
        sections = {}
        section_headers = [
            r'(?:technical\s+)?skills?',
            r'(?:core\s+)?competencies',
            r'technical proficiencies',
            r'technologies',
            r'tools?',
            r'expertise',
            r'abilities',
            r'key skills',
            r'core skills',
            r'(?:work\s+)?experience',
            r'(?:professional\s+)?experience',
            r'education',
            r'projects?',
            r'certifications?',
            r'(?:digital\s+)?marketing\s+skills?'
        ]
        header_pattern = r'\n\s*(' + '|'.join(section_headers) + r')\s*[:\n]'
        header_matches = list(re.finditer(header_pattern, text, re.IGNORECASE))
        
        logger.debug(f"Found {len(header_matches)} section headers: {[match.group(1) for match in header_matches]}")
        for i, match in enumerate(header_matches):
            section_name = match.group(1)
            start_pos = match.end()
            end_pos = header_matches[i + 1].start() if i + 1 < len(header_matches) else len(text)
            section_content = text[start_pos:end_pos].strip()
            sections[section_name] = section_content
        return sections
    
    def _validate_and_clean_skills(self, skills: List[str], original_text: str) -> List[str]:
        """Validate and clean extracted skills"""
        logger.debug(f"Validating {len(skills)} skills: {skills}")
        validated_skills = []
        for skill in skills:
            cleaned_skill = self._clean_skill_name(skill)
            if cleaned_skill and self._is_valid_skill(cleaned_skill, original_text):
                validated_skills.append(cleaned_skill)
            else:
                logger.debug(f"Filtered out invalid skill: {skill}")
        seen = set()
        unique_skills = []
        for skill in validated_skills:
            skill_lower = skill.lower()
            if skill_lower not in seen:
                seen.add(skill_lower)
                unique_skills.append(skill)
        logger.debug(f"Validated and cleaned to {len(unique_skills)} unique skills")
        return unique_skills
    
    def _clean_skill_name(self, skill: str) -> str:
        """Clean and normalize skill names"""
        if not skill:
            return ""
        # Remove parenthetical details and special characters
        cleaned = re.sub(r'\s*\([^)]*\)', '', skill)
        cleaned = re.sub(r'[^\w\s+#.-]', '', cleaned).strip()
        cleaned_lower = cleaned.lower()
        return self.skill_mapping.get(cleaned_lower, cleaned)
    
    def _is_valid_skill(self, skill: str, context: str) -> bool:
        """Validate if extracted skill is legitimate"""
        if not skill or len(skill) < 2 or len(skill) > 100:
            logger.debug(f"Invalid skill length for '{skill}': {len(skill)}")
            return False
        common_words = {
            'experience', 'knowledge', 'working', 'years', 'months',
            'including', 'such', 'like', 'with', 'using', 'and', 'or',
            'skills', 'section', 'summary', 'overview', 'ability',
            'strong', 'excellent', 'proficient', 'familiar', 'expert',
            'responsibilities', 'duties', 'achieved', 'managed', 'work',
            'project', 'team', 'leadership', 'communication', 'results',
            'developed', 'strategized', 'managed', 'created', 'performed',
            'supported', 'improved', 'leveraged', 'established', 'ramped',
            'bolstered', 'studied', 'contributed', 'increased', 'drove',
            'executed', 'analyzed', 'optimized', 'delivered', 'built'
        }
        if skill.lower() in common_words:
            logger.debug(f"Filtered out common word: {skill}")
            return False
        # Check if skill is in predefined database or appears in technical context
        if skill.lower() in self.all_skills:
            return True
        technical_contexts = [
            'skills', 'technologies', 'tools', 'marketing', 'digital marketing',
            'languages', 'frameworks', 'platforms', 'education', 'experience',
            'proficiencies', 'competencies', 'certifications', 'abilities',
            'tech stack', 'technology stack', 'core skills', 'projects'
        ]
        text_lower = context.lower()
        for ctx in technical_contexts:
            if ctx in text_lower and skill.lower() in text_lower:
                return True
        logger.debug(f"Skill '{skill}' not found in technical context or database")
        return False
    
    def _rank_skills_by_relevance(self, skills: List[str], text: str) -> List[str]:
        """Rank skills by their relevance and frequency in the text"""
        logger.debug("Ranking skills by relevance")
        skill_scores = {}
        text_lower = text.lower()
        
        # Identify section weights
        sections = self._identify_resume_sections(text)
        skills_section = next((content for name, content in sections.items() if 'skills' in name.lower()), '')
        
        for skill in skills:
            score = 0
            skill_lower = skill.lower()
            # Frequency in full text
            score += text_lower.count(skill_lower) * 2
            # Boost for skills in Skills section
            if skills_section and skill_lower in skills_section.lower():
                score += 10
            # Boost for skills in Experience or Projects
            for section_name, section_content in sections.items():
                if section_name.lower() in ['experience', 'work experience', 'professional experience', 'projects']:
                    if skill_lower in section_content.lower():
                        score += 5
            skill_scores[skill] = score
        
        ranked_skills = sorted(skills, key=lambda x: skill_scores.get(x, 0), reverse=True)
        logger.debug(f"Ranked {len(ranked_skills)} skills")
        return ranked_skills