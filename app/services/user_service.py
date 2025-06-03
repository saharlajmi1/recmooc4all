"""
This module implements the UserServiceImpl class, which provides services 
for managing user entities such as creating, updating, retrieving, and deleting users.
"""
from fastapi import HTTPException
from app.repositories.user_repo import (
    create_user,
    delete_user,
    list_users,
    get_user_by_uuid,
    find_and_modify_user,
    create_anonymous_user
)

class UserServiceImpl:
    """Service class to handle User-related operations."""

    def get_all_users(self):
        """
        Retrieve all user records.
        :return: List of all User records.
        """
        return list_users()

    def get_user_by_id(self, user_uuid: str):
        """
        Retrieve a user by UUID.
        :param user_uuid: UUID of the user.
        :return: User object or raise HTTP 404 if not found.
        """
        user = get_user_by_uuid(user_uuid)
        if isinstance(user, dict) and "error" in user:
            return None
        return user

    def create_user(self):
        """
        Create a new user record.
        :return: Created User object.
        """

        try:
           return create_user()
        except Exception as e:
          raise HTTPException(status_code=400, detail=str(e))
     
    def create_anonymous_user(self, user_id: str):
        """
       Create an anonymous user record.
       :param user_id: ID of the anonymous user.
       :return: Created User object
       """
        try:
            return create_anonymous_user(user_id)
        except Exception as e:
           raise HTTPException(status_code=400, detail=str(e))

    def update_user(self, user_uuid: str, new_data: dict, topic: str = None, level: str = None):
        """
        Update user fields by UUID.
        :param user_uuid: UUID of the user.
        :param new_data: Dict of fields to update.
        :return: Updated User object or raise HTTP 404 if not found.
        """
        updated_user = find_and_modify_user(user_uuid, new_data, topic, level)
        if not updated_user:
            raise HTTPException(status_code=404, detail="❌ User not found or update failed.")
        return updated_user

    
   
          
    def delete_user(self, user_id: str):
        """
        Delete a user by ID.
        :param user_id: ID of the user to delete.
        :return: Confirmation message or raise HTTP 404 if not found.
        """
        deleted = delete_user(user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="❌ User not found.")
        return {"message": f"✅ User with ID {user_id} deleted."}
