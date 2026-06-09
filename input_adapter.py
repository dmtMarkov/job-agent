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

