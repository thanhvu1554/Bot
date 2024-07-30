import requests
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler
from telegram.utils.request import Request

# Các hằng số
TOKEN = "5452812723:AAHwdHJSMqqb__KzcSIOdJ3QuhqsIr9YTro"

# Hàm để lấy thông tin tracking
def get_tracking_info(t: str):
    url = f"https://global.cainiao.com/global/detail.json?mailNos={t}&lang=en&language=en"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
        "Pragma": "no-cache",
        "Accept": "*/*"
    }
    
    response = requests.get(url, headers=headers)
    data = response.json()
    
    if 'module' not in data or not data['module']:
        return None
    
    tracking_info = data['module'][0]
    return tracking_info

# Hàm để gửi thông báo tracking
def send_tracking_info(context: CallbackContext):
    job = context.job
    tracking_info = get_tracking_info(job.context['t'])
    
    if not tracking_info:
        context.bot.send_message(job.context['chat_id'], text="Sai Mã Rồi Nha")
        return
    
    # Phân tích các thông tin từ JSON
    mailNo = tracking_info.get("mailNo", "N/A")
    ct1 = tracking_info.get("originCountry", "N/A")
    ct2 = tracking_info.get("destCountry", "N/A")
    status = tracking_info.get("status", "N/A")
    statusDesc = tracking_info.get("statusDesc", "N/A")
    progressStatus = tracking_info.get("processInfo", {}).get("progressStatus", "N/A")
    latest_trace = tracking_info.get("latestTrace", {})
    latest_desc = latest_trace.get("desc", "N/A")
    latest_timeStr = latest_trace.get("timeStr", "N/A")

    # Kiểm tra nếu bất kỳ thông tin nào là N/A, thì mã theo dõi là sai
    if mailNo == "N/A" or ct1 == "N/A" or ct2 == "N/A" or status == "N/A":
        context.bot.send_message(job.context['chat_id'], text="Sai Mã Rồi Nha")
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
        f"*Tình Trạng:* `{progressStatus}`\n"
        f"**------------------------------------------------**\n"
        f"*Latest Update:*\n`{latest_timeStr} - {latest_desc}`"
    )
    
    context.bot.send_message(job.context['chat_id'], text=message, parse_mode='Markdown')

# Hàm để theo dõi một lần
def track(update: Update, context: CallbackContext) -> None:
    if len(context.args) != 1:
        update.message.reply_text("Vui lòng nhập đúng định dạng: /track <mã theo dõi>")
        return
    
    t = context.args[0]
    tracking_info = get_tracking_info(t)
    
    if not tracking_info:
        update.message.reply_text("Sai Mã Rồi Nha")
        return
    
    # Phân tích các thông tin từ JSON
    mailNo = tracking_info.get("mailNo", "N/A")
    ct1 = tracking_info.get("originCountry", "N/A")
    ct2 = tracking_info.get("destCountry", "N/A")
    status = tracking_info.get("status", "N/A")
    statusDesc = tracking_info.get("statusDesc", "N/A")
    progressStatus = tracking_info.get("processInfo", {}).get("progressStatus", "N/A")
    latest_trace = tracking_info.get("latestTrace", {})
    latest_desc = latest_trace.get("desc", "N/A")
    latest_timeStr = latest_trace.get("timeStr", "N/A")

    # Kiểm tra nếu bất kỳ thông tin nào là N/A, thì mã theo dõi là sai
    if mailNo == "N/A" or ct1 == "N/A" or ct2 == "N/A" or status == "N/A":
        update.message.reply_text("Sai Mã Rồi Nha")
        return

    # Tạo các nút ấn hiển thị các chi tiết theo thời gian
    keyboard = [
        [
            InlineKeyboardButton("Latest Update", callback_data=f"latest_{t}"),
            InlineKeyboardButton("All Updates", callback_data=f"all_{t}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

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
        f"*Tình Trạng:* `{progressStatus}`\n"
        f"**------------------------------------------------**\n"
        f"*Latest Update:*\n`{latest_timeStr} - {latest_desc}`"
    )
    
    update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    # Lấy dữ liệu từ callback_data
    data = query.data.split('_')
    action = data[0]
    t = data[1]
    
    tracking_info = get_tracking_info(t)
    
    if not tracking_info:
        query.edit_message_text(text="Sai Mã Rồi Nha")
        return
    
    if action == 'latest':
        latest_trace = tracking_info.get("latestTrace", {})
        latest_desc = latest_trace.get("desc", "N/A")
        latest_timeStr = latest_trace.get("timeStr", "N/A")
        
        message = (
            f"*Latest Update:*\n"
            f"**------------------------------------------------**\n"
            f"*Time:* `{latest_timeStr}`\n"
            f"**------------------------------------------------**\n"
            f"*Description:* `{latest_desc}`"
        )
    elif action == 'all':
        details = tracking_info.get("detailList", [])
        message = "*All Updates:*\n"
        for detail in details:
            timeStr = detail.get("timeStr", "N/A")
            desc = detail.get("desc", "N/A")
            message += (
                f"**------------------------------------------------**\n"
                f"*Time:* `{timeStr}`\n"
                f"*Description:* `{desc}`\n"
            )

    # Thêm nút Trở Lại
    keyboard = [[InlineKeyboardButton("Trở Lại", callback_data=f"back_{t}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(text=message, parse_mode='Markdown', reply_markup=reply_markup)

def back(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    # Lấy dữ liệu từ callback_data
    data = query.data.split('_')
    t = data[1]

    tracking_info = get_tracking_info(t)
    
    if not tracking_info:
        query.edit_message_text(text="Sai Mã Rồi Nha")
        return
    
    # Phân tích các thông tin từ JSON
    mailNo = tracking_info.get("mailNo", "N/A")
    ct1 = tracking_info.get("originCountry", "N/A")
    ct2 = tracking_info.get("destCountry", "N/A")
    status = tracking_info.get("status", "N/A")
    statusDesc = tracking_info.get("statusDesc", "N/A")
    progressStatus = tracking_info.get("processInfo", {}).get("progressStatus", "N/A")
    latest_trace = tracking_info.get("latestTrace", {})
    latest_desc = latest_trace.get("desc", "N/A")
    latest_timeStr = latest_trace.get("timeStr", "N/A")

    # Tạo các nút ấn hiển thị các chi tiết theo thời gian
    keyboard = [
        [
            InlineKeyboardButton("Latest Update", callback_data=f"latest_{t}"),
            InlineKeyboardButton("All Updates", callback_data=f"all_{t}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

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
        f"*Tình Trạng:* `{progressStatus}`\n"
        f"**------------------------------------------------**\n"
        f"*Latest Update:*\n`{latest_timeStr} - {latest_desc}`"
    )
    
    query.edit_message_text(text=message, parse_mode='Markdown', reply_markup=reply_markup)

# Hàm để theo dõi liên tục
def altrack(update: Update, context: CallbackContext) -> None:
    if len(context.args) != 1:
        update.message.reply_text("Vui lòng nhập đúng định dạng: /altrack <mã theo dõi>")
        return
    
    t = context.args[0]
    chat_id = update.message.chat_id
    
    # Tạo một công việc định kỳ để gửi thông tin theo dõi mỗi phút
    job_removed = remove_job_if_exists(str(chat_id), context)
    context.job_queue.run_repeating(send_tracking_info, interval=60, first=0, context={'chat_id': chat_id, 't': t}, name=str(chat_id))
    
    text = 'Bắt đầu theo dõi' if job_removed else 'Đã cập nhật theo dõi'
    update.message.reply_text(text)

def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True

# Hàm để hiển thị bảng lệnh
def cmd(update: Update, context: CallbackContext) -> None:
    message = (
        "*Danh sách lệnh:*\n"
        f"**------------------------------------------------**\n"
        f"/track <mã theo dõi>: Theo dõi một lần.\n"
        f"/altrack <mã theo dõi>: Theo dõi liên tục mỗi phút.\n"
        f"/cmd: Hiển thị bảng lệnh.\n"
        f"**------------------------------------------------**"
    )
    update.message.reply_text(message, parse_mode='Markdown')

def main() -> None:
    # Tăng kích thước pool kết nối
    request = Request(con_pool_size=8)
    bot = Bot(token=TOKEN, request=request)
    updater = Updater(bot=bot, use_context=True)
    
    # Tạo Dispatcher
    dispatcher = updater.dispatcher
    
    # Đăng ký handler cho lệnh /track, /altrack, và /cmd
    dispatcher.add_handler(CommandHandler("track", track))
    dispatcher.add_handler(CommandHandler("altrack", altrack))
    dispatcher.add_handler(CommandHandler("cmd", cmd))
    dispatcher.add_handler(CallbackQueryHandler(button, pattern='^(latest|all)_'))
    dispatcher.add_handler(CallbackQueryHandler(back, pattern='^back_'))
    
    # Bắt đầu bot
    updater.start_polling()
    
    # Chạy bot cho đến khi bạn nhấn Ctrl-C hoặc quá trình nhận tín hiệu dừng (SIGINT, SIGTERM, hoặc SIGABRT)
    updater.idle()

if __name__ == '__main__':
    main()
