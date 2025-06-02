# pylint: disable=invalid-name
from langgraph.graph import StateGraph, END, START
from app.nodes.nodes import (
    get_assistance,
    classify,
    get_courses_metadatas,
    generate_courses_recommandation,
    classify_assistant,
    get_feedback,
    platform_assistant,
    roadmap_generation,
    get_sentiment,
    get_final_answer,
    generate_quiz,
    speech_to_text,
    text_to_speech,
    detect_language,
    get_prepare_tts,
    get_final_answer_2
)
from app.models.agent_state import AgentState
from app.models.models import Classification, AssistantClassification

def initial_router(state: AgentState):
    """
    Route based on whether the input is audio or text.
    If audio_input is present, go to speech_to_text; otherwise, proceed to detect_emotion.
    """
    print(f"🧠 Initial Router - Audio Input: {state.get('audio_input')}")
    if state.get("audio_input"):
        return "speech_to_text"
    return "detect_emotion"

def output_type_router(state: AgentState):
    """
    Route based on whether the input was audio.
    If is_audio_input is True, go to prepare_tts; otherwise, end.
    """
    print(f"🧠 Output Router State: {state}")
    if state.get("is_audio_input"):
        return "prepare_tts"
    return "generate_final_answer"

def classification_router(state: AgentState):
    classification = state["classification"].value
    if isinstance(classification, str):
        classification = Classification(classification)

    classification_map = {
        Classification.recommendation: "generate_courses_metadatas",
        Classification.assistance: "assistant_classification",
        Classification.feedback: "provide_feedback",
        Classification.platform_assistant: "platform_assistant",
        Classification.roadmap: "roadmap_generation",
        Classification.quiz: "generate_quiz"
    }

    return classification_map.get(classification, "generate_final_answer")

def feedback_router(state: AgentState):
    classification = state["classification"].value
    if isinstance(classification, str):
        classification = Classification(classification)

    if classification == Classification.roadmap:
        return "roadmap_generation"
    elif classification == Classification.recommendation:
        return "generate_courses_metadatas"

def assistant_classification_router(state: AgentState):
    classification = state["classification"].value
    if isinstance(classification, str):
        classification = AssistantClassification(classification)

    if classification == AssistantClassification.simple_assistance:
        return "provide_assistance"
    else:
        return "unhandled_assistance"

def unhandled_assistance(state: AgentState):
    return None

def create_workflow():
    workflow = StateGraph(AgentState)
    
    # Add all nodes (keeping generate_final_answer for potential future use)
    workflow.add_node("speech_to_text", speech_to_text)
    workflow.add_node("detect_emotion", get_sentiment)
    workflow.add_node("detect_language", detect_language)
    workflow.add_node("generate_quiz", generate_quiz)
    workflow.add_node("classify_query", classify)
    workflow.add_node("classification_router", classification_router)
    workflow.add_node("generate_courses_metadatas", get_courses_metadatas)
    workflow.add_node("generate_courses_recommandation", generate_courses_recommandation)
    workflow.add_node("provide_assistance", get_assistance)
    workflow.add_node("provide_feedback", get_feedback)
    workflow.add_node("platform_assistant", platform_assistant)
    workflow.add_node("assistant_classification", classify_assistant)
    workflow.add_node("unhandled_assistance", unhandled_assistance)
    workflow.add_node("roadmap_generation", roadmap_generation)
    workflow.add_node("generate_final_answer", get_final_answer_2) 
    workflow.add_node("prepare_tts", get_prepare_tts)
    workflow.add_node("text_to_speech", text_to_speech)
    
    # Conditional edges for initial routing
    workflow.add_conditional_edges(
        "detect_language",
        initial_router,
        {
            "speech_to_text": "speech_to_text",
            "detect_emotion": "detect_emotion"
        }
    )
    
    # Conditional edges for speech_to_text
    workflow.add_conditional_edges(
        "speech_to_text",
        lambda state: "detect_emotion",
        {
            "detect_emotion": "detect_emotion"
        }
    )
    
    # Conditional edges for classify_query
    workflow.add_conditional_edges(
        "classify_query",
        classification_router,
        {
            "generate_courses_metadatas": "generate_courses_metadatas",
            "assistant_classification": "assistant_classification",
            "provide_feedback": "provide_feedback",
            "platform_assistant": "platform_assistant",
            "roadmap_generation": "roadmap_generation",
            "generate_quiz": "generate_quiz"
        }
    )
    
    # Conditional edges for assistant_classification
    workflow.add_conditional_edges(
        "assistant_classification",
        assistant_classification_router,
        {
            "provide_assistance": "provide_assistance",
            "unhandled_assistance": "unhandled_assistance"
        }
    )
    
    # Conditional edges for nodes that produce output, bypassing generate_final_answer
    nodes_with_output = [
        "provide_assistance",
        "unhandled_assistance",
        "platform_assistant",
        "generate_courses_recommandation",
        "generate_quiz"
    ]
    
    for node in nodes_with_output:
        workflow.add_conditional_edges(
            node,
            output_type_router,
            {
                "prepare_tts": "prepare_tts",
                "generate_final_answer": "generate_final_answer"
            }
        )
    
    # Main workflow edges
    workflow.add_edge(START, "detect_language")
    workflow.add_edge("detect_emotion", "classify_query")
    workflow.add_edge("roadmap_generation", "generate_courses_metadatas")
    workflow.add_edge("generate_courses_metadatas", "generate_courses_recommandation")
    workflow.add_edge("provide_feedback", "classify_query")
    workflow.add_edge("prepare_tts", "text_to_speech")
    workflow.add_edge("text_to_speech", END)
    workflow.add_edge("generate_final_answer", END)
    
    
    
    app = workflow.compile()
    
    return app