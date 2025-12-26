import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import random
from datetime import date

@csrf_exempt
@require_POST
def analyze_receipt(request):
    """
    Mock OCR endpoint.
    In a real implementation, this would send the image to Google Cloud Vision or AWS Textract.
    """
    if 'receipt' not in request.FILES:
        return JsonResponse({'error': 'No image provided'}, status=400)

    image = request.FILES['receipt']
    
    # Simulate processing time or valid image check
    if not image.name.lower().endswith(('.png', '.jpg', '.jpeg')):
        return JsonResponse({'error': 'Invalid file type'}, status=400)

    # Mock Data Return
    # We return a random realistic amount and today's date
    mock_data = {
        "date": date.today().strftime("%Y-%m-%d"),
        "vendor": "General Supplier Ltd",
        "amount": round(random.uniform(1000, 50000), 2),
        "confidence": 0.89,
        "items": [
            {"description": "Item 1", "amount": 1000.00},
            {"description": "Item 2", "amount": 2500.00}
        ]
    }

    return JsonResponse(mock_data)
