"""
gerar_session_string.py
Execute este script UMA VEZ no seu PC para gerar o TRADUTOR_SESSION_STRING.
Depois cole o valor gerado como variável no Railway.

Uso:
  pip install telethon
  python gerar_session_string.py
"""
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

API_ID   = 33341404
API_HASH = "7b7fcaabc8f53102411e0b822aca9098"

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    print("\n✅ SESSION_STRING gerada com sucesso!\n")
    print("Cole este valor no Railway como TRADUTOR_SESSION_STRING:")
    print("=" * 60)
    print(client.session.save())
    print("=" * 60)
