from sqlalchemy import Column, String, DateTime, Text, Integer
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    keycloak_id = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    roles = Column(Text, default="[]")  # JSON array as string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_roles(self) -> list[str]:
        import json
        try:
            return json.loads(self.roles)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_roles(self, roles: list[str]) -> None:
        import json
        self.roles = json.dumps(roles)


class AgentConfig(Base):
    __tablename__ = "agent_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    config_data = Column(Text, nullable=False)  # JSON config
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)