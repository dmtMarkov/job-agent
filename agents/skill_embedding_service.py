import re
import logging
from agents.base_llm_agent import EmbeddingAgent
from db.repositories.skill_embedding_repository import SkillEmbeddingRepository

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s — %(message)s'
)

class SkillEmbeddingService:
    def __init__(self, embedding_agent: EmbeddingAgent, skill_repository: SkillEmbeddingRepository):
        self.embedding_agent = embedding_agent
        self.skill_repo = skill_repository

    @staticmethod
    def _normalize_skill(skill_name: str) -> str:
        skill = skill_name.lower()
        skill = re.sub(r'\(.*?\)', '', skill).strip()
        skill = skill.replace('_', ' ')
        skill = re.sub(r'\s+', ' ', skill).strip()
        return skill

    def compute_role_embedding(self, skill_weights: dict[str, float]) -> list[float]:
        skill_names = [self._normalize_skill(s) for s in skill_weights.keys()]

        existing = self.skill_repo.get_existing_skills(skill_names)

        new_skills = [s for s in skill_names if s not in existing]
        if new_skills:
            vectors = self.embedding_agent.get_embedding_batch(new_skills)
            for skill, vector in zip(new_skills, vectors):
                self.skill_repo.create(skill, vector)
                existing[skill] = vector

        normalized_weights = {self._normalize_skill(s): w for s, w in skill_weights.items()}

        return EmbeddingAgent.compute_role_embedding(existing, normalized_weights)
