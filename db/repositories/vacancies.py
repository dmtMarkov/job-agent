import logging
from contextlib import contextmanager
from utils import get_env
from typing import Any, Generator

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    create_engine,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Declarative mapping
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


class VacancyModel(Base):
    __tablename__ = 'vacancies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(255), unique=True, nullable=False, index=True)
    company = Column(String(255), nullable=True)
    country = Column(String(100), nullable=True)
    salary_amount = Column(Numeric(12, 2), nullable=True)
    salary_currency = Column(String(10), nullable=True)
    remote = Column(Boolean, default=False)
    language = Column(String(50), nullable=True)
    visa_sponsorship = Column(Boolean, default=False)
    date_published = Column(Date, nullable=True)
    url = Column(Text, nullable=False)
    extracted_json = Column(JSONB, default=dict)
    raw_json = Column(JSONB, default=dict)
    embedding = Column(Text, nullable=True)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=True)

    role = relationship('RoleModel', back_populates='vacancies')

    def __repr__(self) -> str:
        return f'<Vacancy job_id={self.job_id!r} company={self.company!r}>'


class RoleModel(Base):
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)

    vacancies = relationship('VacancyModel', back_populates='role')


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------

class VacanciesRepository:
    def __init__(self, database_url: str):
        self._database_url = database_url
        self._engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=2,
            max_overflow=0,
        )
        self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False)

    def init_schema(self) -> None:
        Base.metadata.create_all(self._engine)

    @classmethod
    def from_env(cls) -> 'VacanciesRepository':
        cfg = get_env()
        return cls(database_url=cfg['DATABASE_URL'])

    @contextmanager
    def _session(self) -> Generator[Session, None, None]:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            logger.exception('Session rollback due to unhandled exception')
            raise
        finally:
            session.close()

    # --- write ---

    def save_vacancy(self, vacancy: dict) -> None:
        with self._session() as session:
            existing = session.scalar(
                select(VacancyModel).where(VacancyModel.job_id == vacancy['job_id'])
            )
            if existing:
                logger.debug('Vacancy already exists, skipping: %s', vacancy['job_id'])
                return
            session.add(VacancyModel(
                job_id=vacancy.get('job_id'),
                company=vacancy.get('company'),
                country=vacancy.get('country'),
                salary_amount=vacancy.get('salary_amount'),
                salary_currency=vacancy.get('salary_currency'),
                remote=vacancy.get('remote', False),
                language=vacancy.get('language'),
                visa_sponsorship=vacancy.get('visa_sponsorship', False),
                date_published=vacancy.get('date_published'),
                url=vacancy.get('url'),
                extracted_json=vacancy.get('extracted_json', {}),
                raw_json=vacancy.get('raw_json', {}),
                embedding=vacancy.get('embedding'),
            ))
            logger.debug('Saved vacancy: %s', vacancy.get('job_id'))

    # --- read ---

    def vacancy_exists(self, job_id: str) -> bool:
        with self._session() as session:
            return session.scalar(
                select(func.count()).where(VacancyModel.job_id == job_id)
            ) > 0

    def get_vacancies_by_role(self, role_id: int) -> list[VacancyModel]:
        with self._session() as session:
            return session.scalars(
                select(VacancyModel)
                .where(VacancyModel.role_id == role_id)
                .options()  # добавь joinedload(VacancyModel.role) если нужен eager load
            ).all()