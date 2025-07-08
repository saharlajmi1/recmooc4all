# judge_module.py

from sqlalchemy import Column, Integer, Text, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from app.database.agent_conn import Base , engine, SessionLocal

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI 
from langchain_core.output_parsers import StrOutputParser,JsonOutputParser
from pydantic import BaseModel, Field

# 1️⃣ Définition du modèle SQLAlchemy
session = SessionLocal()


class LogEntry(Base):
    __tablename__ = 'logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    requete = Column(Text, nullable=False)
    reponse = Column(Text, nullable=False)
    judgement = Column(JSON, nullable=False)  
    created_at = Column(DateTime, default=datetime.utcnow)

# Crée la table si elle n'existe pas encore
Base.metadata.create_all(bind=engine)
print("✅ Table 'logs' vérifiée/créée avec succès.")

# -------------------------------------------------------
# 2️⃣ Prompt du juge
judge_template = """
Tu es un évaluateur expert et impartial.
Voici la requête utilisateur : "{requete}"
Voici la réponse générée : "{reponse}"
Langue détectée : "{langue}"

Donne une note de 1 à 5 pour :
- clarity : clarté et compréhension
- adaptability : adaptation à l'intention de la requête
- relevance : pertinence et utilité
- language_adequacy : respect et fluidité dans la langue détectée

Ajoute aussi un petit commentaire général.

Réponds seulement sous ce format JSON :
{{
  "clarity": int,
  "adaptability": int,
  "relevance": int,
  "language_adequacy": int,
  "comment": "string"
}}
"""

# -------------------------------------------------------
# 3️⃣ Modèle Pydantic pour parser la sortie JSON
class EvaluationScores(BaseModel):
    clarity: int = Field(..., ge=1, le=5)
    adaptability: int = Field(..., ge=1, le=5)
    relevance: int = Field(..., ge=1, le=5)
    language_adequacy: int = Field(..., ge=1, le=5)
    comment: str

# -------------------------------------------------------
# 4️⃣ Chaîne LangChain
def get_judge_chain():
    prompt = ChatPromptTemplate.from_template(judge_template)
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
    parser = JsonOutputParser(pydantic=EvaluationScores)
    return prompt | llm | parser

judge_chain = get_judge_chain()

# -------------------------------------------------------
# 5️⃣ Nœud LangGraph (ou simple fonction) pour juger
def judge_answer_node(state):
    """
    state doit être un dict avec :
    - 'query': requête utilisateur
    - 'final_answer': réponse générée
    - 'language': langue détectée
    """
    evaluation = judge_chain.invoke({
        "requete": state['query'],
        "reponse": state['final_answer'],
        "langue": state['language']
    })
    state['evaluation'] = evaluation # ajoute au state
    return state

# -------------------------------------------------------
# 6️⃣ Insertion dans la base

def save_log(requete, reponse, judgement):
    """
    judgement est un dict JSON {clarity, adaptability, relevance, language_adequacy, comment}
    """
    session = SessionLocal()
    try:
        log_entry = LogEntry(
            requete=requete,
            reponse=reponse,
            judgement=judgement
        )
        session.add(log_entry)
        session.commit()
        print(f"✅ Log ajouté avec ID {log_entry.id}")
    except Exception as e:
        session.rollback()
        print(f"❌ Erreur lors de l'insertion : {e}")
    finally:
        session.close()

# -------------------------------------------------------
# 7️⃣ Exemple d’utilisation complète
if __name__ == "__main__":
    # Exemple de requête et réponse
    state = {
        'query': "Peux-tu me recommander un cours Python pour débutant ?",
        'final_answer': "Bien sûr ! Voici trois cours Python pour débutant disponibles sur Coursera et Udemy...",
        'language': "fr"
    }

    # Appel du nœud d'évaluation
    new_state = judge_answer_node(state)

    # Insertion dans la base
    save_log(
        requete=new_state['query'],
        reponse=new_state['final_answer'],
        judgement=new_state['evaluation']
    )

    print("🌟 Évaluation et insertion terminées avec succès.")
