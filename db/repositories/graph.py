import logging
from contextlib import contextmanager
from typing import LiteralString

from neo4j import GraphDatabase
from utils import get_env

_CONSTRAINT_ROLE: LiteralString="""
CREATE CONSTRAINT role_name IF NOT EXISTS
FOR (r:Role) REQUIRE r.canonical_name IS UNIQUE
"""

_CONSTRAINT_SKILL: LiteralString="""
CREATE CONSTRAINT skill_name IF NOT EXISTS
FOR (s:Skill) REQUIRE s.name IS UNIQUE
"""

_MERGE_ROLE: LiteralString= """
MERGE (r:Role {canonical_name: $canonical_name})
ON CREATE SET r.aliases = $aliases,
              r.count = 1
ON MATCH SET r.count = r.count + 1,
             r.aliases = r.aliases + [a IN $aliases WHERE NOT a IN r.aliases]
SET r.embedding = $embedding
"""

_MERGE_STACK: LiteralString="""
MATCH (r:Role {canonical_name: $canonical_name})
MERGE (s:Stack {name: $name})
MERGE (r)-[u:HAS_STACK]->(s)
ON CREATE SET s.family = $family   
ON CREATE SET u.count = 1
ON MATCH SET u.count = u.count + 1
"""

_MERGE_SENIORITY: LiteralString= """
MATCH (r:Role {canonical_name: $canonical_name})-[:HAS_STACK]->(s:Stack {name: $name})
MERGE (s)-[:AT_LEVEL]->(sen:Seniority {level: $level})
ON CREATE SET sen.count = 1
ON MATCH SET sen.count = sen.count + 1
"""

_MERGE_SKILL: LiteralString="""
MATCH (r:Role {canonical_name: $canonical_name})-[:HAS_STACK]->(s:Stack {name: $name})
              -[:AT_LEVEL]->(sen:Seniority {level: $level})
UNWIND $skills AS skill
MERGE (sen)-[req:REQUIRES]->(sk:Skill {name: skill.name})
ON CREATE SET req.mention_count = 1,
              req.required_count = CASE WHEN skill.importance = 'required' THEN 1 ELSE 0 END
ON MATCH SET req.mention_count = req.mention_count + 1,
             req.required_count = req.required_count + CASE WHEN skill.importance = 'required' THEN 1 ELSE 0 END
"""

_FIND_ROLE: LiteralString="""
MATCH (r:Role {canonical_name: $canonical_name})
RETURN r
"""

_GET_ROLE_STACKS: LiteralString = """
MATCH (r:Role {canonical_name: $canonical_name})-[hs:HAS_STACK]->(s:Stack)
RETURN s.name AS name, s.family AS family, hs.count AS count
ORDER BY hs.count DESC
"""

_GET_ROLE_SKILLS: LiteralString = """
MATCH (r:Role {canonical_name: $canonical_name})-[:HAS_STACK]->(:Stack)
      -[:AT_LEVEL]->(sen:Seniority)-[req:REQUIRES]->(sk:Skill)
WITH sk.name AS skill,
     sum(req.mention_count) AS mentions,
     sum(sen.count) AS total,
     sum(req.required_count) AS required
RETURN skill,
       mentions,
       total,
       CASE WHEN total > 0 THEN toFloat(mentions) / total ELSE 0.0 END AS frequency,
       CASE WHEN mentions > 0 THEN toFloat(required) / mentions ELSE 0.0 END AS required_ratio
ORDER BY frequency DESC
"""

logger = logging.getLogger(__name__)

class GraphRepository:
    def __init__(self, uri: str, username: str, password: str):
        self._driver = GraphDatabase.driver(uri, auth=(username, password))

    @classmethod
    def from_env(cls):
        env = get_env()
        return cls(uri=env["NEO4J_URI"],
                   username=env["NEO4J_USERNAME"],
                   password=env["NEO4J_PASSWORD"]
                   )

    @contextmanager
    def _session(self):
        session = self._driver.session()
        try:
            yield session
        except Exception:
            logger.exception('Neo4j session error')
            raise
        finally:
            session.close()

    def close(self):
        self._driver.close()

    def init_schema(self):
        with self._session() as session:
            session.run(_CONSTRAINT_ROLE)
            session.run(_CONSTRAINT_SKILL)

    def merge_role(self, canonical_name, embedding, aliases):
        with self._session() as session:
            session.run(_MERGE_ROLE,
                        canonical_name=canonical_name,
                        embedding=embedding,
                        aliases=aliases)

    def merge_stack(self, canonical_name, name, family):
        with self._session() as session:
            session.run(_MERGE_STACK,
                        canonical_name=canonical_name,
                        name=name,
                        family=family)

    def merge_seniority(self, canonical_name, name, level):
        with self._session() as session:
            session.run(_MERGE_SENIORITY,
                        canonical_name=canonical_name,
                        name=name,
                        level=level)

    def merge_skill(self, canonical_name, name, level, skills):
        with self._session() as session:
            session.run(_MERGE_SKILL,
                        canonical_name=canonical_name,
                        name=name,
                        level=level,
                        skills=skills)

    def find_role_by_title(self, title):
        with self._session() as session:
            result = session.run(_FIND_ROLE,
                                canonical_name=title)
            record = result.single()
            if record is None:
                return None
            return dict(record["r"])

    def get_role_skills(self, canonical_name):
        with self._session() as session:
            result = session.run(_GET_ROLE_SKILLS,
                                 canonical_name=canonical_name)
            return [dict(record) for record in result]

    def get_role_stacks(self, canonical_name):
        with self._session() as session:
            result = session.run(_GET_ROLE_STACKS,
                                 canonical_name=canonical_name)
            return [dict(record) for record in result]


