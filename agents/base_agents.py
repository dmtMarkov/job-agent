from openai import OpenAI

from utils import get_yaml, get_env

class BaseLLMAgent:
    def __init__(self, model_key: str = 'llm_model'):
        self.config = get_yaml('config.yaml')['LLM']
        self.client = OpenAI(
            api_key=get_env()['OPENROUTER_API_KEY'],
            base_url=self.config['base_url']
        )
        self.model = self.config[model_key]

    


class BasePromptAgent(BaseLLMAgent):
    def __init__(self, model_key: str = 'llm_model'):
        super().__init__(model_key=model_key)
        self.prompt_config = get_yaml('prompts.yaml')

    def _call_llm(
            self,
            prompt: str,
            system: str | None = None,
            history: list[dict] | None = None,
            ) -> str | None:
        messages = []

        if system:
            messages.append({"role": "system", "content": system})

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )
        return response.choices[0].message.content
