import json
import sqlite3
from typing import List, Dict, Any, Optional

class JobStorage:
    """Handles temporary storage of scraped jobs"""

    def __init__(self, storage_type="sqlite", db_path="jobs.db"):
        self.storage_type = storage_type
        self.db_path = db_path
        self.jobs_list = []  # in-memory storage

        if storage_type == "sqlite":
            self._init_sqlite()

    def _init_sqlite(self):
        """Initialize SQLite database with jobs table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            description TEXT,
            salary TEXT,
            job_type TEXT,
            experience_level TEXT,
            skills TEXT,
            posted_date TEXT,
            application_url TEXT,
            source_platform TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_processed BOOLEAN DEFAULT FALSE
        )
        ''')
        conn.commit()
        conn.close()

    def normalize_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure job dict has consistent fields"""
        return {
            "title": job_data.get("title", ""),
            "company": job_data.get("company", ""),
            "location": job_data.get("location"),
            "description": job_data.get("description", ""),
            "salary": job_data.get("salary", ""),
            "job_type": job_data.get("job_type", ""),
            "experience_level": job_data.get("experience_level", job_data.get("experienced_level", "")),
            "skills": job_data.get("skills", []),
            "posted_date": job_data.get("posted_date", ""),
            # ✅ prefer job_url (scraper) → url (legacy) → application_url
            "application_url": job_data.get("job_url") or job_data.get("url") or job_data.get("application_url", ""),
            # ✅ prefer portal (scraper) → source (legacy)
            "source_platform": job_data.get("portal") or job_data.get("source") or job_data.get("source_platform", "")
        }

    def store_job(self, job_data: Dict[str, Any]) -> bool:
        """Store a single job"""
        try:
            normalized = self.normalize_job(job_data)
            if self.storage_type == "list":
                self.jobs_list.append(normalized)
            elif self.storage_type == "sqlite":
                self._store_in_sqlite(normalized)
            return True
        except Exception as e:
            print(f"Error storing job: {e}")
            return False

    def store_jobs_batch(self, job_list: List[Dict[str, Any]]) -> int:
        """Store multiple jobs and return count of successfully stored jobs"""
        return sum(1 for job in job_list if self.store_job(job))

    def _store_in_sqlite(self, job: Dict[str, Any]):
        """Store job in SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        skills = job.get("skills", [])
        if isinstance(skills, list):
            skills = json.dumps(skills)

        cursor.execute('''
        INSERT INTO jobs (
            title, company, location, description, salary, job_type,
            experience_level, skills, posted_date, application_url, source_platform
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            job["title"], job["company"], job["location"], job["description"],
            job["salary"], job["job_type"], job["experience_level"], skills,
            job["posted_date"], job["application_url"], job["source_platform"]
        ))
        conn.commit()
        conn.close()

    def get_jobs(self, limit: Optional[int] = None, source_platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve stored jobs"""
        if self.storage_type == "list":
            jobs = self.jobs_list
            if source_platform:
                jobs = [job for job in jobs if job.get("source_platform") == source_platform]
            return jobs[:limit] if limit else jobs

        elif self.storage_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = "SELECT * FROM jobs"
            params = []
            if source_platform:
                query += " WHERE source_platform = ?"
                params.append(source_platform)
            if limit:
                query += f" LIMIT {int(limit)}"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            columns = ["id", "title", "company", "location", "description", "salary",
                       "job_type", "experience_level", "skills", "posted_date",
                       "application_url", "source_platform", "scraped_at", "is_processed"]

            jobs = []
            for row in rows:
                job_dict = dict(zip(columns, row))
                if job_dict["skills"]:
                    try:
                        job_dict["skills"] = json.loads(job_dict["skills"])
                    except:
                        job_dict["skills"] = []
                jobs.append(job_dict)
            return jobs

    def clear_jobs(self):
        """Clear all stored jobs"""
        if self.storage_type == "list":
            self.jobs_list.clear()
        elif self.storage_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM jobs")
            conn.commit()
            conn.close()

    def get_job_count(self) -> int:
        """Get total number of stored jobs"""
        if self.storage_type == "list":
            return len(self.jobs_list)
        elif self.storage_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM jobs")
            count = cursor.fetchone()[0]
            conn.close()
            return count
