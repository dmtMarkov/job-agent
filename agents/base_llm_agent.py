import numpy as np
from openai import OpenAI
import json

from openai.types import Embedding

from utils import get_yaml, get_env
from openai.types.chat import ChatCompletionUserMessageParam

class BaseLLMAgent:
    def __init__(self):
        self.config = get_yaml('config.yaml')['LLM']
        self.client = OpenAI(
            api_key=get_env()['OPENROUTER_API_KEY'],
            base_url=self.config['base_url']
        )


class BasePromptAgent(BaseLLMAgent):
    def __init__(self):
        super().__init__()
        self.prompt_config = get_yaml('prompts.yaml')

    def _call_llm(self, prompt: str) -> str | None:
        response = self.client.chat.completions.create(
            model=self.config['llm_model'],
            messages=[ChatCompletionUserMessageParam(role="user", content=prompt)]
        )
        return response.choices[0].message.content


class ExtractionAgent(BasePromptAgent):
    #TODO Добавить проверку схемы
    def extract_skills(self, description: str) -> str | None:
        existing_stacks = "(пока нет, создай новый)"
        #TODO Подключить существующий стек
        prompt = self.prompt_config['extraction'].format(job_description=description, existing_stacks=existing_stacks)

        return self._call_llm(prompt=prompt)


class RoleResolutionAgent(BasePromptAgent):
    def get_canonical_name_and_alias(self, title: str, roles: dict[str, list[str]]) -> tuple[str, str] | None:

        candidates_role = roles.keys()
        candidates_str = "\n".join(f"- {c}" for c in candidates_role)
        aliases_str = "\n".join(f"- {role}: {', '.join(aliases)}" for role, aliases in roles.items())
        prompt = self.prompt_config['role_resolution'].format(title=title,
                                                              candidates=candidates_str,
                                                              aliases=aliases_str)

        response = self._call_llm(prompt=prompt)

        clean = response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        if clean is None:
            return None
        else:
            data = json.loads(clean)
            return data['canonical_name'], data['alias']


class EmbeddingAgent(BaseLLMAgent):

    def _call_embedding_api(self, texts: list[str]) -> list[Embedding]:
        response = self.client.embeddings.create(
            model=self.config['embedding_model'],
            input=texts
        )
        return response.data

    def get_embedding_batch(self, texts: list[str]) -> list[list[float]]:
        response = self._call_embedding_api(texts)
        return [item.embedding for item in response]

    def get_embedding(self, description: str) -> list[float]:
        return self.get_embedding_batch([description])[0]

    @staticmethod
    def compute_role_embedding(skill_vectors: dict[str, list[float]],
                               skill_weights: dict[str, float]) -> list[float]:

        weighted_sum = np.zeros(len(next(iter(skill_vectors.values()))))

        for skill, vector in skill_vectors.items():
            weight = skill_weights.get(skill, 0.0)
            weighted_sum += np.array(vector) * weight

        norm = np.linalg.norm(weighted_sum)
        if norm == 0:
            return weighted_sum.tolist()
        return (weighted_sum / norm).tolist()