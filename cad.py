import logging
import json
import requests
import time
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Token của bot Telegram (DALL-E bot)
TOKEN = '5452812723:AAHwdHJSMqqb__KzcSIOdJ3QuhqsIr9YTro'

# Token của bot để gửi log
LOG_BOT_TOKEN = '5726763371:AAG7tvRAA-YOzUAKdqfYPH3zJNCrK_PFai0'
LOG_CHAT_ID = '2077786453'

# RapidAPI Key và URL cho GPT-4
GPT_API_KEY = "e710048e2bmshb2c56bd23b6e5c8p13c3jsn55207155321d"
GPT_API_HOST = "chatgpt-42.p.rapidapi.com"
GPT_API_URL = "https://chatgpt-42.p.rapidapi.com/conversationgpt4"

# RapidAPI Key và URL cho DALL-E
DALL_E_API_KEY = "e710048e2bmshb2c56bd23b6e5c8p13c3c3jsn55207155321d"
DALL_E_API_HOST = "chatgpt-42.p.rapidapi.com"
DALL_E_API_URL = "https://chatgpt-42.p.rapidapi.com/texttoimage"

# Thiết lập logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Hàm gọi API GPT-4 để nhận phản hồi
def gpt4_response(message):
    payload = {
        "messages": [
            {
                "role": "user",
                "content": message
            }
        ],
        "system_prompt": "",
        "temperature": 0.9,
        "top_k": 5,
        "top_p": 0.9,
        "max_tokens": 256,
        "web_access": False
    }
    
    headers = {
        'x-rapidapi-key': GPT_API_KEY,
        'x-rapidapi-host': GPT_API_HOST,
        'Content-Type': "application/json"
    }
    
    response = requests.post(GPT_API_URL, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return data.get("response", "No response from GPT-4")
    else:
        return "Lỗi khi kết nối GPT-4"

# Hàm gửi log về bot log qua Telegram
def send_log_to_bot(log_message):
    log_url = f"https://api.telegram.org/bot{LOG_BOT_TOKEN}/sendMessage"
    log_payload = {
        "chat_id": LOG_CHAT_ID,
        "text": log_message
    }
    requests.post(log_url, data=log_payload)

# Xử lý tin nhắn từ người dùng
def handle_message(update: Update, context: CallbackContext) -> None:
    try:
        message_text = update.message.text

        # Gửi log tin nhắn người dùng
        log_message = f"User: {update.message.from_user.username}, Message: {message_text}"
        send_log_to_bot(log_message)

        # Gọi GPT-4 để lấy phản hồi
        gpt4_reply = gpt4_response(message_text)
        
        # Phản hồi lại người dùng
        update.message.reply_text(gpt4_reply)
        
    except Exception as e:
        update.message.reply_text(f"Đã có lỗi xảy ra: {str(e)}")

# Hàm khởi tạo bot
def start_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "Chào mừng bạn đến với bot! Hãy gửi tin nhắn bất kỳ để trò chuyện."
    )

# Hàm khởi động bot
def main() -> None:
    """Khởi động bot"""
    updater = Updater(TOKEN)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
