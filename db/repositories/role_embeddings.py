import logging
from contextlib import contextmanager
from typing import Generator

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from utils import get_env

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class RoleEmbeddingModel(Base):
    __tablename__ = 'role_embeddings'

    role_name = Column(String(255), primary_key=True)
    embedding = Column(Vector(1536), nullable=False)

    def __repr__(self) -> str:
        return f'<RoleEmbedding role_name={self.role_name!r}>'


class RoleEmbeddingRepository:
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
    def from_env(cls) -> 'RoleEmbeddingRepository':
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

    def is_role_exist(self, role_name: str) -> bool:
        with self._session() as session:
            return session.scalar(
                select(RoleEmbeddingModel)
                .where(RoleEmbeddingModel.role_name == role_name)
            ) is not None

    def get_role(self, role_name: str) -> list[float]:
        with self._session() as session:
            model = session.scalar(
                select(RoleEmbeddingModel)
                .where(RoleEmbeddingModel.role_name == role_name)
            )
            return model.embedding.tolist()

    def create(self, role_name: str, vector: list[float]) -> None:
        with self._session() as session:
            session.add(RoleEmbeddingModel(
                role_name=role_name,
                embedding=vector
            ))
            logger.debug('Saved role embedding: %s', role_name)

    def update(self, role_name: str, vector: list[float]) -> None:
        with self._session() as session:
            model = session.scalar(
                select(RoleEmbeddingModel)
                .where(RoleEmbeddingModel.role_name == role_name)
            )
            if model:
                model.embedding = vector
                logger.debug('Updated role embedding: %s', role_name)

    def find_nearest(self, vector: list[float], limit: int = 3) -> list[str]:
        #TODO Добавить trash hold
        with self._session() as session:
            results = session.scalars(
                select(RoleEmbeddingModel)
                .order_by(RoleEmbeddingModel.embedding.cosine_distance(vector))
                .limit(limit)
            ).all()
            return [r.role_name for r in results]