from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from app.schema.query_schema import UnifiedQuerySchema, QueryResponseSchema
from app.services.query_service import QueryServiceImpl
from app.services.conv_service import ConversationServiceImpl
from app.services.user_service import UserServiceImpl
from app.chatbot import recMooc4all
from app.utils.utils import generate_title
from app.utils.stt_tts import test_tts_lemonfox
from typing import Optional
import tempfile, os, logging
from uuid import uuid4
import re
import json
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2", tags=["RecMooc4All"])

query_service = QueryServiceImpl()
conversation_service = ConversationServiceImpl()
user_service = UserServiceImpl()
agent = recMooc4all()
import ast

def parse_choices(choices_str):
    """
    Parse string representation of a list of choices safely.
    Example: "list = [1, 2, 3]" or "['choice1', 'choice2']"
    """
    
    try:
       
        parsed = ast.literal_eval("[" + choices_str + "]") or ast.literal_eval("(" + choices_str + ")") or ast.literal_eval("{" + choices_str + "}")
        
        return [str(c).strip() for c in parsed]
    except Exception as e:
        
        return [c.strip().strip("'\"") for c in choices_str.split(',')]




def parse_quiz_string(quiz_string: str) -> dict:
    question_pattern = r"Question\(question='(.*?)', choices=\[(.*?)\], correct_answer='(.*?)'\)"
    matches = re.findall(question_pattern, quiz_string, re.DOTALL)
    
    questions = []
    for question, choices_str, correct_answer in matches:
        choices = parse_choices(choices_str)
        questions.append({
            "question": question,
            "choices": choices,
            "correct_answer": correct_answer
        })
    return {"questions": questions}

async def process_query(query_text: str, user_id: str, conversation_id: Optional[str], audio_input: Optional[str] = None):
    user = user_service.get_user_by_id(user_id)
    if not user:
        user = user_service.create_anonymous_user(str(uuid4()))

    conversation = conversation_service.get_conversation(conversation_id) if conversation_id else None
    if not conversation:
        conversation_title = generate_title(query_text)
        conversation = conversation_service.create_conversation(conversation_title, user_id)
        conversation_id = conversation.id

    query = query_service.create_query(query=query_text, response=None, intent=None, user_id=user_id, conversation_id=conversation_id)
    result = agent.run(query, audio_input=audio_input)

    metadata = result.get("courses_metadatas")
    title = getattr(metadata, 'course_title_or_skill', None) if metadata else None
    level = getattr(metadata.level, 'value', None) if metadata and hasattr(metadata, 'level') else None
    num_courses = getattr(metadata, 'num_courses', None) if metadata else None

    # --------- Correction ici pour gérer string Quiz(...) ---------
    
    if result.get("classification") == "quiz":
         quiz_raw = result.get("final_answer")
         if isinstance(quiz_raw, str):
            final_answer = parse_quiz_string(quiz_raw)
         else:
            final_answer = {
            "questions": [
                {
                    "question": q.question,
                    "choices":  q.choices,
                    "correct_answer": q.correct_answer
                } for q in quiz_raw.questions
            ]
        }
    # ➔ On prépare aussi le champ `response` sous forme JSON (string propre)
         response_to_store = json.dumps(final_answer)
         
    else:
              final_answer = result.get("final_answer", "⚠️ Unable to find an answer")
              response_to_store = final_answer if isinstance(final_answer, str) else json.dumps(final_answer)
              

 
    print("the resonse is",response_to_store)

    user_service.update_user(user_id, {}, topic=title, level=level)

    updated_query = query_service.update_query(query.id, {
        "response": result.get("final_answer", "⚠️ Unable to find an answer"),
        "intent": result.get("classification"),
        "refined_query": result.get("refined_query"),
        "topic": title,
        "level": level,
        "num_courses": num_courses
    })

    return {
        "query": updated_query.query,
        "response": response_to_store,
        "intent": updated_query.intent,
        "conversation_id": updated_query.conversation_id,
        "user_id": updated_query.user_id,
        "refined_query": updated_query.refined_query,
        "topic": updated_query.topic,
        "level": updated_query.level,
        "num_courses": updated_query.num_courses,
        "audio_output": result.get("audio_output"),
        "final_answer": final_answer  # ajoute ici si besoin dans la réponse JSON
    }
# ---------------- Routes ------------------



@router.post("/query", response_model=QueryResponseSchema)
async def unified_query_endpoint(
    query: Optional[str] = Form(None),
    user_id: str = Form(...),
    conversation_id: Optional[str] = Form(None),
    audio_file: Optional[UploadFile] = File(None)
):
    temp_file_path = None
    try:
        logger.info(f"Extracted: query_text={query}, user_id={user_id}, conversation_id={conversation_id}, audio_file={audio_file}")

        if audio_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                content = await audio_file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name

            transcription = test_tts_lemonfox(temp_file_path)
            query = transcription.text if hasattr(transcription, 'text') else str(transcription)

            if not query:
                raise HTTPException(status_code=400, detail="No valid query provided (audio transcription failed)")

        if not query:
            raise HTTPException(status_code=400, detail="Query text is required")

        result = await process_query(query, user_id, conversation_id, audio_input=temp_file_path)

        if result.get("audio_output") and os.path.exists(result["audio_output"]):
            return FileResponse(result["audio_output"], media_type="audio/mp3")

        return JSONResponse(content=result)

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


@router.post("/login")
async def login_endpoint(email: str = Form(...)):
    user = user_service.get_user_by_mail(email)
    if not user :  
        raise HTTPException(status_code=400, detail="Invalid email or password")
    return JSONResponse(content={"user_id": user.id})

@router.post("/guest")
async def guest_login():
    user_id = str(uuid4())
    user_service.create_anonymous_user(user_id)
    return JSONResponse(content={"user_id": user_id})

@router.get("/conversations/{user_id}")
def get_user_conversations(user_id: str):
    conversations = conversation_service.get_conversations_by_user(user_id)
    return [
        {"user_id": conv.user_id, "title": conv.title, "id": conv.id, "is_archived": conv.is_archived}
        for conv in conversations
    ]


@router.get("/conversations/queries/{conversation_id}")
def get_conversation_queries(conversation_id: str):
    queries = query_service.get_queries_by_conversation(conversation_id)
    return [
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


@router.delete("/deleteConversation/{conversation_id}")
def delete_conversation(conversation_id: str, user_id: str):
    conversation = conversation_service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conversation.user_id != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized: User does not own this conversation")
    conversation_service.delete_conversation(conversation_id)
    return {"message": "Conversation deleted successfully"}


@router.get("/quiz/pdf")
def get_quiz_pdf():
    pdf_path = "quiz_output.pdf"
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Quiz PDF not found")
    return FileResponse(pdf_path, media_type="application/pdf")


@router.get("/audio")
def get_audio():
    audio_path = "speech.mp3"
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(audio_path, media_type="audio/mp3")    
