import logging
from utils import get_yaml, parse_date, parse_llm_json
from parsers.local_storage import LocalStorage
from parsers.parser import Parser
from agents.base_llm_agent import ExtractionAgent, EmbeddingAgent, RoleResolutionAgent
from agents.skill_embedding_service import SkillEmbeddingService
from agents.kg_builder import KnowledgeGraphBuilder
from db.repositories.vacancies import VacanciesRepository
from db.repositories.graph import GraphRepository
from db.repositories.skill_embedding_repository import SkillEmbeddingRepository
from db.repositories.role_embeddings import RoleEmbeddingRepository

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s — %(message)s'
)
logger = logging.getLogger(__name__)


def run_pipeline():
    cfg = get_yaml('config.yaml')
    logger.info("Запуск пайплайна")

    local_storage = LocalStorage()
    parser = Parser()

    graph_repo = GraphRepository.from_env()
    graph_repo.init_schema()
    logger.info("Neo4j подключён, схема инициализирована")

    skill_embedding_repo = SkillEmbeddingRepository.from_env()
    role_embedding_repo = RoleEmbeddingRepository.from_env()
    vacancies_repo = VacanciesRepository.from_env()

    vacancies_repo.init_schema()
    skill_embedding_repo.init_schema()
    role_embedding_repo.init_schema()

    embedding_agent = EmbeddingAgent()
    role_resolution_agent = RoleResolutionAgent()

    skill_embedding_service = SkillEmbeddingService(embedding_agent, skill_embedding_repo)

    kg_builder = KnowledgeGraphBuilder(
        graph_repo=graph_repo,
        skill_embedding_service=skill_embedding_service,
        role_embedding_repo=role_embedding_repo,
        role_resolution_agent=role_resolution_agent
    )

    extraction_agent = ExtractionAgent()

    if cfg['Local']:
        data = local_storage.read()
        logger.info("Загружено %d вакансий из локального хранилища", len(data))
    else:
        data = parser.get_vacancies('AI Engineer')
        local_storage.write_raw_data(data)
        logger.info("Спаршено %d вакансий", len(data))

    success = 0
    skipped = 0

    for vacancy in data:
        job_id = vacancy['job_id']

        extracted = extraction_agent.extract_skills(description=vacancy['job_description'])
        if not extracted:
            logger.warning("Пропускаем %s — extraction вернул None", job_id)
            skipped += 1
            continue

        extracted_dict = parse_llm_json(extracted)
        if not extracted_dict:
            logger.warning("Пропускаем %s — parse_llm_json вернул None", job_id)
            skipped += 1
            continue

        if extracted_dict.get('requires_clearance'):
            logger.info("Пропускаем %s — требует clearance", vacancy['job_title'])
            continue

        if not extracted_dict.get('primary_stacks'):
            logger.info("Пропускаем %s — нет primary_stacks", vacancy['job_title'])
            continue

        kg_builder.process_vacancy(vacancy, extracted_dict)

        vacancies_repo.save_vacancy({
            'job_id': vacancy['job_id'],
            'company': vacancy.get('employer_name'),
            'country': vacancy.get('job_country'),
            'remote': vacancy.get('job_is_remote', False),
            'url': vacancy.get('job_apply_link') or vacancy.get('job_google_link', ''),
            'date_published': parse_date(vacancy.get('job_posted_at_datetime_utc')),
            'extracted_json': extracted_dict,
            'raw_json': vacancy,
        })

        logger.info("Обработана вакансия %s", job_id)
        success += 1

    logger.info("Готово — обработано: %d, пропущено: %d", success, skipped)


if __name__ == "__main__":
    run_pipeline()