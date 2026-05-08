from telethon.sync import TelegramClient
from telethon.sessions import StringSession

api_id = 33341404
api_hash = "7b7fcaabc8f53102411e0b822aca9098"

with TelegramClient(StringSession(), api_id, api_hash) as client:
    print("\nSESSION STRING:\n")
    print(client.session.save())