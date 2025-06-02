
from fastapi import APIRouter, FastAPI, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.schema.query_schema import UnifiedQuerySchema, QueryResponseSchema
from app.services.query_service import QueryServiceImpl
from app.services.conv_service import ConversationServiceImpl
from app.services.user_service import UserServiceImpl
from app.chatbot import recMooc4all
from app.utils.utils import generate_title
from app.database.synchronisation import setup_sync
from app.utils.stt_tts import test_tts_lemonfox
from typing import Optional
import os
import tempfile

app = FastAPI()

# Custom middleware to log all requests and responses
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        print(f"Incoming request: {request.method} {request.url}")
        response = await call_next(request)
        print(f"Response status: {response.status_code}, Headers: {response.headers}")
        return response

app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    print(f"HTTP exception occurred: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={"Access-Control-Allow-Origin": "http://localhost:5173"}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)},
        headers={"Access-Control-Allow-Origin": "http://localhost:5173"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    print(f"Unexpected error: {exc}")
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"},
        headers={"Access-Control-Allow-Origin": "http://localhost:5173"}
    )

router = APIRouter(prefix="/api/v2", tags=["RecMooc4All"])
query_service = QueryServiceImpl()
conversation_service = ConversationServiceImpl()
user_service = UserServiceImpl()
agent = recMooc4all()

@app.on_event("startup")
async def startup_event():
    try:
        setup_sync()
        print("✅ Synchronisation des bases de données configurée")
        print("Registered routes:", [route.path for route in app.routes])
    except Exception as e:
        print(f"❌ Erreur lors de la configuration de la synchronisation : {e}")
        raise e

async def process_query(query_text: str, user_id: str, conversation_id: Optional[str], audio_input: Optional[str] = None):
    """Shared logic to process a query (text or transcribed audio)."""
    user = user_service.get_user_by_id(user_id)
    if not user:
        user = user_service.create_anonymous_user(user_id)
        print(f"✅ Utilisateur anonyme créé : {user.id}")
    conversation = None
    if conversation_id:
        conversation = conversation_service.get_conversation(conversation_id)
    if not conversation_id or not conversation:
        conversation_title = generate_title(query_text)
        conversation = conversation_service.create_conversation(conversation_title, user_id)
        conversation_id = conversation.id
        print(f"✅ Nouvelle conversation créée : {conversation.id}")

    query = query_service.create_query(
        query=query_text,
        response=None,
        intent=None,
        user_id=user_id,
        conversation_id=conversation_id,
    )
    print("✅ Requête enregistrée")

    # Pass the query object to agent.run instead of query_text
    result = agent.run(query, audio_input=audio_input)
    print(f"✅ Réponse générée: {result}")
    response = result.get("final_answer", "⚠️ Je ne peux pas trouver la réponse à votre question")
    refined_query = result.get("refined_query", None)
    title = level = num_courses = None
    if "courses_metadatas" in result:
        metadata = result["courses_metadatas"]
        title = metadata.course_title_or_skill
        level = metadata.level.value if hasattr(metadata.level, 'value') else metadata.level
        num_courses = metadata.num_courses
        user_service.update_user(
            user_id,
            {},
            topic=title,
            level=level
        )
    updated_query = query_service.update_query(
        query.id,
        {
            "response": response,
            "intent": result.get("classification"),
            "refined_query": refined_query,
            "topic": title,
            "level": level,
            "num_courses": num_courses
        }
    )
    print("✅ Requête mise à jour")
    return {
        "query": updated_query.query,
        "response": updated_query.response,
        "intent": updated_query.intent,
        "conversation_id": updated_query.conversation_id,
        "user_id": updated_query.user_id,
        "refined_query": updated_query.refined_query,
        "topic": updated_query.topic,
        "level": updated_query.level,
        "num_courses": updated_query.num_courses,
        "audio_output": result.get("audio_output")  # Include audio_output if present
    }
@router.options("/query")
async def options_query():
    print("Handling OPTIONS for /query")
    return JSONResponse(
        status_code=200,
        content={},
        headers={
            "Access-Control-Allow-Origin": "http://localhost:5173",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )

@router.post("/query", response_model=QueryResponseSchema)
async def unified_query_endpoint(input_data: UnifiedQuerySchema = Depends()):
    print(f"Processing unified query for user_id: {input_data.user_id}")
    temp_file_path = None
    try:
        query_text = input_data.query
        if input_data.audio_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                content = await input_data.audio_file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name

            transcription = test_tts_lemonfox(temp_file_path)
            query_text = transcription.text if hasattr(transcription, 'text') else str(transcription)
            print(f"Transcribed query: {query_text}")

            if not query_text:
                raise HTTPException(
                    status_code=400,
                    detail="No valid query provided (audio transcription failed)",
                    headers={"Access-Control-Allow-Origin": "http://localhost:5173"}
                )

        if not query_text:
            raise HTTPException(
                status_code=400,
                detail="Query text is required",
                headers={"Access-Control-Allow-Origin": "http://localhost:5173"}
            )

        result = await process_query(
            query_text=query_text,
            user_id=input_data.user_id,
            conversation_id=input_data.conversation_id,
            audio_input=temp_file_path
        )

        # Check for audio_output in the result
        audio_output = result.get("audio_output")
        if audio_output and os.path.exists(audio_output):
            return FileResponse(
                audio_output,
                media_type="audio/mp3",
                headers={"Access-Control-Allow-Origin": "http://localhost:5173"}
            )
        return JSONResponse(
            content=result,
            headers={"Access-Control-Allow-Origin": "http://localhost:5173"}
        )
    except Exception as e:
        print(f"❌ Error in /query endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Internal Server Error: {str(e)}",
            headers={"Access-Control-Allow-Origin": "http://localhost:5173"}
        )
    finally:
        # Move file deletion here, after process_query
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                print(f"Deleted temporary file: {temp_file_path}")
            except Exception as e:
                print(f"Failed to delete temporary file {temp_file_path}: {e}")
@router.get("/conversations/{user_id}")
def get_user_conversations(user_id: str):
    print(f"Fetching conversations for user_id: {user_id}")
    try:
        conversations = conversation_service.get_conversations_by_user(user_id)
        result = [
            {
                "user_id": conv.user_id,
                "title": conv.title,
                "id": conv.id,
                "is_archived": conv.is_archived
            }
            for conv in conversations
        ]
        return JSONResponse(
            content=result,
            headers={"Access-Control-Allow-Origin": "http://localhost:5173"}
        )
    except Exception as e:
        print(f"Error fetching conversations: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error",
            headers={"Access-Control-Allow-Origin": "http://localhost:5173"}
        )

@router.options("/conversations/{user_id}")
async def options_conversations():
    print("Handling OPTIONS for /conversations/{user_id}")
    return JSONResponse(
        status_code=200,
        content={},
        headers={
            "Access-Control-Allow-Origin": "http://localhost:5173",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )

@router.get("/conversations/queries/{conversation_id}")
def get_conversation_queries(conversation_id: str):
    print(f"Fetching queries for conversation_id: {conversation_id}")
    try:
        queries = query_service.get_queries_by_conversation(conversation_id)
        result = [
            {
                "query": q.query,
                "response": q.response,
                "intent": q.intent,
                "timestamp": q.timestamp.isoformat(),
                "refined_query": q.refined_query,
                "topic": q.topic,
                "level": q.level,
                "num_courses": q.num_courses
            }
            for q in queries
        ]
        return JSONResponse(
            content=result,
            headers={"Access-Control-Allow-Origin": "http://localhost:5173"}
        )
    except HTTPException as e:
        print(f"HTTPException in get_conversation_queries: {e.detail}")
        raise e
    except Exception as e:
        print(f"Error fetching queries for conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error",
            headers={"Access-Control-Allow-Origin": "http://localhost:5173"}
        )

@router.options("/deleteConversation/{conversation_id}")
async def options_delete_conversation():
    print("Handling OPTIONS for /deleteConversation/{conversation_id}")
    return JSONResponse(
        status_code=200,
        content={},
        headers={
            "Access-Control-Allow-Origin": "http://localhost:5173",
            "Access-Control-Allow-Methods": "DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        }
    )

@router.delete("/deleteConversation/{conversation_id}")
def delete_conversation(conversation_id: str, user_id: str):
    print(f"Received DELETE request for conversation_id: {conversation_id}, user_id: {user_id}")
    try:
        conversation = conversation_service.get_conversation(conversation_id)
        print(f"Conversation found: {conversation.id if conversation else None}")
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
                headers={"Access-Control-Allow-Origin": "http://localhost:5173"}
            )
        if conversation.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Unauthorized: User does not own this conversation",
                headers={"Access-Control-Allow-Origin": "http://localhost:5173"}
            )
        conversation_service.delete_conversation(conversation_id)
        print(f"Conversation {conversation_id} deleted successfully")
        return JSONResponse(
            content={"message": "Conversation deleted successfully"},
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Methods": "DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            }
        )
    except HTTPException as e:
        print(f"HTTPException in delete_conversation: {e.detail}")
        raise e
    except Exception as e:
        print(f"Error deleting conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error",
            headers={"Access-Control-Allow-Origin": "http://localhost:5173"}
        )

@router.get("/quiz/pdf")
def get_quiz_pdf():
    print("Fetching quiz PDF")
    try:
        import os
        pdf_path = "quiz_output.pdf"
        if not os.path.exists(pdf_path):
            raise HTTPException(
                status_code=404,
                detail="Quiz PDF not found",
                headers={"Access-Control-Allow-Origin": "http://localhost:5173"}
            )
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            headers={"Access-Control-Allow-Origin": "http://localhost:5173"}
        )
    except Exception as e:
        print(f"Error fetching quiz PDF: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error",
            headers={"Access-Control-Allow-Origin": "http://localhost:5173"}
        )

@router.options("/quiz/pdf")
async def options_quiz_pdf():
    print("Handling OPTIONS for /quiz/pdf")
    return JSONResponse(
        status_code=200,
        content={},
        headers={
            "Access-Control-Allow-Origin": "http://localhost:5173",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )

app.include_router(router)
