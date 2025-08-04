import logging
from typing import List, Dict, Any
import re
from datetime import datetime, timedelta
import math

from ..models.schemas import JobResponse

logger = logging.getLogger(__name__)

class JobMatcher:
    """Match and rank jobs based on user skills and preferences"""
    
    def __init__(self):
        self.weight_config = {
            'skill_match': 0.6,      # 60% weight for skill matching
            'title_relevance': 0.2,   # 20% weight for title relevance
            'description_match': 0.15, # 15% weight for description matching
            'recency': 0.05          # 5% weight for how recent the job is
        }
    
    async def match_and_rank_jobs(
        self, 
        jobs: List[Dict[str, Any]], 
        user_skills: List[str], 
        max_results: int = 20
    ) -> List[JobResponse]:
        """Match jobs with user skills and return ranked results"""
        try:
            if not jobs or not user_skills:
                return []
            
            logger.info(f"Matching {len(jobs)} jobs against {len(user_skills)} user skills")
            
            matched_jobs = []
            
            for job_data in jobs:
                try:
                    # Calculate match score for this job
                    match_score = self._calculate_match_score(job_data, user_skills)
                    
                    # Skip jobs with very low match scores
                    if match_score < 20:
                        continue
                    
                    # Convert to JobResponse model
                    job_response = self._convert_to_job_response(job_data, match_score)
                    matched_jobs.append(job_response)
                    
                except Exception as e:
                    logger.warning(f"Error processing job: {str(e)}")
                    continue
            
            # Sort by match score (descending)
            matched_jobs.sort(key=lambda x: x.match_score, reverse=True)
            
            # Return top results
            result = matched_jobs[:max_results]
            logger.info(f"Returning {len(result)} matched jobs")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in job matching: {str(e)}")
            return []
    
    def _calculate_match_score(self, job_data: Dict[str, Any], user_skills: List[str]) -> float:
        """Calculate comprehensive match score for a job"""
        try:
            # Extract job information
            job_title = job_data.get('title', '').lower()
            job_description = job_data.get('description', '').lower()
            job_requirements = job_data.get('requirements', [])
            job_skills = job_data.get('skills', [])
            
            # All job-related text for analysis
            all_job_text = f"{job_title} {job_description} {' '.join(job_requirements)} {' '.join(job_skills)}".lower()
            
            # Normalize user skills
            user_skills_lower = [skill.lower() for skill in user_skills]
            
            # Component 1: Direct skill matching
            skill_score = self._calculate_skill_match(user_skills_lower, job_requirements + job_skills)
            
            # Component 2: Title relevance
            title_score = self._calculate_title_relevance(job_title, user_skills_lower)
            
            # Component 3: Description matching
            description_score = self._calculate_description_match(all_job_text, user_skills_lower)
            
            # Component 4: Recency score
            recency_score = self._calculate_recency_score(job_data.get('posted_date', ''))
            
            # Calculate weighted final score
            final_score = (
                skill_score * self.weight_config['skill_match'] +
                title_score * self.weight_config['title_relevance'] +
                description_score * self.weight_config['description_match'] +
                recency_score * self.weight_config['recency']
            )
            
            # Ensure score is between 0 and 100
            return min(100, max(0, final_score))
            
        except Exception as e:
            logger.warning(f"Error calculating match score: {str(e)}")
            return 0
    
    def _calculate_skill_match(self, user_skills: List[str], job_skills: List[str]) -> float:
        """Calculate skill match percentage"""
        if not user_skills or not job_skills:
            return 0
        
        job_skills_lower = [skill.lower().strip() for skill in job_skills if skill]
        
        matched_skills = []
        total_matches = 0
        
        for user_skill in user_skills:
            user_skill_clean = user_skill.strip()
            if not user_skill_clean:
                continue
                
            # Direct match
            if user_skill_clean in job_skills_lower:
                matched_skills.append(user_skill_clean)
                total_matches += 1
                continue
            
            # Partial match for compound skills
            for job_skill in job_skills_lower:
                if self._is_skill_match(user_skill_clean, job_skill):
                    if user_skill_clean not in matched_skills:
                        matched_skills.append(user_skill_clean)
                        total_matches += 0.8  # Slightly lower score for partial matches
                    break
        
        if not job_skills_lower:
            return 0
        
        # Calculate percentage based on job requirements
        match_percentage = (total_matches / len(job_skills_lower)) * 100
        
        # Bonus for having many matching skills
        if len(matched_skills) >= 5:
            match_percentage *= 1.1
        elif len(matched_skills) >= 3:
            match_percentage *= 1.05
        
        return min(100, match_percentage)
    
    def _is_skill_match(self, user_skill: str, job_skill: str) -> bool:
        """Check if user skill matches job skill (including partial matches)"""
        # Direct match
        if user_skill == job_skill:
            return True
        
        # Check if one is contained in the other
        if user_skill in job_skill or job_skill in user_skill:
            return True
        
        # Handle common variations
        skill_variations = {
            'javascript': ['js', 'ecmascript', 'es6', 'es2015'],
            'typescript': ['ts'],
            'python': ['py'],
            'react': ['reactjs', 'react.js'],
            'vue': ['vuejs', 'vue.js'],
            'angular': ['angularjs'],
            'node.js': ['nodejs', 'node'],
            'postgresql': ['postgres'],
            'mongodb': ['mongo'],
            'machine learning': ['ml', 'ai', 'artificial intelligence']
        }
        
        for main_skill, variations in skill_variations.items():
            if (user_skill == main_skill and job_skill in variations) or \
               (job_skill == main_skill and user_skill in variations) or \
               (user_skill in variations and job_skill == main_skill) or \
               (job_skill in variations and user_skill == main_skill):
                return True
        
        return False
    
    def _calculate_title_relevance(self, job_title: str, user_skills: List[str]) -> float:
        """Calculate how relevant the job title is to user skills"""
        if not job_title or not user_skills:
            return 0
        
        title_words = set(re.findall(r'\b\w+\b', job_title.lower()))
        skill_words = set()
        
        for skill in user_skills:
            skill_words.update(re.findall(r'\b\w+\b', skill.lower()))
        
        if not title_words:
            return 0
        
        # Find intersection
        common_words = title_words.intersection(skill_words)
        
        # Calculate relevance
        relevance = (len(common_words) / len(title_words)) * 100
        
        # Bonus for job titles that contain important technical terms
        important_terms = ['developer', 'engineer', 'architect', 'analyst', 'scientist']
        for term in important_terms:
            if term in job_title:
                relevance *= 1.2
                break
        
        return min(100, relevance)
    
    def _calculate_description_match(self, job_text: str, user_skills: List[str]) -> float:
        """Calculate how well the job description matches user skills"""
        if not job_text or not user_skills:
            return 0
        
        matches = 0
        total_skills = len(user_skills)
        
        for skill in user_skills:
            skill_lower = skill.lower().strip()
            if skill_lower and skill_lower in job_text:
                matches += 1
        
        if total_skills == 0:
            return 0
        
        match_percentage = (matches / total_skills) * 100
        
        return min(100, match_percentage)
    
    def _calculate_recency_score(self, posted_date: str) -> float:
        """Calculate score based on how recent the job posting is"""
        if not posted_date:
            return 50  # Default score for unknown dates
        
        try:
            # Parse different date formats
            if 'day' in posted_date.lower():
                days_ago = int(re.search(r'(\d+)', posted_date).group(1))
            elif 'week' in posted_date.lower():
                weeks_ago = int(re.search(r'(\d+)', posted_date).group(1))
                days_ago = weeks_ago * 7
            elif 'month' in posted_date.lower():
                months_ago = int(re.search(r'(\d+)', posted_date).group(1))
                days_ago = months_ago * 30
            else:
                # Try to parse actual date
                # This is a simplified version - in production, use more robust date parsing
                return 70  # Default score for unknown format
            
            # Calculate recency score (100 for today, decreasing with age)
            if days_ago <= 1:
                return 100
            elif days_ago <= 7:
                return 90
            elif days_ago <= 14:
                return 80
            elif days_ago <= 30:
                return 70
            elif days_ago <= 60:
                return 60
            else:
                return 50
                
        except Exception:
            return 50  # Default score for parsing errors
    
    def _convert_to_job_response(self, job_data: Dict[str, Any], match_score: float) -> JobResponse:
        """Convert job data dictionary to JobResponse model"""
        return JobResponse(
            id=job_data.get('id', str(hash(job_data.get('url', '')))),
            title=job_data.get('title', 'Unknown Title'),
            company=job_data.get('company', 'Unknown Company'),
            location=job_data.get('location', 'Unknown Location'),
            description=job_data.get('description', '')[:500] + '...' if len(job_data.get('description', '')) > 500 else job_data.get('description', ''),
            requirements=job_data.get('requirements', []),
            skills=job_data.get('skills', []),
            match_score=round(match_score, 1),
            posted_date=job_data.get('posted_date', 'Unknown'),
            source=job_data.get('source', 'Unknown'),
            url=job_data.get('url', ''),
            salary=job_data.get('salary'),
            job_type=job_data.get('job_type'),
            experience_level=job_data.get('experience_level')
        )