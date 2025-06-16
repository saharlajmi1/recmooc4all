from app.chains.chains import get_finale_answer_chain,get_roadmap_chain,get_classification_chain, get_rec_chain, get_assistant_chain, get_retriever_chain, get_feedback_chain, get_assistant_classification_chain,get_quiz_chain,get_language, get_prepare_tts_chain,get_generate_final_answer_chain_2
from app.models.agent_state import AgentState
from app.vector_db.retrieve_courses import search_courses
from app.vector_db.retrieve_FAQ import serach_response
from app.utils.decorator import log_execution
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.utils.utils import format_courses_list,generate_roadmap_output,detect_emotion,get_tone_from_emotion,render_quiz_to_pdf
from app.services.user_service import UserServiceImpl
from app.models.models import Classification
from app.database.database import Query
from app.utils.stt_tts import test_tts_lemonfox,generate_tts


@log_execution
def classify(state: AgentState) -> AgentState:
    """
    Classify the user query using a classification chain.
    Adds the classification result to the agent state.
    """
    classification = get_classification_chain().invoke({"query": state["query"], "chat_history": state["chat_history"]})
    print(f"🧠 Classification: {classification.classification}")
    return {
        **state,
        "classification": classification.classification,
    }

@log_execution
def detect_language(state: AgentState) -> AgentState:
    """
    Detect the language of the user's query using a language detection chain.
    Adds the detected language to the agent state.
    """
    language = get_language().invoke({"query": state["query"]})
    print(f"🧠 Detected Language: {language}")
    return {
        **state,
        "language": language  
    }

def get_sentiment(state: AgentState) -> AgentState:
    """
    Analyze the sentiment of the user's query using a sentiment analysis chain.
    Adds the sentiment result to the agent state.
    """
    emotion=detect_emotion(state["query"])
    print(f"🧠 Sentiment: {emotion}")
    return {
        **state,
        "emotion": emotion  
    }

@log_execution
def roadmap_generation(state: AgentState) -> AgentState:
    """
    Generate a learning roadmap based on the user's query.
    Adds the roadmap to the agent state.
    """
    roadmap = get_roadmap_chain().invoke({"query": state["query"], "chat_history": state["chat_history"]})
    print(f"🧠 Roadmap: {roadmap}")
    return {
        **state,
        "roadmap": roadmap  
    }

@log_execution
def get_courses_metadatas(state: AgentState) -> AgentState:
    """
    Extract metadata (e.g., topic, level, number of courses) from the query
    using a recommendation chain. Adds metadata to agent state.
    """
    courses_metadatas = get_rec_chain().invoke({"query": state["query"], "chat_history": state["chat_history"]})
    
    if courses_metadatas.course_title_or_skill is None:
        from app.database.agent_conn import SessionLocal
        from sqlalchemy import asc
        conversation_id = state["conversation_uuid"]
        with SessionLocal() as db_session:
            last_intent_query = db_session.query(Query).filter(
            Query.conversation_id == conversation_id,
            Query.intent.in_(["recommendation", "roadmap"]),
            Query.is_deleted == False
            ).order_by(asc(Query.timestamp)).first()
        courses_metadatas.course_title_or_skill = last_intent_query.topic if last_intent_query else None


    print(f"🧠 Courses Metadatas: {courses_metadatas}")
    return {
        **state,
        "courses_metadatas": courses_metadatas  
    }


@log_execution
def generate_courses_recommandation(state: AgentState) -> AgentState:
    import traceback
    import requests

    def get_user_if_exists(user_id):
        if user_id:
            user_service = UserServiceImpl()
            user = user_service.get_user_by_id(user_uuid=user_id)
            print(f"🧠 User: {user.id}")
            return user
        return None

    def enrich_data_from_user(user, fallback):
        return {
            "knowledge_level": fallback["desired_level"] or getattr(user, "knowledge_level", None),
            "field_of_study": fallback["topic"] or getattr(user, "field_of_study", None),
            "preferred_languages": fallback["preferred_languages"] or getattr(user, "preferred_languages", None),
            "preferred_learning_style": fallback["preferred_learning_style"] or getattr(user, "preferred_learning_style", None),
            "areas_of_interest": fallback["topic"] or getattr(user, "areas_of_interest", None)
            #ajouter type d'handicap
        }

    def fetch_recommander_sys_courses(topic_entry, user_profile):
        print(f"[THREAD-{topic_entry}] 🔍 Started fetching courses")
        payload = {
            **user_profile,
            "areas_of_interest": topic_entry
        }
        try:
            response = requests.post("http://localhost:8000/recommend", json=payload)
            response.raise_for_status()
            courses = response.json().get("recommended_moocs", [])
        except Exception as e:
            print(f"❌ Error for topic '{topic_entry}': {e}")
            traceback.print_exc()
            courses = []
        print(f"[THREAD-{topic_entry}] ✅ Got {len(courses)} courses")
        return topic_entry, courses

    def fetch_local_courses(topic_entry, level):
        print(f"[THREAD-{topic_entry}] 🔍 Started fetching local courses")
        courses = search_courses(topic_entry, k=5, level_filter=level)
        print(f"[THREAD-{topic_entry}] ✅ Found {len(courses)} courses locally")
        return topic_entry, courses

    def build_roadmap(topics, fetch_fn):
        roadmaps = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(fetch_fn, topic) for topic in topics]
            
            for i, (topic, future) in enumerate(zip(topics, futures), 1):
                topic_entry, courses = future.result()
                print(f"📦 Step {i} done: {topic_entry} → {len(courses)} courses")
                roadmaps.append({
                    "step": i,
                    "topic": topic_entry,
                    "courses": courses
                })
        
        return generate_roadmap_output(roadmaps, topics)

    def get_general_recommendations(payload):
        print("➡️ Calling /recommend for general recommendation...")
        try:
            response = requests.post("http://localhost:8000/recommend", json=payload)
            response.raise_for_status()
            courses = response.json().get("recommended_moocs", [])
            print(f"✅ Found {len(courses)} courses")
            return format_courses_list(courses,topic)
        except Exception as e:
            print(f"❌ Recommendation error: {e}")
            traceback.print_exc()
            return []

    # --- Main logic begins here ---
    query = state["query"]
    user_id = state["user_id"]
    courses_metadatas = state["courses_metadatas"]
    classification = state["classification"]

    # Extract metadata
    desired_level = courses_metadatas.level
    num_courses = courses_metadatas.num_courses
    field_of_study = courses_metadatas.field_of_study
    preferred_languages = courses_metadatas.preferred_languages
    preferred_learning_style = courses_metadatas.preferred_learning_style

    topic = courses_metadatas.course_title_or_skill
   


    user = get_user_if_exists(user_id)
    recommended_courses = []

    if user and getattr(user, "email", None):
        print("✅ User info retrieved from DB")
        user_profile = enrich_data_from_user(user, {
            "desired_level": desired_level,
            "topic": topic,
            "preferred_languages": preferred_languages,
            "preferred_learning_style": preferred_learning_style,
           

        })

        if classification == Classification.roadmap and state.get("roadmap"):
            print("🚀 Fetching roadmap recommendations (remote)")
            recommended_courses = build_roadmap(state["roadmap"], lambda t: fetch_recommander_sys_courses(t, user_profile))
            

        elif classification == Classification.recommendation:
            recommended_courses = get_general_recommendations(user_profile)
          

    else:
        print("🔒 No user info found: fallback to local search")

        if classification == Classification.roadmap and state.get("roadmap"):
            print("🚀 Fetching roadmap recommendations (local)")
            recommended_courses = build_roadmap(state["roadmap"], lambda t: fetch_local_courses(t, desired_level))
            

        elif classification == Classification.recommendation:
            print(f"🧠 Local search on topic: {topic}")
            recommended_courses = search_courses(topic, k=num_courses, level_filter=desired_level)
            recommended_courses = format_courses_list(recommended_courses, topic)
            print(f"✅ Found {len(recommended_courses)} local recommendations")

    return {
        **state,
        "final_answer": recommended_courses
    }


# @log_execution
# def get_final_recommandation(state: AgentState) -> AgentState:
#     """
#     Finalize the recommended courses using a retriever chain.
#     Returns a polished answer to the user with the refined results.
#     """
#     final_retrieved_courses = get_retriever_chain().invoke({
#         "recommanded_courses": state["recommanded_courses"]
#         #"chat_history": state["chat_history"]
#     })
#     return {
#         **state,
#         "final_answer": final_retrieved_courses
#     }
@log_execution
def get_feedback(state: AgentState) -> AgentState:
    """
    Request feedback from a dedicated chain to refine the user query.
    Updates both 'query' and 'refined_query' in the agent state.
    """
    from app.database.agent_conn import SessionLocal
    from sqlalchemy import asc

    conversation_id = state["conversation_uuid"]

    # Retrieve the last Query object with recommendation or roadmap intent from the database
    with SessionLocal() as db_session:
        last_intent_query = db_session.query(Query).filter(
            Query.conversation_id == conversation_id,
            Query.intent.in_(["recommendation", "roadmap"]),
            Query.is_deleted == False
        ).order_by(asc(Query.timestamp)).first()

    # Extract intent and query from the Query object
    original_intent = last_intent_query.intent
    last_query = last_intent_query.query 

    # Invoke the feedback chain with the correct context
    feedback = get_feedback_chain().invoke({
        "query": state["query"],
        "chat_history": state["chat_history"],
        "original_intent": original_intent,
        "last_query": last_query
    })
    print(f"🧠 Feedback: {feedback}")
    return {
        **state,
        "refined_query": feedback,
        "query": feedback
    }
@log_execution
def classify_assistant(state: AgentState) -> AgentState:
    """
    Classify the user's query to determine the type of assistant.
    Uses a dedicated assistant classification chain.
    """
    classification_assistance = get_assistant_classification_chain().invoke({
        "query": state["query"], 
        "chat_history": state["chat_history"]
    })
    print(f"🧠 Classification retournée: {classification_assistance.classification}")
    return {
        **state,
        "classification": classification_assistance.classification,
    }
@log_execution
def platform_assistant(state: AgentState) -> AgentState:
    """
    Answer platform-related queries using FAQ vector search.
    Searches for a response in a knowledge base and adds it to the state.
    """
    assistance = serach_response(state["query"])
    return {
        **state,
        "final_answer": assistance  
    }
@log_execution
def get_assistance(state: AgentState) -> AgentState:
    """
    Provide general assistant support using an assistant chain.
    Generates an answer based on the query and chat history.
    """
    assistance = get_assistant_chain().invoke({
        "query": state["query"], 
        "chat_history": state["chat_history"]
    }) 
    return {
        **state,
        "final_answer": assistance  
    }
@log_execution
def get_final_answer(state: AgentState) -> AgentState:
    """
    Finalize the answer to the user query.
    This is a placeholder function that can be extended in the future.

    """
    ton=get_tone_from_emotion(state["emotion"])
    answer = state["final_answer"]
    print(f"🧠 Final answer: {answer}")
    final_answer = get_finale_answer_chain().invoke({"final_answer": answer, "ton":ton, "query": state["query"]})
    return {
        **state,
        "final_answer": final_answer
    }

@log_execution
def generate_quiz(state: AgentState) -> AgentState:
    from app.database.agent_conn import SessionLocal
    from app.database.database import Query
    from sqlalchemy import asc
   

    conversation_id = state["conversation_uuid"]
    with SessionLocal() as db_session:
        last_intent_query = db_session.query(Query).filter(
            Query.conversation_id == conversation_id,
            Query.intent.in_(["recommendation", "roadmap"]),
            Query.is_deleted == False
        ).order_by(asc(Query.timestamp)).first()


    if last_intent_query and last_intent_query.level:
        level = last_intent_query.level
    else:
        level = "Débutant"

    print(f"🧠 Level: {level}")

    num_questions = 6
    quiz = get_quiz_chain().invoke({
        "num_question": num_questions,
        "query": state["query"],
        "chat_history": state["chat_history"],
        "level": level
    })

    print(f"Quiz: {quiz}")
    questions = quiz.questions

    render_quiz_to_pdf(questions, filename="quiz_output.pdf", title="Quiz Document")

    return {
        **state,
        "final_answer": quiz
    }
   
@log_execution
def speech_to_text(state: AgentState) -> AgentState:
    """
    Convert speech to text using the Whisper model if audio_input is provided.
    Updates the query field with the transcribed text and clears audio_input to prevent looping.
    """
    print(f"🧠 Speech to Text - Audio Input: {state.get('audio_input')}")
    if state.get("audio_input"):
        resultat = test_tts_lemonfox(state["audio_input"])
        query_text = resultat.text if hasattr(resultat, 'text') else str(resultat)
        print(f"🧠 Transcription: {query_text}")
        return {
            **state,
            "query": query_text,
            "is_audio_input": True,
            "audio_input": None  # Clear audio_input to prevent looping
        }
    print("🧠 No audio input, skipping transcription")
    return state
@log_execution
def text_to_speech(state: AgentState) -> AgentState:
    """
    Convert text to speech using the Lemonfox TTS service.
    Returns the audio file path.
    """
    if state.get("final_answer"):
        language = state.get("language")
        audio_path = generate_tts(state["tts_output"],language)
        return {
            **state,
            "audio_output": audio_path,
        }

@log_execution
def get_prepare_tts(state: AgentState) -> AgentState:
    """
    Prepare the text-to-speech chain.
    This function is a placeholder for future TTS preparation logic.
    """
    prepare_tts = get_prepare_tts_chain().invoke({
        "final_answer": state["final_answer"], "language": state["language"]
    })
    return {
        **state,
        "tts_output": prepare_tts
        
       
    }

@log_execution
def get_final_answer_2(state: AgentState) -> AgentState:
    """
    Finalize the answer to the user query using a different chain.
    This is a placeholder function that can be extended in the future.
    """
    
    final_answer = get_generate_final_answer_chain_2().invoke({"final_answer": state["final_answer"], "language":state["language"]})
    return {
        **state,
        "final_answer": final_answer
    }
