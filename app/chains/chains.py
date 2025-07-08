from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser,JsonOutputParser
from app.models.models import llm_json_mode, UserIntent, RecommendationRequest, Type_assistance ,Quiz,EvaluationScores
from app.prompts.prompt import (
    classification_few_shot_prompt_examples,
    feedback_prompt_template2,
    recommendation_extraction_prompt_template,
    assistant_prompt_template,
    retriever_prompt_template,
    classification_assistant_prompt_template,
    roadmap_generation_prompt_template,
    gnerate_finale_answer_prompt_template,
    quiz_template,
    language_detection_prompt_template,
    prepare_tts_prompt_template,
    generate_final_answer_prompt_template2,
    suggestion_resquest_prompt,
    quiz_level_extraction_prompt_template,
    gnerate_finale_answer_prompt_template,
    judge_template
    
    
)
# Define structured output parsers for different model outputs
llm_intent = llm_json_mode.with_structured_output(UserIntent)
llm_rec = llm_json_mode.with_structured_output(RecommendationRequest)
llm_assistance = llm_json_mode.with_structured_output(Type_assistance)
llm_quiz = llm_json_mode.with_structured_output(Quiz)
llm_eval=llm_json_mode.with_structured_output(EvaluationScores)

def get_classification_chain():
    """
    Returns a chain that classifies the user's intent.
    Uses a few-shot classification prompt and parses output into the UserIntent structure.
    """
    classification_prompt = ChatPromptTemplate.from_messages([
        ("system", classification_few_shot_prompt_examples),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("user", "{query}")
    ])
    classification_chain = classification_prompt | llm_intent
    return classification_chain

def get_language():

    language_prompt= ChatPromptTemplate.from_messages([
        ("system", language_detection_prompt_template), 
        ("user", "{query}")])
    language_chain = language_prompt | llm_json_mode | StrOutputParser()
    return language_chain


def get_roadmap_chain():
    """
    Returns a chain that generates a learning roadmap from a user's query.
    The roadmap is a list of 3 to 5 learning topics or skills.
    """
    roadmap_prompt = ChatPromptTemplate.from_messages([
        ("system", roadmap_generation_prompt_template),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("user", "{query}")
    ])
    
    roadmap_chain = roadmap_prompt | llm_json_mode |  JsonOutputParser() 
    return roadmap_chain


def get_rec_chain():
    """
    Returns a chain that extracts course recommendation parameters (e.g., topic, level, number of courses)
    from the user query and chat history. Output is structured as RecommendationRequest.
    """
    rec_prompt = ChatPromptTemplate.from_messages([
        ("system", recommendation_extraction_prompt_template),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("user", "{query}")
    ])
    rec_chain = rec_prompt | llm_rec
    return rec_chain


def get_retriever_chain():
    """
    Returns a chain that generates a  final recommendation answer
  
    """
    retriever_prompt = ChatPromptTemplate.from_messages([
        ("system", retriever_prompt_template),
       # MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("user", "{recommanded_courses}")
    ])
    retriever_chain = retriever_prompt | llm_json_mode | StrOutputParser()
    return retriever_chain


def get_feedback_chain():
    """
    Returns a chain that asks the model to reformulate or refine the user's query
    while preserving the original intent.
    """
    feedback_prompt = ChatPromptTemplate.from_messages([
        ("system", feedback_prompt_template2),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("user", """
Original Intent: {original_intent}
Last Query: {last_query}
Feedback Query: {query}
        """)
    ])
    feedback_chain = feedback_prompt | llm_json_mode | StrOutputParser()
    return feedback_chain

def get_assistant_classification_chain():
    """
    Returns a chain that classifies whether the user's query is simple or complex assistance.
    Output is structured as Type_assistance.
    """
    assistant_classification_prompt = ChatPromptTemplate.from_messages([
        ("system", classification_assistant_prompt_template),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("user", "{query}")
    ])
    assistant_classification_chain = assistant_classification_prompt | llm_assistance
    return assistant_classification_chain


def get_assistant_chain():
    """
    Returns a chain that generates an answer for  assistant queries.
    Uses an assistant prompt and outputs a plain string.
    """
    assistant_prompt = ChatPromptTemplate.from_messages([
        ("system", assistant_prompt_template),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("user", "{query}")
    ])
    assistant_chain = assistant_prompt | llm_json_mode | StrOutputParser()
    return assistant_chain



def get_finale_answer_chain():
    finale_answer_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system", gnerate_finale_answer_prompt_template),
           
            ("user", "{final_answer}"),
            ("user", "{language}"),
            ("user", "{ton}"),
            ("user", "{query}"),

        ]
    )

    finale_answer_chain = finale_answer_prompt | llm_json_mode | StrOutputParser()
    return finale_answer_chain

def get_level_extraction_chain():
    """
    Returns a chain that extracts the level of expertise from the user's query.
    Output is structured as a string representing the level.
    """
    level_extraction_prompt = ChatPromptTemplate.from_messages([
        ("system", quiz_level_extraction_prompt_template ),
        ("user", "{query}")
    ])
    level_extraction_chain = level_extraction_prompt | llm_json_mode | StrOutputParser()
    return level_extraction_chain

def get_quiz_chain():
    quiz_prompt = ChatPromptTemplate.from_messages([
    ("system", quiz_template),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    ("user", "{query}"),
    ("user", "{level}"),
    ("user", "{num_question}")])

    quiz_chain = quiz_prompt | llm_quiz 
    return quiz_chain

def get_prepare_tts_chain():
    prepare_tts_prompt = ChatPromptTemplate.from_messages([
        ("system", prepare_tts_prompt_template),
        ("user", "{final_answer}"),
        ("user", "{language}")
    ])
    prepare_tts_chain = prepare_tts_prompt | llm_json_mode | StrOutputParser()
    return prepare_tts_chain

def get_generate_final_answer_chain_2():
    generate_final_answer_prompt = ChatPromptTemplate.from_messages([
        ("system", generate_final_answer_prompt_template2),
        ("user", "{final_answer}"),
        ("user", "{language}")
    ])
    generate_final_answer_chain = generate_final_answer_prompt | llm_json_mode | StrOutputParser()
    return generate_final_answer_chain

def get_suggestion_request_chain():
    suggestion_request_prompt = ChatPromptTemplate.from_messages([
        ("system", suggestion_resquest_prompt),
        ("user", "{field_of_study}"),
        ("user", "{areas_of_interest}"),
        ("user", "{preferred_learning_style}"),
        ("user", "{knowledge_level}"),
        ("user", "{recent_queries}"),
    ])
    suggestion_request_chain = suggestion_request_prompt | llm_json_mode | StrOutputParser()
    return suggestion_request_chain


def get_llm_eval_chain():
    """
    Returns a chain that evaluates the final answer based on clarity, adaptability, relevance, language adequacy, and comment.
    Output is structured as EvaluationScores.
    """
    judge_prompt = ChatPromptTemplate.from_messages([
        ("system", judge_template),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("user", "{requete}"),
        ("user", "{reponse}"),
        ("user", "{langue}")
    ])
    
    judge_chain = judge_prompt | llm_eval
    return judge_chain
