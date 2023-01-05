from datetime import timedelta

from pynamodb.attributes import TTLAttribute, UnicodeAttribute
from pynamodb.models import Model
import os


class ChatModel(Model):
    class Meta:
        table_name = os.getenv("CHAT_TABLE")
        host = os.getenv("DYNAMODB_HOST")
        region = os.getenv("REGION")

    ttl = TTLAttribute(default=timedelta(days=1))
    notification_id = UnicodeAttribute(hash_key=True)

    @staticmethod
    def lock(notification_id: str):
        try:
            ChatModel().get(hash_key=notification_id)
            return False
        except ChatModel.DoesNotExist:
            ChatModel(notification_id=notification_id).save()
            return True
