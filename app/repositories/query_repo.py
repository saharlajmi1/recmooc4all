# crud.py
from app.database.database import Query
from app.database.agent_conn import SessionLocal
from uuid import uuid4
from datetime import datetime

session = SessionLocal()
# CREATE
# CREATE
def create_query(query, response, intent, user_id, conversation_id, refined_query=None, topic=None, level=None, num_courses=None):
    new_query = Query(
        id=str(uuid4()),
        query=query,
        response=response,
        intent=intent,
        timestamp=datetime.utcnow(),
        user_id=str(user_id),
        conversation_id=str(conversation_id),
        is_deleted=False,
        refined_query=refined_query ,
        topic=topic,  
        level=level, 
        num_courses=num_courses,   
    )
    session.add(new_query)
    session.commit()
    session.refresh(new_query)
    session.close()
    return new_query


#Get query by UUID
def get_query_by_uuid(query_uuid: str):
    try:
        query = session.query(Query).filter_by(id=query_uuid, is_deleted=False).first()
        if query:
            return query
        else:
            return {"error": f"❌ No query found with UUID {query_uuid}"}
    except Exception as e:
        return {"error": f"❌ An error occurred: {str(e)}"}
    finally:
        session.close()

#UPDATE QUERY

def find_and_modify_query(query_uuid: str, new_data: dict):
    try:
        # Fetch the query by UUID (assuming UUID is stored in `id`)
        query_obj = session.query(Query).filter_by(id=query_uuid, is_deleted=False).one()
        if not query_obj:
            print(f"No query found with id {query_uuid}")
            return None
        # Modify the query text
        for key, value in new_data.items():
            if hasattr(query_obj, key): 
                setattr(query_obj, key, value)  
        session.commit()  
        session.commit()
        return query_obj  # Optionally return the updated object

    except Exception as e:
        session.rollback()
        print(f"Error updating query: {e}")
        return None

# Get queries by conversation ID
def get_queries_by_conversation_id(conversation_id: str):
    session = SessionLocal()
    try:
        queries = session.query(Query).filter_by(conversation_id=conversation_id, is_deleted=False).order_by(Query.timestamp.asc()).all()
        return queries
    except Exception as e:
        print(f"❌ Error fetching queries for conversation {conversation_id}: {str(e)}")
        return []
    finally:
        session.close()
#READ - Get all queries
def list_queries():
    queries = session.query(Query).filter_by(is_deleted=False).all()
    session.close()
    return queries


#DELETE 
def delete_query(query_uuid: str) -> bool:
    try:

        query = session.query(Query).filter_by(id=query_uuid, is_deleted=False).first()
        if query:
            query.is_deleted = True
            session.commit()
            print(f"✅ Query with UUID {query_uuid} marked as deleted.")
            return True
        else:
            print(f"❌ Query with UUID {query_uuid} not found or already deleted.")
            return False
    except Exception as e:
        session.rollback()
        print(f"❌ Error deleting query: {e}")
        return False
    finally:
        session.close()

