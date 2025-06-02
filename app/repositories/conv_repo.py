# crud_conversation.py
from datetime import datetime
from app.database.database import Conversation
from app.database.agent_conn import SessionLocal
from datetime import datetime
from uuid import uuid4

session = SessionLocal()
# CREATE
def create_conversation(title: str, user_id: int):
    try:
        new_convo = Conversation(
            id = uuid4(),
            title=title,
            user_id=user_id,
            created_at=datetime.utcnow(),
            is_archived=False
        )
        session.add(new_convo)
        session.commit()
        session.refresh(new_convo)
        return new_convo

    except Exception as e:
        session.rollback()
        print(f"error : ❌ Failed to create conversation: {str(e)}")
        return None

    finally:
        session.close()

def find_and_modify_conv(conv_uuid: str, new_data: dict):
    try:
        # Fetch the conv by UUID (assuming UUID is stored in `id`)
        conv_obj = session.query(Conversation).filter_by(id=conv_uuid, is_deleted=False).one()
        if not conv_obj:
            print(f"No conv found with id {conv_uuid}")
            return None
        # Modify the conv text
        for key, value in new_data.items():
            if hasattr(conv_obj, key): 
                setattr(conv_obj, key, value)  
        session.commit()  
        session.commit()
        return conv_obj  # Optionally return the updated object

    except Exception as e:
        session.rollback()
        print(f"Error updating conv: {e}")
        return None
# READ - List conversations by user ID
def list_conversations_by_user(user_id: str):
    session = SessionLocal()
    try:
        conversations = session.query(Conversation).filter_by(user_id=user_id, is_archived=False).all()
        return conversations
    except Exception as e:
        print(f"❌ Error fetching conversations for user {user_id}: {str(e)}")
        return []
    finally:
        session.close()

# READ - Get all conversations
def list_conversations():
    session = SessionLocal()
    try:
        conversations = session.query(Conversation).all()
        return conversations
    finally:
        session.close()

# READ - All non-archived conversations
def list_conversations():
    session = SessionLocal()
    try:
        conversations = session.query(Conversation).filter_by(is_archived=False).all()
        return conversations
    finally:
        session.close()


# READ - Get conversation by ID
def get_conversation_by_id(convo_id: int):
    session = SessionLocal()
    try:
        return session.query(Conversation).filter(Conversation.id == convo_id).first()
    finally:
        session.close()

# ARCHIVE - Set is_archived=True
def archive_conversation_by_id(convo_id: str) -> bool:
    session = SessionLocal()
    try:
        convo = session.query(Conversation).filter_by(id=convo_id, is_archived=False).first()
        if convo:
            convo.is_archived = True
            session.commit()
            print(f"📦 Conversation with ID {convo_id} archived successfully.")
            return True
        else:
            print(f"❌ No conversation found to archive with ID {convo_id}.")
            return False
    except Exception as e:
        session.rollback()
        print(f"❌ Error archiving conversation: {str(e)}")
        return False
    finally:
        session.close()
# DELETE
def delete_conversation(convo_id: str) -> bool:
    session = SessionLocal()
    try:
        convo = session.query(Conversation).filter(Conversation.id == convo_id).first()
        if convo:
            convo.is_archived = True
            session.commit()
            print(f"✅ Conversation with ID {convo_id} archived.")
            return True
        else:
            print(f"❌ Conversation with ID {convo_id} not found.")
            return False
    except Exception as e:
        session.rollback()
        print(f"❌ Error archiving conversation: {str(e)}")
        return False
    finally:
        session.close()
