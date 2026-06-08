import logging
from contextlib import contextmanager
from typing import Generator

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, String, create_engine, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from utils import get_env

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class SkillEmbeddingModel(Base):
    __tablename__ = 'skill_embeddings'

    skill_name = Column(String(255), primary_key=True)
    embedding = Column(Vector(1536), nullable=False)

    def __repr__(self) -> str:
        return f'<SkillEmbedding skill_name={self.skill_name!r}>'


class SkillEmbeddingRepository:
    def __init__(self, database_url: str):
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
    def from_env(cls) -> 'SkillEmbeddingRepository':
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

    def get_existing_skills(self, skill_names: list[str]) -> dict[str, list[float]]:
        with self._session() as session:
            results = session.scalars(
                select(SkillEmbeddingModel)
                .where(SkillEmbeddingModel.skill_name.in_(skill_names))
            ).all()
            return {r.skill_name: r.embedding.tolist() for r in results}

    def create(self, skill_name: str, vector: list[float]) -> None:
        with self._session() as session:
            stmt = insert(SkillEmbeddingModel).values(
                skill_name=skill_name,
                embedding=vector
            ).on_conflict_do_nothing(index_elements=['skill_name'])
            session.execute(stmt)
            logger.debug('Saved skill embedding: %s', skill_name)