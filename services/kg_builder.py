from openai.types import skill

from db.repositories.role_embeddings import RoleEmbeddingRepository
from db.repositories.graph import GraphRepository
from services.skill_embedding_service import SkillEmbeddingService
from agents.role_resolution_agent import RoleResolutionAgent


class KnowledgeGraphBuilder:

    def __init__(self,
                 graph_repo: GraphRepository,
                 skill_embedding_service: SkillEmbeddingService,
                 role_embedding_repo: RoleEmbeddingRepository,
                 role_resolution_agent: RoleResolutionAgent
                 ):
        self.graph_repo = graph_repo
        self.skill_embedding_service = skill_embedding_service
        self.role_embedding_repo = role_embedding_repo
        self.role_resolution_agent = role_resolution_agent

    def resolve_role(self, title: str, skills: dict[str, str]) -> tuple[str, str] | None:
        skill_weights = {}
        for skill in skills:
            skill_weights[skill] = 1.0

        vector = self.skill_embedding_service.compute_role_embedding(skill_weights)

        candidates = self.role_embedding_repo.find_nearest(vector)
        # TODO: если candidates пустой, собрать потенциальные алиасы через LLM
        roles_with_aliases = {
            role: self.graph_repo.get_role_aliases(role)
            for role in candidates
        }

        return self.role_resolution_agent.get_canonical_name_and_alias(title, roles_with_aliases)

    def process_vacancy(self, vacancy: dict, extracted: dict) -> None:
        print(extracted.get('seniority'), extracted.get('primary_stacks'))
        canonical_name, alias = self.resolve_role(vacancy['job_title'], extracted['skills'])
        self.graph_repo.merge_role(canonical_name=canonical_name)

        if alias:
            self.graph_repo.merge_alias(canonical_name=canonical_name, alias=alias)

        stack = "+".join(sorted(extracted['primary_stacks']))
        self.graph_repo.merge_stack(canonical_name = canonical_name,
                                    name=stack,
                                    family=stack)

        self.graph_repo.merge_seniority(canonical_name=canonical_name,
                                        name=stack,
                                        level=extracted['seniority'])

        skills = [{'name': k, 'importance': v} for k, v in extracted['skills'].items()]
        self.graph_repo.merge_skill(canonical_name=canonical_name,
                                    name=stack,
                                    level=extracted['seniority'],
                                    skills=skills)

        role = self.graph_repo.get_role(canonical_name=canonical_name)
        count = role['count']

        if count < 10 or count % 50 == 0:
            skill_weights = {r['skill']: r['frequency']
                             for r in self.graph_repo.get_role_skills(canonical_name)}

            vector = self.skill_embedding_service.compute_role_embedding(skill_weights)
            if self.role_embedding_repo.is_role_exist(canonical_name):
                self.role_embedding_repo.update(canonical_name, vector)
            else:
                self.role_embedding_repo.create(canonical_name, vector)



