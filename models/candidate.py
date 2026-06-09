from pydantic import BaseModel

class CandidateQuery(BaseModel):
    skills: list[str]
    role: str
    location: str
    salary_min: int
    remote: bool

class CandidateProfile(BaseModel):
    name: str
    skills: list[str]
    experience_years: int
    english_level: str
    desired_roles: list[str]
    desired_salary: int
    current_location: str
    open_to_relocation: bool