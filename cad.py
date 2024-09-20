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

# RapidAPI Key và URL cho GPT-4, LLaMA 3 và DALL-E
API_KEY = "e710048e2bmshb2c56bd23b6e5c8p13c3c3jsn55207155321d"
API_HOST = "chatgpt-42.p.rapidapi.com"
GPT_API_URL = "https://chatgpt-42.p.rapidapi.com/conversationgpt4"
LLAMA_API_URL = "https://chatgpt-42.p.rapidapi.com/conversationllama3"
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
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': API_HOST,
        'Content-Type': "application/json"
    }
    
    response = requests.post(GPT_API_URL, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return data.get("result", "No response from GPT-4")
    else:
        return "Lỗi khi kết nối GPT-4"

# Hàm gọi API LLaMA 3 để nhận phản hồi
def llama3_response(message):
    payload = {
        "messages": [
            {
                "role": "user",
                "content": message
            }
        ],
        "web_access": False
    }
    
    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': API_HOST,
        'Content-Type': "application/json"
    }
    
    response = requests.post(LLAMA_API_URL, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return data.get("result", "No response from LLaMA 3")
    else:
        return "Lỗi khi kết nối LLaMA 3"

# Hàm gọi API DALL-E để tạo ảnh
def generate_image(prompt):
    payload = {
        "text": prompt,
        "width": 512,
        "height": 512
    }
    
    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': API_HOST,
        'Content-Type': "application/json"
    }
    
    response = requests.post(DALL_E_API_URL, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return data.get("generated_image")
    else:
        return None

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

        # Gửi log phản hồi GPT-4
        log_reply = f"Bot Response (GPT-4): {gpt4_reply}"
        send_log_to_bot(log_reply)

        # Phản hồi lại người dùng
        update.message.reply_text(gpt4_reply)
        
    except Exception as e:
        update.message.reply_text(f"Đã có lỗi xảy ra: {str(e)}")

# Xử lý lệnh /gen cho DALL-E (tạo ảnh)
def generate_command(update: Update, context: CallbackContext) -> None:
    try:
        if len(context.args) == 0:
            update.message.reply_text("Vui lòng nhập từ khoá cần tạo ảnh.")
            return
        
        keyword = ' '.join(context.args)

        # Gửi log tin nhắn người dùng
        log_message = f"User: {update.message.from_user.username}, Message: {keyword}"
        send_log_to_bot(log_message)

        # Gọi API DALL-E để tạo ảnh
        image_url = generate_image(keyword)

        # Gửi log phản hồi DALL-E
        log_reply = f"Bot Response (DALL-E): {image_url}"
        send_log_to_bot(log_reply)

        if image_url:
            # Phản hồi lại người dùng với link ảnh
            update.message.reply_text(f"Generation Complete! [Here]({image_url})", parse_mode=ParseMode.MARKDOWN)
        else:
            update.message.reply_text("Không thể tạo ảnh, vui lòng thử lại sau.")
    
    except Exception as e:
        update.message.reply_text(f"Đã có lỗi xảy ra: {str(e)}")

# Xử lý lệnh /ll cho API LLaMA 3
def llama_command(update: Update, context: CallbackContext) -> None:
    try:
        if len(context.args) == 0:
            update.message.reply_text("Vui lòng nhập từ khoá cần tạo phản hồi.")
            return
        
        keyword = ' '.join(context.args)

        # Gửi log tin nhắn người dùng
        log_message = f"User: {update.message.from_user.username}, Message: {keyword}"
        send_log_to_bot(log_message)

        # Gọi API LLaMA 3 để lấy phản hồi
        llama_reply = llama3_response(keyword)

        # Gửi log phản hồi LLaMA 3
        log_reply = f"Bot Response (LLaMA 3): {llama_reply}"
        send_log_to_bot(log_reply)

        # Phản hồi lại người dùng
        update.message.reply_text(llama_reply)
    
    except Exception as e:
        update.message.reply_text(f"Đã có lỗi xảy ra: {str(e)}")

# Hàm khởi tạo bot
def start_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "Chào mừng bạn đến với bot! Hãy gửi tin nhắn bất kỳ để trò chuyện hoặc sử dụng lệnh /gen để tạo ảnh, /ll để gọi API LLaMA 3."
    )

# Hàm khởi động bot
def main() -> None:
    """Khởi động bot"""
    updater = Updater(TOKEN)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("gen", generate_command))
    dispatcher.add_handler(CommandHandler("ll", llama_command))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
