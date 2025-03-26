from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage
import requests
import discord
import asyncio
import os

app = Flask(__name__)

# LINE 設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
LINE_USER_ID = os.getenv('LINE_TO_USER_ID')
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Discord 設定
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Flask 路由設定
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except Exception as e:
        print("Webhook Error:", e)
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    user_id = event.source.user_id
    print(user_id)
    requests.post(os.getenv('DISCORD_WEBHOOK_URL'), json={
        "content": f"{text}"
    })

# 推送 LINE 訊息的函式
def send_line_message(text):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    body = {
        "to": LINE_USER_ID,
        "messages": [{
            "type": "text",
            "text": text
        }]
    }
    r = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=body)
    print("LINE 推送結果：", r.status_code)

# Discord 事件設定
@client.event
async def on_ready():
    print(f'已登入 Discord bot: {client.user}')

@client.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.name == "general":  # 根據你要監聽的頻道調整
        text = f"[Discord] {message.author.name}: {message.content}"
        send_line_message(text)

# 同時執行 Flask 和 Discord Bot
import threading

def run_flask():
    app.run(host='0.0.0.0', port=10000)

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

client.run(DISCORD_TOKEN)
