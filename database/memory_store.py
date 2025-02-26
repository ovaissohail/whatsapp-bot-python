from datetime import datetime, UTC
from typing import List, Dict, Any, Optional
from pymongo.collection import Collection
from database.config import MongoDBConnection

class ConversationMemoryStore:
    def __init__(self):
        self.db = MongoDBConnection().db
        self.conversations: Collection = self.db.conversations
        self.messages: Collection = self.db.messages
        
        # Create indexes
        self.conversations.create_index("thread_id")
        self.messages.create_index([("thread_id", 1), ("timestamp", 1)])

    def create_conversation(self, thread_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        conversation = {
            "thread_id": thread_id,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "metadata": metadata or {}
        }
        result = self.conversations.insert_one(conversation)
        return str(result.inserted_id)

    def add_message(self, thread_id: str, message: Dict[str, Any]) -> str:
        message_doc = {
            "thread_id": thread_id,
            "content": message.get("content"),
            "type": message.get("type"),  # 'human', 'ai', 'system', 'tool'
            "timestamp": datetime.now(UTC),
            "metadata": message.get("metadata", {})
        }
        
        # Update conversation's last activity
        self.conversations.update_one(
            {"thread_id": thread_id},
            {"$set": {"updated_at": datetime.now(UTC)}}
        )
        
        result = self.messages.insert_one(message_doc)
        return str(result.inserted_id)

    def get_conversation_history(self, thread_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        return list(
            self.messages.find(
                {"thread_id": thread_id},
                {"_id": 0}
            ).sort("timestamp", 1).limit(limit)
        )

    def get_conversation_metadata(self, thread_id: str) -> Optional[Dict[str, Any]]:
        conversation = self.conversations.find_one({"thread_id": thread_id})
        return conversation.get("metadata") if conversation else None

    def get_conversation(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get a conversation by thread_id."""
        return self.conversations.find_one({"thread_id": thread_id})
