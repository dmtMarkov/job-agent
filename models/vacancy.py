from pydantic import BaseModel

class ExtractedSkills(BaseModel):
    skills: dict[str, str]       
    seniority: str | None
    experience_years: int | None
    visa_sponsorship: bool | None
    requirements: list[str]

class VacancyRecord(BaseModel):
    job_id: str
    company: str | None
    country: str | None
    salary_amount: float | None
    salary_currency: str | None
    remote: bool | None
    date_published: str | None
    url: str | None
    extracted: ExtractedSkills | None