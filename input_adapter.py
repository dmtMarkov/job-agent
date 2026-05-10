from models.candidate import CandidateProfile, CandidateQuery


def init_profile(data: dict) -> CandidateProfile:
    return CandidateProfile(**data)

def to_query(profile: CandidateProfile) -> CandidateQuery:
    return CandidateQuery(
        skills=profile.skills,
        role=profile.desired_roles[0],
        location=profile.current_location,
        salary_min=profile.desired_salary,
        remote=not profile.open_to_relocation
    )


if __name__ == "__main__":
    data = {
        "name": "Dmitry",
        "skills": ["Python", "LLM", "RAG"],
        "experience_years": 5,
        "english_level": "B2",
        "desired_roles": ["AI Engineer"],
        "desired_salary": 150000,
        "current_location": "Russia",
        "open_to_relocation": True
    }

    profile = init_profile(data)
    query = to_query(profile)
    print(query)
    print(profile)