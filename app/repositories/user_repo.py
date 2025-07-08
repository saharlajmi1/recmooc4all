# crud.py
from app.database.database import User,Query

from sqlalchemy import desc

from app.database.agent_conn import SessionLocal
from app.database.recmooc_conn import RecSessionLocal
from app.database.recmoocusers import recmoocUser
from uuid import uuid4
# CREATE
session = SessionLocal()

def create_user():
    rec_session = RecSessionLocal()
    test_session = SessionLocal()

    try:
        rec_users = rec_session.query(recmoocUser).all()

        for rec_user in rec_users:
            exists = test_session.query(User).filter_by(email=rec_user.email).first()
            if exists:
                continue

            new_user = User(
                id=str(uuid4()),
                name=rec_user.name,
                email=rec_user.email,
                field_of_study=rec_user.field_of_study,
                areas_of_interest=rec_user.areas_of_interest,
                preferred_languages=rec_user.preferred_languages,
                preferred_learning_style=rec_user.preferred_learning_style,
                knowledge_level=rec_user.knowledge_level,
                interests=[]
            )
            test_session.add(new_user)

        test_session.commit()
        print("✅ Synchronisation terminée.")

    except Exception as e:
        test_session.rollback()
        print(f"❌ Erreur: {e}")

    finally:
        rec_session.close()
        test_session.close()
# CREATE USER anonyme
def create_anonymous_user(user_id: str):
    test_session = SessionLocal()
    """
    Crée un utilisateur anonyme avec l'ID fourni.
    :param user_id: ID fourni (UUID string)
    :param session: Session SQLAlchemy
    :return: L'objet User créé
    """
    try:
        anonymous_user = User(
            id=user_id,
            name=f"anonymous_{user_id[:6]}",
            email=None,
            field_of_study=None,
            areas_of_interest=None,
            preferred_languages=None,
            preferred_learning_style=None,
            knowledge_level=None,
            interests=[]
        )
        test_session.add(anonymous_user)
        test_session.commit()
        print(f"✅ Utilisateur anonyme {anonymous_user.name} créé.")
        return anonymous_user

    except Exception as e:
        session.rollback()
        print(f"❌ Erreur lors de la création de l'utilisateur anonyme : {e}")
        raise e
# GET USER BY UUID
def get_user_by_uuid(user_uuid: str):
    try:
        session = SessionLocal()
        user = session.query(User).filter_by(id=user_uuid).first()
        if user:
            return user
        else:
            return {"error": f"❌ No user found with UUID {user_uuid}"}
    except Exception as e:
        return {"error": f"❌ An error occurred: {str(e)}"}
    finally:
        session.close()

#UPDATE USER

def find_and_modify_user(user_id: str, new_data: dict, topic: str = None, level: str = None):
    try:
        user = session.query(User).filter_by(id=user_id).first()

        if not user:
            print(f"❌ No user found with id {user_id}")
            return None

        # Mettre à jour les champs standards
        for key, value in new_data.items():
            if key != "interests" and hasattr(user, key):
                setattr(user, key, value)

        # Mettre à jour les intérêts s'ils sont fournis
        if topic and level:
            new_interest = {"title": topic, "level": level}

            if user.interests is None:
                user.interests = []

            if new_interest not in user.interests:
                user.interests.append(new_interest)

        session.commit()
        print(f"✅ User {user_id} updated successfully.")
        return user

    except Exception as e:
        session.rollback()
        print(f"❌ Error updating user: {e}")
        return None


# READ
def list_users():
    session = SessionLocal()
    users = session.query(User).all()
    session.close()
    return users


#DELETE USER
def delete_user(user_id: int) -> bool:
    with SessionLocal() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            session.delete(user)
            session.commit()
            print(f"✅ User with ID {user_id} deleted.")
            return True
        else:
            print(f"❌ User with ID {user_id} not found.")
            return False

def get_user_by_mail(email: str):
    try:
        session = SessionLocal()
        user = session.query(User).filter_by(email=email).first()
        if user:
            return user
        else:
            return {"error": f"❌ No user found with email {email}"}
    except Exception as e:
        return {"error": f"❌ An error occurred: {str(e)}"}
    finally:
        session.close()


def get_user_data_for_prompt(user_id: str):
    session = SessionLocal()

    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return None, ""

        recent_queries = session.query(Query).filter(
            Query.user_id == user_id,
            Query.is_deleted == False
        ).order_by(desc(Query.timestamp)).limit(5).all()

        recent_queries_str = "\n".join([f"- {q.query}" for q in recent_queries]) or ""

        return user, recent_queries_str

    except Exception as e:
        print(f"❌ Error fetching user data for prompt: {e}")
        return None, ""

    finally:
        session.close()
