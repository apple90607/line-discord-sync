from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage
import requests
import discord
import asyncio
import os
import re


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
    print("LINE 回傳狀態：", r.status_code)
    print("LINE 回傳內容：", r.text)

# Discord 事件設定
@client.event
async def on_ready():
    print(f'已登入 Discord bot: {client.user}')

@client.event
async def on_message(message):
    print("收到訊息：", message.content)  # 加這行
    if message.author.bot:
        return
    if message.channel.name == "ㄚㄚㄚㄚㄚㄚㄚㄚㄚ":  # 根據你要監聽的頻道調整
        messages = convert_discord_emoji_to_line_messages(
            f"[Discord] {message.author.display_name}: {message.content}"
        )
        send_line_multi_messages(messages)

# 同時執行 Flask 和 Discord Bot
import threading

def convert_discord_emoji_to_line_messages(text):
    # 抓出自訂 emoji 例如 <:cat:123456789012345678>
    pattern = r'<:(.*?):(\d+)>'
    matches = re.findall(pattern, text)
    messages = []

    # 將文字中移除自訂 emoji
    cleaned_text = re.sub(pattern, '', text).strip()
    if cleaned_text:
        messages.append({"type": "text", "text": cleaned_text})

    # 每個自訂 emoji 轉換成圖片訊息
    for name, emoji_id in matches:
        emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.png"
        messages.append({
            "type": "image",
            "originalContentUrl": emoji_url,
            "previewImageUrl": emoji_url
        })

    return messages

def send_line_multi_messages(messages):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    body = {
        "to": LINE_USER_ID,
        "messages": messages[:5]  # LINE 一次最多只能推送 5 則
    }
    r = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=body)
    print("LINE 圖文訊息狀態：", r.status_code)
    print("LINE 回應內容：", r.text)


def run_flask():
    app.run(host='0.0.0.0', port=10000)

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

client.run(DISCORD_TOKEN)
