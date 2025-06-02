from typing import TypedDict, Optional
from langchain_core.messages import BaseMessage
from langchain.schema import Document

class AgentState(TypedDict):
    query_uuid: str
    user_id: str
    conversation_uuid: str
    query: str
    refined_query: str
    classification: str
    roadmap: list[str]
    courses_metadatas: list[Document]
    recommanded_courses: list[Document]
    chat_history: list[BaseMessage]
    final_answer: str
    emotion: str
    audio_input: Optional[str]
    audio_output: Optional[str]
    is_audio_input: bool
    language: str
    tts_output: Optional[str]
 