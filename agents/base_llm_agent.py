from openai import OpenAI
from utils import get_yaml, get_env
from openai.types.chat import ChatCompletionUserMessageParam

class BaseLLMAgent:
    def __init__(self):
        self.config = get_yaml('config.yaml')['LLM']
        self.client = OpenAI(
            api_key=get_env()['OPENROUTER_API_KEY'],
            base_url=self.config['base_url']
        )


class ExtractionAgent(BaseLLMAgent):
    def __init__(self):
        super().__init__()
        self.prompt_config = get_yaml('prompts.yaml')

    def extract_skills(self, description: str) -> str | None:

        prompt = self.prompt_config['extraction'].format(job_description=description)

        response = self.client.chat.completions.create(
            model=self.config['llm_model'],
            messages=[
                ChatCompletionUserMessageParam(role="user", content=prompt)
            ]
        )
        return response.choices[0].message.content


class EmbeddingAgent(BaseLLMAgent):
    def get_embedding(self, description: str) -> list[float]:
        response = self.client.embeddings.create(
            model=self.config['embedding_model'],
            input=description
        )
        return response.data[0].embedding
