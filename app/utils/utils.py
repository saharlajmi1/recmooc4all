from typing import List, Union
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
load_dotenv()
import re

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
def flatten_list(input_list: List[Union[str, List[str]]]) -> List[str]:
    result = []
    for item in input_list:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, list):
            result.extend(item)
    return result

import ast

def generate_roadmap_output(roadmap_steps, topic) -> str:
    """
    Génère un texte étape par étape pour devenir un expert dans un domaine donné.
    Chaque étape contient un titre et les cours associés à cette étape, incluant la description (Headline).
    """
    output = [f"Here are the steps to learn {topic}:\n"]

    for step in roadmap_steps:
        step_number = step["step"]
        step_topic = step["topic"]
        courses = step["courses"]

        # Add step header
        output.append(f"Step {step_number}: {step_topic}")
        output.append("Courses:")

        # Format each course
        for course in courses:
            # Safely parse category_title and Level
            try:
                categories = ast.literal_eval(course.get("category_title", "[]")) if course.get("category_title") else []
                levels = ast.literal_eval(course.get("Level", "[]")) if course.get("Level") else []
            except (ValueError, SyntaxError):
                categories, levels = [], []

            # Handle the Headline
            headline = course.get("Headline", "")
            description_lines = []
            if headline:
                keywords = [k.strip() for k in headline.split(",") if k.strip()]
                if keywords:
                    description_lines.append("    - description:")
                    for keyword in keywords:
                        description_lines.append(f"      - {keyword}")
                else:
                    description_lines.append("    - description: No description available")
            else:
                description_lines.append("    - description: No description available")

            # Format course details
            course_details = [
                f"  - {course.get('Title', 'Titre inconnu')}",
                f"    - category: {', '.join(categories) if categories else ''}",
                f"    - level: {', '.join(levels) if levels else ''}",
                f"    - URL: {course.get('URL', '')}"
            ] + description_lines

            output.extend(course_details)

        # Add a blank line after each step
        output.append("")

    # Join all lines with newlines
    return "\n".join(output)


from transformers import pipeline

# Charger le pipeline d’analyse d’émotions
emotion_classifier = pipeline("text-classification", 
                              model="j-hartmann/emotion-english-distilroberta-base", 
                              return_all_scores=True)



# Fonction d’analyse
def detect_emotion(text):
    results = emotion_classifier(text)[0]
    results = sorted(results, key=lambda x: x['score'], reverse=True)
    top_emotion = results[0]['label']

    # Mapping personnalisé si tu veux d'autres noms
    emotion_map = {
        "anger": "angry",
        "disgust": "frustrated",
        "fear": "scared",
        "joy": "happy",
        "neutral": "neutral",
        "sadness": "sad",
        "surprise": "confused"
    }

    return emotion_map.get(top_emotion, "neutral")  # default = neutral

def get_tone_from_emotion(emotion: str) -> str:
    tone_map = {
        "confused": "educational and reassuring",
        "scared": "soothing and supportive",
        "angry": "calm and understanding",
        "sad": "encouraging and positive",
        "frustrated": "clear and motivating",
        "happy": "enthusiastic and warm",
        "neutral": "informative and professional"
    }
    return tone_map.get(emotion, "neutral")



def format_courses_list(courses, topic) -> str:
    output = f" Here are the recommended courses to learn {topic}:\n\n"
    for i, course in enumerate(courses, 1):
        output += f" {i}. {course.get('Title', 'Titre inconnu')}\n"
        output += f"- category: {', '.join(eval(course.get('category_title', '[]')))}\n"
        output += f"- level: {', '.join(eval(course.get('Level', '[]')))}\n"
        output += f"- URL: {course.get('URL', 'URL indisponible')}\n"
        # Handle the Headline
        headline = course.get('Headline', '')
        keywords = [k.strip() for k in headline.split(',')]
        output += f"- description: {', '.join(keywords)}\n"
   
        output += "\n"
    return output


def generate_title(query: str) -> str:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    prompt = f"generate a short and simple  title  from the user query : {query}"
    messages = [HumanMessage(content=prompt)]
    response = llm.invoke(messages)
    return response.content.strip()


def format_code_block(code):
    """Préprocesse le code pour préserver l'indentation et les retours à la ligne."""
    lines = code.split('\n')
    formatted_lines = []
    for line in lines:
        leading_spaces = len(line) - len(line.lstrip(' '))
        formatted_line = ' ' * leading_spaces + line.lstrip(' ')
        formatted_lines.append(formatted_line)
    return '<br/>'.join(formatted_lines)

def render_quiz_to_pdf(questions, filename="quiz_output.pdf", title="Quiz Document"):
    # Configuration du document
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=18,
        spaceAfter=20,
        alignment=1,  # Centré
        textColor=colors.darkblue
    )
    
    question_style = ParagraphStyle(
        'Question',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=8,
        leading=14,
        fontName='Helvetica-Bold'
    )
    
    code_style = ParagraphStyle(
        'Code',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=11,
        spaceBefore=8,
        spaceAfter=8,
        leading=14,
        leftIndent=1*cm,
        backColor=colors.lightgrey,
        borderPadding=5
    )
    
    choice_style = ParagraphStyle(
        'Choice',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=4,
        leading=12,
        leftIndent=1*cm
    )
    
    answer_style = ParagraphStyle(
        'Answer',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        leading=12,
        textColor=colors.green
    )
    
    # Contenu du document
    elements = []
    
    # En-tête
    elements.append(Paragraph(title, title_style))
    elements.append(Paragraph(
        f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        styles['Italic']
    ))
    elements.append(Spacer(1, 0.5*cm))
    
    # Questions
    for idx, q in enumerate(questions, 1):
        # Utiliser une regex pour trouver tous les blocs de code
        # Cette regex capture le texte avant, le langage, le code, et le texte après
        pattern = r'(.*?)(?:```(\w+)\n(.*?)\n```|$)(.*)'
        remaining_text = q.question
        question_started = False
        
        while remaining_text:
            match = re.match(pattern, remaining_text, re.DOTALL)
            if not match:
                # Aucun bloc de code trouvé ou fin de la chaîne
                if remaining_text.strip():
                    if not question_started:
                        elements.append(Paragraph(f"Q{idx}: {remaining_text.strip()}", question_style))
                    else:
                        elements.append(Paragraph(remaining_text.strip(), question_style))
                break
            
            # Extraire les parties
            before_text, language, code, after_text = match.groups()
            
            # Texte avant le bloc de code
            if before_text.strip():
                if not question_started:
                    elements.append(Paragraph(f"Q{idx}: {before_text.strip()}", question_style))
                    question_started = True
                else:
                    elements.append(Paragraph(before_text.strip(), question_style))
            
            # Bloc de code
            if language and code:
                formatted_code = format_code_block(code.strip())
                elements.append(Paragraph(formatted_code, code_style))
            
            # Continuer avec le texte restant
            remaining_text = after_text
        
        # Choix
        for choice in q.choices:
            elements.append(Paragraph(f"• {choice}", choice_style))
        
        elements.append(Spacer(1, 0.3*cm))
    
    # Saut de page avant les réponses
    elements.append(PageBreak())
    
    # Page des réponses
    elements.append(Paragraph("Correct Answers", title_style))
    elements.append(Spacer(1, 0.3*cm))
    
    for idx, q in enumerate(questions, 1):
        elements.append(Paragraph(f"Q{idx}: {q.correct_answer}", answer_style))
    
    # Fonction pour ajouter le numéro de page et l'en-tête
    def add_page_number(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        page_number = f"Page {doc.page}"
        canvas.drawCentredString(A4[0]/2, 1*cm, page_number)
        
        # En-tête sur chaque page
        canvas.setFont('Helvetica-Bold', 12)
        canvas.setFillColor(colors.darkblue)
        canvas.drawString(2*cm, A4[1] - 1.5*cm, title)
        canvas.restoreState()
    
    # Construction du PDF
    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)


