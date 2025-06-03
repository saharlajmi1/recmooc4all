from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column, Integer, String, Enum, Boolean, TIMESTAMP
)
RecBase = declarative_base()



class recmoocUser(RecBase):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    email = Column(String(200), unique=True)
    password = Column(String(200))
    age = Column(Integer)
    location = Column(String(50))
    user_picture = Column(String(255))

    educational_qualification = Column(Enum(
        'High School', 'Associate Degree', "Bachelor's Degree", 'Master\'s Degree',
        'Doctoral Degree', 'Other', name="educational_qualification_enum"
    ))

    field_of_study = Column(Enum(
        'Computer Science', 'Engineering', 'Mathematics', 'Physics', 'Biology',
        'Business', 'Arts', 'Other', name="field_of_study_enum"
    ))

    areas_of_interest = Column(Enum(
        'Technology', 'Science', 'Business', 'Arts', 'Language',
        'Healthcare', 'Other', name="areas_of_interest_enum"
    ))

    career_goals = Column(Enum(
        'Career Advancement', 'Skill Development', 'Job Change',
        'Personal Interest', 'Other', name="career_goals_enum"
    ))

    accessibility_features = Column(Enum(
        'Visual Accommodations', 'Auditory Accommodations',
        'Mobility Accommodations', 'Other', name="accessibility_features_enum"
    ))

    preferred_languages = Column(Enum(
        'English', 'Spanish', 'French', 'German', 'Mandarin', 'Other',
        name="preferred_languages_enum"
    ))

    preferred_learning_style = Column(Enum(
        'Visual', 'Auditory', 'Kinesthetic', 'Reading/Writing', 'Other',
        name="preferred_learning_style_enum"
    ))

    course_format = Column(Enum(
        'Video Lectures', 'Text-Based', 'Interactive', 'Live Sessions', 'Other',
        name="course_format_enum"
    ))

    email_verified = Column(Boolean, default=False)
    verification_token = Column(String(200))
    token_expiration = Column(TIMESTAMP)

    knowledge_level = Column(Enum(
        'Beginner', 'Intermediate', 'Advanced',
        name="knowledge_level_enum"
    ))
