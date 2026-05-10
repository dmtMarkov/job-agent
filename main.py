from utils import get_yaml, parse_date, parse_llm_json
from parsers.local_storage import LocalStorage
from parsers.parser import Parser
from agents.base_llm_agent import ExtractionAgent, EmbeddingAgent
from db.repositories.vacancies import save_vacancy, vacancy_exists

def run_pipeline():
    cfg = get_yaml('config.yaml')

    local_storage = LocalStorage()
    parser = Parser()

    if cfg['Local']:
        data = local_storage.read()
    else:
        data = parser.get_vacancies('CV')
        local_storage.write_raw_data(data)


    extraction_agent = ExtractionAgent()
    embedding_agent = EmbeddingAgent()
    for vacancy in data:
        job_id = vacancy['job_id']

        if vacancy_exists(job_id):
            continue

        extracted = extraction_agent.extract_skills(description=vacancy['job_description'])
        if not extracted:
            print(f"Пропускаем {job_id} — extraction вернул None")
            continue
        extracted_dict = parse_llm_json(extracted)
        skills_text = ", ".join(extracted_dict["skills"].keys())
        embedding = embedding_agent.get_embedding(skills_text)

        local_storage.write_processed(vacancy, extracted_dict, embedding)

        save_vacancy({
            "job_id": job_id,
            "company": vacancy.get("employer_name"),
            "country": vacancy.get("job_country"),
            "remote": vacancy.get("job_is_remote"),
            "date_published": parse_date(vacancy.get("job_posted_at_timestamp")),
            "url": vacancy.get("job_apply_link"),
            "extracted_json": extracted_dict,
            "embedding": embedding,
            "raw_json": vacancy
        })


        print(f"Save vacancy {job_id}")

if __name__ == "__main__":
    run_pipeline()