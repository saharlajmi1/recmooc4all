
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# local_llm = "llama3.2:3b"
# llm = OllamaLLM(model=local_llm, temperature=0)
# llm_json_mode = OllamaLLM(model=local_llm, temperature=0, format="json")

llm_json_mode = ChatOpenAI(streaming=True,model="gpt-4o-mini", temperature=0)


class Classification(str, Enum):
    assistance = "assistance"
    recommendation = "recommendation"
    feedback = "feedback"
    platform_assistant = "platform_assistant"
    roadmap = "roadmap"
    quiz = "quiz"

class AssistantClassification(str, Enum):
    simple_assistance = "simple assistance"
    complex_assistance = "complex assistance"
 
class Type_assistance(BaseModel):
    classification: AssistantClassification = Field(
        description=(
            "The type of user request:\n"
            "- 'simple assistance': user asks for help with a simple task\n"
            "- 'complex assistance': user asks for help with a complex task\n"
        )
    )
class UserIntent(BaseModel):
    classification: Classification = Field(
        description=(
            "The type of user request:\n"
            "- 'recommendation': user asks for course recommendation\n"
            "- 'feedback': user clarifies or corrects a previous recommendation\n"
            "- 'assistance': any other general question\n"
            "- 'platform_assistant': user asks for help with the platform\n"
            "- 'roadmap': user asks for a learning roadmap\n"
            "- 'quiz': user asks for quiz questions\n"
        )
    )

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class CourseLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"

class FieldOfStudy(str, Enum):
    computer_science = "Computer Science"
    engineering = "Engineering"
    mathematics = "Mathematics"
    physics = "Physics"
    biology = "Biology"
    business = "Business"
    arts = "Arts"
    other = "Other"

class PreferredLearningStyle(str, Enum):
    visual = "Visual"
    auditory = "Auditory"
    kinesthetic = "Kinesthetic"
    reading_writing = "Reading/Writing"
    other = "Other"

class PreferredLanguage(str, Enum):
    english = "English"
    spanish = "Spanish"
    french = "French"
    german = "German"
    mandarin = "Mandarin"
    other = "Other"


class RecommendationRequest(BaseModel):
    course_title_or_skill: Optional[str] = Field(
        description="The course title or skill area the user is interested in, e.g., 'python for beginners', 'data science'"
    )
    level: Optional[CourseLevel] = Field(
        description="The desired level of the course if mentioned: beginner, intermediate, or advanced. return beginner if not specified."
    )
    num_courses: Optional[int] = Field(
        description="The number of courses the user wants, between 1 and 10. Defaults to 5 if not mentioned.",
    )
    field_of_study: Optional[FieldOfStudy] = Field(
      
        description="The user's field of study, if mentioned. Should be one of the predefined values."
    )
    preferred_languages: Optional[PreferredLanguage] = Field(
        #default=PreferredLanguage.english,
        description="The user's preferred language. Defaults to English if not specified."
    )
    preferred_learning_style: Optional[PreferredLearningStyle] = Field(
       # default=None,
        description="The user's preferred learning style, if mentioned."
    )


class Question(BaseModel):
    question: str = Field(description="The quiz question text")
    choices: list[str] = Field(description="List of answer choices")
    correct_answer: str = Field(description="The correct answer from the choices")

class Quiz(BaseModel):
     questions: list[Question] = Field(description="List of quiz questions")
