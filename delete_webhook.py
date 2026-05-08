import requests

TOKEN = "8361643236:AAG0amRx5YJGvy8vRWjTBxTZpmrTY6foNok"
url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=true"
response = requests.get(url)
print(response.json())