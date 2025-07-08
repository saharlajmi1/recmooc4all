from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from app.schema.query_schema import UnifiedQuerySchema, QueryResponseSchema
from app.services.query_service import QueryServiceImpl
from app.services.conv_service import ConversationServiceImpl
from app.services.user_service import UserServiceImpl
from app.database.database import Query
from app.chatbot import recMooc4all
from sqlalchemy import asc
from app.utils.utils import generate_title
from app.utils.redis_cache import embed_context, search_in_cache, save_to_cache
from app.utils.stt_tts import test_tts_lemonfox
from typing import Optional
from app.repositories.user_repo import get_user_data_for_prompt
import tempfile, os, logging
from app.nodes.nodes import get_suggestion_request, generate_quiz_level_recommendation
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


# def parse_choices(choices_str):
#     """
#     Parse string representation of a list of choices safely.
#     Example: "list = [1, 2, 3]" or "['choice1', 'choice2']"
#     """
#     try:
#         parsed = ast.literal_eval("[" + choices_str + "]") or ast.literal_eval("(" + choices_str + ")") or ast.literal_eval("{" + choices_str + "}") or  ast.literal_eval("<" + choices_str + ">") 
#         return [str(c).strip() for c in parsed]
#     except Exception as e:
#         return [c.strip().strip("'\"") for c in choices_str.split(',')]

# def parse_quiz_string(quiz_string: str) -> dict:
#     question_pattern = r"Question\(question='(.*?)', choices=\[(.*?)\], correct_answer='(.*?)'\)"
#     matches = re.findall(question_pattern, quiz_string, re.DOTALL)

#     questions = []
#     for question, choices_str, correct_answer in matches:
#         choices = parse_choices(choices_str)
#         questions.append({
#             "question": question,
#             "choices": choices,
#             "correct_answer": correct_answer
#         })
#     return {"questions": questions}

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
    chat_history = Query.langchain_messages(query.recent())
    print(f"📝 Historique de la conversation: {chat_history}")
    
    contextual_query, new_embedding = embed_context(chat_history, query_text)
    cached_response, similarity, cached_intent = search_in_cache(new_embedding)
    print(f"🔍 Similarité trouvée: {similarity:.2f} pour la requête '{query_text}'")
    
    if cached_response:
        updated_query = query_service.update_query(query.id, {
            "response": cached_response,
            "intent": cached_intent or "cached",  # Fallback to "cached" for legacy entries
        })
        print(f"✅ Cache HIT! Similarité: {similarity:.2f}")
        return {
            "query": query_text,
            "response": cached_response,
            "intent": cached_intent or "cached",  # Fallback to "cached" for legacy entries
            "conversation_id": conversation_id,
            "user_id": user_id,
            "refined_query": query_text,
            "topic": None,
            "level": None,
            "num_courses": None,
            "audio_output": None,
            "final_answer": cached_response,
        }

    result = agent.run(query, audio_input=audio_input)

    metadata = result.get("courses_metadatas")
    title = getattr(metadata, 'course_title_or_skill', None) if metadata else None
    level = getattr(metadata.level, 'value', None) if metadata and hasattr(metadata, 'level') else result.get("level", None)
    num_courses = getattr(metadata, 'num_courses', None) if metadata else None

    if result.get("classification") == "quiz":
        quiz_raw = result.get("final_answer")
        
        final_answer = {
                "questions": [
                    {
                        "question": q.question,
                        "choices": q.choices,
                        "correct_answer": q.correct_answer
                    } for q in quiz_raw.questions
                ]
            }
        response_to_store = json.dumps(final_answer)
    else:
        final_answer = result.get("final_answer", "⚠️ Unable to find an answer")
        response_to_store = final_answer if isinstance(final_answer, str) else json.dumps(final_answer)

    save_to_cache(contextual_query, new_embedding, response_to_store, result.get("classification"))
    user_service.update_user(user_id, {}, topic=title, level=level)
    updated_query = query_service.update_query(query.id, {
        "response": result.get("final_answer", "⚠️ Unable to find an answer"),
        "intent": result.get("classification"),
        "refined_query": result.get("refined_query"),
        "topic": title,
        "level": level,
        "num_courses": num_courses
    })
    evaluation = result.get("evaluation", None)
    if evaluation is not None:
        # Convert Pydantic model to dict if needed
        if hasattr(evaluation, "model_dump"):  # Pydantic v2+
            result["evaluation"] = evaluation.model_dump()
        elif hasattr(evaluation, "dict"):      # Pydantic v1
            result["evaluation"] = evaluation.dict()
        else:
            result["evaluation"] = dict(evaluation)


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
        "final_answer": final_answer,
        "evaluation": result.get("evaluation", None)
    }
# Existing endpoints remain unchanged
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

@router.post("/generate-suggestions/{user_id}")
async def generate_suggestions(user_id: str):
    user, recent_queries = get_user_data_for_prompt(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    field_of_study = user.field_of_study 
    areas_of_interest = user.areas_of_interest 
    preferred_learning_style = user.preferred_learning_style 
    knowledge_level = user.knowledge_level 
    suggestions = get_suggestion_request(
        field_of_study=field_of_study,
        areas_of_interest=areas_of_interest,
        preferred_learning_style=preferred_learning_style,
        knowledge_level=knowledge_level,
        recent_queries=recent_queries
    )
    print(suggestions)
    if isinstance(suggestions, str):
        suggestions = [
            item.strip() for item in suggestions.split('\n')
            if item.strip() and item.strip().startswith(tuple(f"{i}." for i in range(1, 10)))
        ]
        suggestions = [item.replace(f"{i}.", "").strip() for i, item in enumerate(suggestions, 1)]
    return {"suggestions": suggestions}


@router.post("/quiz/level-recommendation")
async def quiz_level_recommendation_endpoint(
    user_id: str = Form(...),
    conversation_id: Optional[str] = Form(None),
    score_percentage: float = Form(...)
):
    """
    Génère une recommandation basée sur le score en pourcentage du quiz.
    """
    try:
        logger.info(f"Processing quiz level recommendation: user_id={user_id}, conversation_id={conversation_id}, score_percentage={score_percentage}")
        result = generate_quiz_level_recommendation(score_percentage, user_id, conversation_id)
        # Stocker la recommandation comme une query
        # query = query_service.create_query(
        #     query="Recommandation basée sur le score du quiz",
        #     response=result["recommendation"],
        #     intent="quiz_recommendation",
        #     user_id=user_id,
        #     conversation_id=conversation_id,
        #     level=result["level"]
        # )
        return JSONResponse(content={
            "recommendation": result["recommendation"],
            "level": result["level"],
           
            "user_id": user_id
        })
    except Exception as e:
        logger.error(f"Erreur lors de la génération de la recommandation : {e}")
        raise HTTPException(status_code=500, detail="Échec de la génération de la recommandation")