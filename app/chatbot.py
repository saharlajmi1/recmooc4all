from app.workflow.workflow import create_workflow
from app.database.database import Query
from app.services.query_service import QueryServiceImpl
from typing import Optional
from langfuse.callback import CallbackHandler

query_service = QueryServiceImpl()
langfuse_handler = CallbackHandler(
    public_key="pk-lf-9fbe65cf-d6ae-4744-b0b0-e614661bbcb8",
    secret_key="sk-lf-10adbbf6-da4e-43b9-b72f-005270f29a62",
    host="https://cloud.langfuse.com"
)


class recMooc4all:
    def __init__(self):
        self.chatbot = create_workflow()

    def run(self, query: Query, audio_input: Optional[str] = None):
        chat_history = Query.langchain_messages(query.recent())
        print("---" * 50)
        print("chat history", chat_history)
        print("---" * 50)

        try:
            result = self.chatbot.invoke({
                "query": query.query,
                "chat_history": chat_history,
                "conversation_uuid": query.conversation_id,
                "user_id": query.user_id,
                "audio_input": audio_input  # Pass audio_input to workflow
            }, config={"callbacks": [langfuse_handler]})
            return result
        except Exception as e:
            print("❌ Error in chatbot invocation:", e)
            return None
   
