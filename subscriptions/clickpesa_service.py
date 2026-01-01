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
        self.checksum_key = settings.CLICKPESA_CHECKSUM_KEY
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



    def generate_checksum(self, payload):
        """
        Calculate Checksum:
        1. Sort keys alphabetically
        2. Concatenate values
        3. HMAC-SHA256
        """
        import hmac
        import hashlib
        
        # Sort keys
        sorted_keys = sorted(payload.keys())
        
        # Concatenate values
        concat_string = ""
        for key in sorted_keys:
            concat_string += str(payload[key])
            
        # HMAC-SHA256
        if not self.checksum_key:
            logger.warning("Checksum Key not found! Checksum will be invalid.")
            return "MISSING_KEY"
            
        signature = hmac.new(
            self.checksum_key.encode('utf-8'),
            concat_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature

    def initiate_ussd_push(self, phone_number, amount, reference):
        """Trigger the USSD Push on user's phone"""
        # New Endpoint: /third-parties/payments/initiate-ussd-push-request
        # New Endpoint: /third-parties/payments/initiate-ussd-push-request
        # base_url = "https://api.clickpesa.com" # REMOVED HARDCODE
        url = f"{self.api_url}/third-parties/payments/initiate-ussd-push-request"
        
        formatted_phone = self.format_phone(phone_number)
        
        # Payload construction
        payload_data = {
            "amount": str(int(float(amount))), # Ensure string, maybe int? User said <string>.
            "currency": "TZS",
            "orderReference": reference,
            "phoneNumber": formatted_phone
        }
        
        # Calculate Checksum (from payload data)
        checksum = self.generate_checksum(payload_data)
        
        # Add checksum to payload
        payload_data["checksum"] = checksum
        
        try:
            headers = self.get_headers()
            
            logger.info(f"Initiating USSD Push to {formatted_phone}: {url}")
            logger.info(f"Payload: {payload_data}")
            
            response = requests.post(url, json=payload_data, headers=headers)
            
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
        # base_url = "https://api.clickpesa.com" # REMOVED HARDCODE
        url = f"{self.api_url}/third-parties/payments/{order_reference}"
        
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
