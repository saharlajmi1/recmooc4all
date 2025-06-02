from fastapi import HTTPException
from app.repositories.conv_repo import (
    create_conversation,
    delete_conversation,
    get_conversation_by_id,
    list_conversations,
    find_and_modify_conv,
    archive_conversation_by_id,
    list_conversations_by_user
)

class ConversationServiceImpl:
    """Service class to handle Conversation-related operations."""

    def get_all_conversations(self):
        """
        Retrieve all non-archived conversations.
        """
        return list_conversations()
    def get_conversations_by_user(self, user_id: str):
        """
        Retrieve all non-archived conversations for a specific user.
        """
        return list_conversations_by_user(user_id)
    def get_conversation(self, convo_id: str):
        """
        Retrieve a specific conversation by its ID.
        """
        convo = get_conversation_by_id(convo_id)
        if not convo:
            print(HTTPException(status_code=404, detail="❌ Conversation not found."))
        return convo

    def create_conversation(self, title: str, user_id: int):
        """
        Create a new conversation.
        """
        result = create_conversation(title, user_id)
        if not result:
            print(HTTPException(status_code=400, detail="❌ Failed to create conversation."))
        return result

    def update_conversation(self, convo_id: str, title: str = None, is_archived: bool = None):
        """
        Update conversation title or archive status.
        """
        result = find_and_modify_conv(convo_id, title, is_archived)
        if isinstance(result, dict) and "error" in result:
            print(HTTPException(status_code=404, detail=result["error"]))
        return result

    def delete_conversation(self, convo_id: str):
        """
        Delete a conversation by its ID.
        """
        success = delete_conversation(convo_id)
        if not success:
            print(HTTPException(status_code=404, detail="❌ Conversation not found."))
        return {"message": f"✅ Conversation with ID {convo_id} deleted."}

    def archive_conversation(self, convo_id: str):
        """
        Archive a conversation (set is_archived=True).
        """
        success = archive_conversation_by_id(convo_id)
        if not success:
            print(HTTPException(status_code=404, detail="❌ Conversation not found or already archived."))
        return {"message": f"📦 Conversation with ID {convo_id} archived successfully."}
