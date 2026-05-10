import httpx
from utils import get_env, get_yaml

class Parser:
    def __init__(self):
        self.secret_cfg = get_env()
        self.cfg = get_yaml('config.yaml')['API_config']

    def _get_raw_vacancies(self, search_query):
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                self.cfg["API_params"]["API_url"],
                headers={
                    "x-rapidapi-key": self.secret_cfg["RAPIDAPI_KEY"],
                    "x-rapidapi-host": self.cfg["API_params"]["API_x-rapidapi-host"]
                },
                params={
                    "query": search_query,
                    "num_pages": self.cfg["Search_params"]["num_pages"],
                    "date_posted": self.cfg["Search_params"]["date_posted"]
                }
            )
        return response.json()

    def get_vacancies(self, search_query):
        data = self._get_raw_vacancies(search_query)
        return data["data"]




