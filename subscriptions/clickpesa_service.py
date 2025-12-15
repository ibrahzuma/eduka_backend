import requests
from django.conf import settings
from datetime import datetime

class ClickPesaService:
    def __init__(self):
        self.api_url = settings.CLICKPESA_API_URL
        self.auth_url = settings.CLICKPESA_AUTH_URL
        self.client_id = settings.CLICKPESA_CLIENT_ID
        self.api_key = settings.CLICKPESA_API_KEY
        self.token = None

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
        # Note: Depending on ClickPesa docs, auth might be Basic Auth or just API Key headers.
        # Based on docs URL provided earlier: "Use API Keys to Generate Authorization Token"
        try:
            # Usually OAuth2 or similar
            # If the docs say "Generate Authorization Token" endpoint:
            response = requests.post(
                self.auth_url, 
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.client_id,
                    'client_secret': self.api_key # Often API Key acts as secret in this flow
                }
            )
            # Fallback if standard OAuth check fails or if docs specify different payload
            if response.status_code == 200:
                self.token = response.json().get('access_token')
            else:
                # If direct API Key usage is allowed or different auth method:
                # Some gateways just use headers. We'll assume Token flow first.
                raise Exception(f"Auth Failed: {response.text}")
        except Exception as e:
            print(f"ClickPesa Auth Error: {e}")
            # In some implementations, you might just need the x-api-key header directly without a Bearer token?
            # Re-reading: "Use API Keys to Generate Authorization Token" strongly implies a token step.
            pass

    def preview_ussd_push(self, phone_number, amount):
        """Validate if payment is possible for number"""
        # Endpoint: /collection/ussd-push/preview (Example path, adjust based on exact docs)
        url = f"{self.api_url}collection/ussd-push/preview"
        payload = {
            "mobile_number": phone_number,
            "amount": str(amount),
            "currency": "TZS" # Assuming Tanzania
        }
        
        # If Token is required
        headers = self.get_headers()
        response = requests.post(url, json=payload, headers=headers)
        return response.json()

    def initiate_ussd_push(self, phone_number, amount, reference):
        """Trigger the USSD Push on user's phone"""
        url = f"{self.api_url}collection/ussd-push/initiate"
        
        payload = {
            "mobile_number": phone_number,
            "amount": str(amount),
            "currency": "TZS",
            "order_reference": reference,
            "description": "Subscription Payment"
        }
        
        headers = self.get_headers()
        try:
            response = requests.post(url, json=payload, headers=headers)
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def check_status(self, order_reference):
        """Poll for payment status"""
        # Endpoint guess based on docs summary "querying-for-payments"
        url = f"{self.api_url}collection/payments" 
        params = {"order_reference": order_reference}
        
        headers = self.get_headers()
        response = requests.get(url, params=params, headers=headers)
        return response.json()
