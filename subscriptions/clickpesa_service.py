import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class ClickPesaService:
    def __init__(self):
        self.api_url = settings.CLICKPESA_API_URL
        self.auth_url = settings.CLICKPESA_AUTH_URL
        self.client_id = settings.CLICKPESA_CLIENT_ID
        self.api_key = settings.CLICKPESA_API_KEY
        self.token = None

    def format_phone(self, phone):
        """Ensure phone is in 255 format"""
        phone = phone.strip().replace('+', '').replace(' ', '')
        if phone.startswith('0'):
            return '255' + phone[1:]
        if phone.startswith('255'):
            return phone
        return '255' + phone # Assumption if 7... provided




    def authenticate(self):
        """Exchange Client ID and API Key for an Access Token"""
        try:
            # Endpoint: https://api.clickpesa.com/third-parties/generate-token
            # Headers: api-key, client-id
            # Method: POST
            
            logger.info(f"Authenticating with ClickPesa... {self.auth_url}")
            
            headers = {
                'api-key': self.api_key,
                'client-id': self.client_id,
                'Content-Type': 'application/json'
            }
            
            response = requests.post(self.auth_url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    # The token sometimes comes with 'Bearer ' prefix or might be raw
                    token = data.get('token')
                    if token.startswith('Bearer '):
                        self.token = token.split(' ')[1]
                    else:
                        self.token = token
                    logger.info("ClickPesa Auth Successful")
                else:
                    raise Exception(f"Auth Failed Response: {data}")
            else:
                 error_msg = f"Auth Failed: {response.status_code} - {response.text}"
                 logger.error(error_msg)
                 raise Exception(error_msg)

        except Exception as e:
            logger.error(f"ClickPesa Connection Error: {e}")
            raise e

    def initiate_ussd_push(self, phone_number, amount, reference):
        """Trigger the USSD Push on user's phone"""
        url = f"{self.api_url}collection/ussd-push/initiate"
        
        formatted_phone = self.format_phone(phone_number)
        
        payload = {
            "mobile_number": formatted_phone,
            "amount": float(amount), # Ensure it's number
            "currency": "TZS",
            "order_reference": reference,
            "description": "Subscription Payment"
        }
        
        try:
            headers = self.get_headers()
            logger.info(f"Initiating USSD Push to {formatted_phone}: {url}")
            
            response = requests.post(url, json=payload, headers=headers)
            
            try:
                res_json = response.json()
            except:
                res_json = {"raw": response.text}
            
            logger.info(f"ClickPesa Response: {response.status_code} - {res_json}")

            if response.status_code in [200, 201]:
                return {"success": True, "data": res_json}
            else:
                return {"success": False, "message": str(res_json)}

        except Exception as e:
            logger.error(f"Initiate USSD Error: {e}")
            return {"success": False, "message": str(e)}

    def get_headers(self):
        if not self.token:
            self.authenticate()
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            # 'x-api-key': self.api_key # Removing x-api-key as docs don't strictly enforce it for GET, reducing noise
            # If initiate breaks, we add it back. But Check Status likely strictly follows Bearer only.
        }

    def check_status(self, order_reference):
        """Poll for payment status"""
        base_url = "https://api.clickpesa.com" 
        url = f"{base_url}/third-parties/payments/{order_reference}"
        
        # Helper to make request
        def make_request(refresh_token=False):
            if refresh_token:
                self.authenticate()
            
            headers = self.get_headers()
            return requests.get(url, headers=headers)

        try:
            response = make_request()
            
            # Retry on 401 (Unauthorized)
            if response.status_code == 401:
                logger.warning("Token expired, refreshing...")
                response = make_request(refresh_token=True)

            logger.info(f"Check Status [{response.status_code}]: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    if len(data) > 0:
                        return data[0]
                    else:
                        # Empty list means Reference not found YET? or Wrong Reference?
                        return {"status": "PENDING", "raw": "Empty List"}
                return data
            
            return {"status": "FAILED", "code": response.status_code}

        except Exception as e:
             logger.error(f"Check Status Error: {e}")
             return {"status": "ERROR", "message": str(e)}
