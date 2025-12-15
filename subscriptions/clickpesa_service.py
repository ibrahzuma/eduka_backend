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

    def get_headers(self):
        if not self.token:
            self.authenticate()
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'x-api-key': self.api_key
        }

    def authenticate(self):
        """Exchange Client ID and API Key for an Access Token"""
        try:
            logger.info(f"Authenticating with ClickPesa... {self.auth_url}")
            response = requests.post(
                self.auth_url, 
                json={ # Changed to json as per common modern standards, fallback to data if needed
                    'grant_type': 'client_credentials',
                    'client_id': self.client_id,
                    'client_secret': self.api_key 
                },
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                self.token = response.json().get('access_token')
                logger.info("ClickPesa Auth Successful")
            else:
                try: 
                     # Try form-data if json failed
                    response = requests.post(
                        self.auth_url, 
                        data={ 
                            'grant_type': 'client_credentials',
                            'client_id': self.client_id,
                            'client_secret': self.api_key 
                        }
                    )
                    if response.status_code == 200:
                         self.token = response.json().get('access_token')
                         return

                    error_msg = f"Auth Failed: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                except Exception as e:
                     raise e
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

    def check_status(self, order_reference):
        """Poll for payment status"""
        url = f"{self.api_url}collection/payments" 
        params = {"order_reference": order_reference}
        
        try:
            headers = self.get_headers()
            response = requests.get(url, params=params, headers=headers)
            return response.json()
        except:
             return {}
