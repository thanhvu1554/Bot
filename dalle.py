import logging
import json
import requests
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackContext

# Token của bot Telegram
TOKEN = '5452812723:AAHwdHJSMqqb__KzcSIOdJ3QuhqsIr9YTro'

# RapidAPI Key và URL
API_KEY = "e710048e2bmshb2c56bd23b6e5c8p13c3c3jsn55207155321d"
API_HOST = "chatgpt-42.p.rapidapi.com"
API_URL = "https://chatgpt-42.p.rapidapi.com/texttoimage"

# Thiết lập logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Hàm gọi API DALL-E để sinh ảnh
def generate_image(prompt):
    payload = json.dumps({
        "text": prompt,
        "width": 512,
        "height": 512
    })
    
    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': API_HOST,
        'Content-Type': "application/json"
    }
    
    response = requests.post(API_URL, data=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        # Giả định rằng đường link ảnh nằm trong trường 'url' của response
        return data.get("url")
    else:
        return None

# Xử lý lệnh /gen
def generate_command(update: Update, context: CallbackContext) -> None:
    try:
        # Lấy từ khoá từ câu lệnh
        if len(context.args) == 0:
            update.message.reply_text("Vui lòng nhập từ khoá cần tạo ảnh.")
            return
        
        keyword = ' '.join(context.args)
        
        # Gọi hàm generate_image để sinh ảnh
        image_url = generate_image(keyword)
        
        if image_url:
            # Trả về kết quả với đường link ảnh
            update.message.reply_text(f"Generation Complete! [Here]({image_url})", parse_mode=ParseMode.MARKDOWN)
        else:
            update.message.reply_text("Không thể tạo ảnh, vui lòng thử lại sau.")
    
    except Exception as e:
        update.message.reply_text(f"Đã có lỗi xảy ra: {str(e)}")

# Hàm khởi tạo bot
def start_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "Chào mừng bạn đến với bot tạo hình ảnh bằng DALL-E!\n"
        "Sử dụng lệnh: /gen <từ khoá> để tạo ảnh."
    )

# Hàm khởi động bot
def main() -> None:
    """Khởi động bot"""
    updater = Updater(TOKEN)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("gen", generate_command))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
