
"""
This module implements the QueryServiceImpl class, which provides services 
for managing query entities such as creating, updating, retrieving, and deleting queries.
"""

from fastapi import HTTPException
from app.repositories.query_repo import (
    create_query,
    get_query_by_uuid,
    find_and_modify_query,
    list_queries,
    delete_query,
    get_queries_by_conversation_id
)


class QueryServiceImpl:
    """Service class to handle Query-related operations."""

    
    def create_query(self, query: str, response: str, intent: str, user_id: int, conversation_id: int, refined_query: str = None, topic: str = None, level: str = None, num_courses: int = None):
        """
        Create a new query.

        :param query: User query text.
        :param response: Response text.
        :param intent: Intent of the query.
        :param user_id: ID of the user.
        :param conversation_id: ID of the conversation.
        :param refined_query: Optional refined version of the query.
        :return: Created Query object.
        """
        try:
            return create_query(query, response, intent, user_id, conversation_id, refined_query, topic, level, num_courses)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"❌ Error creating query: {str(e)}")
    def get_queries_by_conversation(self, conversation_id: str):
        """
        Retrieve all queries for a given conversation ID.

        :param conversation_id: ID of the conversation.
        :return: List of Query objects.
        """
        try:
            queries = get_queries_by_conversation_id(conversation_id)
            if not queries:
                raise HTTPException(status_code=404, detail=f"❌ No queries found for conversation {conversation_id}")
            return queries
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"❌ Error retrieving queries for conversation: {str(e)}")
    def update_query(self, query_uuid: str, new_data: dict):
        """
        Update a specific query by its UUID.

        :param query_uuid: UUID of the query to be updated.
        :param new_data: Dictionary containing the fields to update.
        :return: Updated Query object.
        """
        try:
            updated_query = find_and_modify_query(query_uuid, new_data)
            if not updated_query:
                raise HTTPException(status_code=404, detail="❌ Query not found or update failed.")
            return updated_query
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"❌ Error updating query: {str(e)}")

    def get_all_queries(self):
        """
        Retrieve all queries.

        :return: List of all Query records.
        """
        try:
            return list_queries()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"❌ Error retrieving queries: {str(e)}")

    def get_query(self, query_uuid: str):
        """
        Get a query by its UUID.

        :param query_uuid: UUID of the query.
        :return: Query object or raise 404.
        """
        query = get_query_by_uuid(query_uuid)
        if isinstance(query, dict) and "error" in query:
            raise HTTPException(status_code=404, detail=query["error"])
        return query

    def delete_query(self, query_uuid: str):
        """
        Delete (soft delete) a query by UUID.

        :param query_uuid: UUID of the query.
        :return: Success message.
        """
        success = delete_query(query_uuid)
        if not success:
            raise HTTPException(status_code=404, detail="❌ Query not found or already deleted.")
        return {"message": f"✅ Query with UUID {query_uuid} marked as deleted."}
