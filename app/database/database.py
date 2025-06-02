# models.py
from typing import List
from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, Integer
from datetime import datetime
from app.database.agent_conn import Base , engine, SessionLocal
from sqlalchemy import ForeignKey ,asc
from sqlalchemy.orm import relationship
from langchain_core.messages import HumanMessage, AIMessage
from app.utils.utils import flatten_list
from sqlalchemy.ext.mutable import MutableList


session = SessionLocal()

class User(Base):
    __tablename__ = 'users'

    id = Column(String(36), primary_key=True)
    name = Column(String(255))
    email = Column(String(255), unique=True)
    field_of_study = Column(String(255))
    areas_of_interest = Column(String(255))
    preferred_languages = Column(String(255))
    preferred_learning_style = Column(String(255))
    knowledge_level = Column(String(255))
    interests = Column(MutableList.as_mutable(JSON), default=[])
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    queries = relationship("Query", back_populates="user", cascade="all, delete-orphan")


class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(String(36), primary_key=True)
    title = Column(String(255))
    user_id = Column(String(36), ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    is_archived = Column(Boolean, default=False)

    user = relationship("User", back_populates="conversations")
    queries = relationship("Query", back_populates="conversation", cascade="all, delete-orphan")


class Query(Base):
    __tablename__ = 'queries'
    id = Column(String(36), primary_key=True)
    query = Column(String(255))
    response = Column(Text)
    intent=Column(String(255))
    timestamp = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    refined_query = Column(String(255))
    user_id = Column(String(36), ForeignKey('users.id'))
    conversation_id = Column(String(36), ForeignKey('conversations.id'))
    topic = Column(String(255))
    level = Column(String(255))
    num_courses = Column(Integer)
    user = relationship("User", back_populates="queries")
    conversation = relationship("Conversation", back_populates="queries")
    emotion = Column(String(255))
     
    def human_message(self):
        return HumanMessage(self.query)

    def ai_message(self):
        return AIMessage(self.response if self.response else "")

    def human_ai_list(self):
        return [self.human_message(), self.ai_message()]

    def readable_list(self):
        return [{
            "role": "Human",
            "message": self.query
        },
        {
            "role": "assistant",
            "message": self.response
        }]

    @staticmethod
    def langchain_messages(Queries):
        return flatten_list([hq.human_ai_list() for hq in Queries])

    @staticmethod
    def readable_messages(Queries):
        return flatten_list([hq.readable_list() for hq in Queries])

    def recent(self, recent: int = 10) -> List['Query']:
        from app.database.agent_conn import SessionLocal  
        with SessionLocal() as db_session:
            return db_session.query(Query).filter(
            Query.conversation_id == self.conversation_id,
        ).order_by(asc(Query.timestamp)).limit(recent).all()


    
Base.metadata.create_all(engine)
