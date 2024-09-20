import logging
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# Token của bot
TOKEN = '5452812723:AAHwdHJSMqqb__KzcSIOdJ3QuhqsIr9YTro'

# Thiết lập logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Hàm để khởi động bot
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Chào mừng bạn đến với bot kiểm tra tài khoản Netflix! Sử dụng lệnh /check <user> <pass> để kiểm tra.')

# Hàm để kiểm tra tài khoản Netflix
def check_account(update: Update, context: CallbackContext) -> None:
    if len(context.args) != 2:
        update.message.reply_text('Vui lòng nhập đúng định dạng: /check <user> <pass>')
        return
    
    user = context.args[0]
    password = context.args[1]
    
    # Khởi động trình duyệt
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    
    try:
        driver.get('https://www.netflix.com/youraccount')
        time.sleep(1)
        
        # Nhập email
        email_input = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div[2]/div/form/div[1]/div/div[1]/input')
        email_input.send_keys(user)
        time.sleep(0.6)
        
        # Nhập mật khẩu
        password_input = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div[2]/div/form/div[2]/div/div[1]/input')
        password_input.send_keys(password)
        time.sleep(0.6)
        
        # Gửi form
        submit_button = driver.find_element(By.CSS_SELECTOR, '#appMountPoint > div > div > div.default-ltr-cache-8hdzfz.eyojgsc0 > div > form > button.e1ax5wel2.ew97par0.default-ltr-cache-62lxnw.e1ff4m3w2')
        submit_button.click()
        time.sleep(5.5)
        
        # Kiểm tra thông báo lỗi
        try:
            error_message = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div[2]/div/header/div/div/div').text
            if 'Incorrect password' in error_message or "Sorry, we can't find an account with this email address" in error_message:
                update.message.reply_text('Tên đăng nhập hoặc mật khẩu không chính xác.')
                return
        except:
            pass
        
        # Kiểm tra trạng thái tài khoản
        try:
            plan_message = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/section/div[2]/div/div/div/div/div/div/section/div[2]/div/div[2]/h3').text
            if 'Gói' in plan_message:
                update.message.reply_text('Tài khoản Netflix hoạt động.')
                return
        except:
            pass
        
        # Kiểm tra hủy tư cách thành viên
        try:
            membership_message = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/section/div[2]/div/div/div/div/div/div/section/div[1]/div/div').text
            if 'Tư cách thành viên của bạn đã bị hủy' in membership_message:
                update.message.reply_text('Tài khoản Netflix đã bị hủy tư cách thành viên.')
                return
        except:
            pass
        
        update.message.reply_text('Không thể xác định trạng thái tài khoản.')
    finally:
        driver.quit()

def main() -> None:
    # Khởi động bot
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    
    # Đăng ký các lệnh
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('check', check_account))
    
    # Bắt đầu bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
