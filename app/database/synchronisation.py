# app/database/sync.py
from sqlalchemy import event
import uuid
from app.database.agent_conn import SessionLocal
from app.database.recmooc_conn import RecSessionLocal
from app.database.database import User
from app.database.recmoocusers import recmoocUser

def setup_sync():
    @event.listens_for(recmoocUser, 'after_insert')
    def sync_insert_to_test_users(mapper, connection, target):
        """Synchronize new user insertions from recmooc.users to test.users."""
        test_session = SessionLocal()
        try:
            # Vérifier si l'email existe déjà dans test.users
            if not test_session.query(User).filter_by(email=target.email).first():
                # Générer un UUID pour test.users
                user_id = str(uuid.uuid4())
                # Créer un nouvel utilisateur dans test.users
                new_test_user = User(
                    id=user_id,
                    name=target.name,
                    email=target.email,
                    field_of_study=target.field_of_study,
                    areas_of_interest=target.areas_of_interest,
                    preferred_languages=target.preferred_languages,
                    preferred_learning_style=target.preferred_learning_style,
                    knowledge_level=target.knowledge_level,
                    interests=[]
                )
                test_session.add(new_test_user)
                test_session.commit()
        except Exception as e:
            test_session.rollback()
            print(f"Erreur lors de la synchronisation (insert) : {e}")
            raise e
        finally:
            test_session.close()

    @event.listens_for(recmoocUser, 'after_update')
    def sync_update_to_test_users(mapper, connection, target):
        """Synchronize user updates from recmooc.users to test.users."""
        test_session = SessionLocal()
        try:
            # Trouver l'utilisateur dans test.users par email
            test_user = test_session.query(User).filter_by(email=target.email).first()
            if test_user:
                # Mettre à jour les champs communs
                test_user.name = target.name
                test_user.email = target.email
                test_user.field_of_study = target.field_of_study
                test_user.areas_of_interest = target.areas_of_interest
                test_user.preferred_languages = target.preferred_languages
                test_user.preferred_learning_style = target.preferred_learning_style
                test_user.knowledge_level = target.knowledge_level
                # interests reste inchangé ou peut être mis à jour si nécessaire
                test_user.interests = []  # Ou [target.areas_of_interest] si désiré
                test_session.commit()
            else:
                # Si l'utilisateur n'existe pas, créer un nouvel utilisateur
                user_id = str(uuid.uuid4())
                new_test_user = User(
                    id=user_id,
                    name=target.name,
                    email=target.email,
                    field_of_study=target.field_of_study,
                    areas_of_interest=target.areas_of_interest,
                    preferred_languages=target.preferred_languages,
                    preferred_learning_style=target.preferred_learning_style,
                    knowledge_level=target.knowledge_level,
                    interests=[]
                )
                test_session.add(new_test_user)
                test_session.commit()
        except Exception as e:
            test_session.rollback()
            print(f"Erreur lors de la synchronisation (update) : {e}")
            raise e
        finally:
            test_session.close()