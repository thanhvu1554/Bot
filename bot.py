import requests
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram.utils.request import Request

# Các hằng số
TOKEN = "5452812723:AAHwdHJSMqqb__KzcSIOdJ3QuhqsIr9YTro"

def track(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id

    if len(context.args) != 1:
        update.message.reply_text("Vui lòng nhập đúng định dạng: /track <mã theo dõi>")
        return
    
    t = context.args[0]
    url = f"https://global.cainiao.com/global/detail.json?mailNos={t}&lang=en&language=en"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
        "Pragma": "no-cache",
        "Accept": "*/*"
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    if 'module' not in data or not data['module']:
        update.message.reply_text("Sai Mã Rồi Nha")
        return

    tracking_info = data['module'][0]

    # Phân tích các thông tin từ JSON
    mailNo = tracking_info.get("mailNo", "N/A")
    ct1 = tracking_info.get("originCountry", "N/A")
    ct2 = tracking_info.get("destCountry", "N/A")
    status = tracking_info.get("status", "N/A")
    statusDesc = tracking_info.get("statusDesc", "N/A")
    progressStatus = tracking_info.get("processInfo", {}).get("progressStatus", "N/A")

    # Kiểm tra nếu bất kỳ thông tin nào là N/A, thì mã theo dõi là sai
    if mailNo == "N/A" or ct1 == "N/A" or ct2 == "N/A" or status == "N/A":
        update.message.reply_text("Sai Mã Rồi Nha")
        return

    # Tạo nội dung tin nhắn để gửi qua Telegram
    message = (
        f"*Track Details:*\n"
        f"**------------------------------------------------**\n"
        f"*TRACK:* `{mailNo}`\n"
        f"**------------------------------------------------**\n"
        f"*Quốc Gia Xuất Phát:* `{ct1}`\n"
        f"**------------------------------------------------**\n"
        f"*Đích Đến:* `{ct2}`\n"
        f"**------------------------------------------------**\n"
        f"*Trạng Thái:* `{status} - {statusDesc}`\n"
        f"**------------------------------------------------**\n"
        f"*Tình Trạng:* `{progressStatus}`"
    )

    update.message.reply_text(message, parse_mode='Markdown')

def main() -> None:
    # Tăng kích thước pool kết nối
    request = Request(con_pool_size=8)
    bot = Bot(token=TOKEN, request=request)
    updater = Updater(bot=bot, use_context=True)
    
    # Tạo Dispatcher
    dispatcher = updater.dispatcher

    # Đăng ký handler cho lệnh /track
    dispatcher.add_handler(CommandHandler("track", track))

    # Bắt đầu bot
    updater.start_polling()

    # Chạy bot cho đến khi bạn nhấn Ctrl-C hoặc quá trình nhận tín hiệu dừng (SIGINT, SIGTERM, hoặc SIGABRT)
    updater.idle()

if __name__ == '__main__':
    main()
