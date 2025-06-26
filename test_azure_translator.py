#!/usr/bin/env python3
"""
Test script for Azure Translator integration
"""
import os
import requests
import uuid
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_azure_translator():
    """Test Azure Translator API with a simple translation"""
    
    # Get credentials from environment
    key = os.getenv('AZURE_TRANSLATOR_KEY')
    endpoint = os.getenv('AZURE_TRANSLATOR_ENDPOINT', 'https://api.cognitive.microsofttranslator.com')
    region = os.getenv('AZURE_TRANSLATOR_REGION')
    
    if not key:
        print("❌ AZURE_TRANSLATOR_KEY not found in environment variables")
        print("Please add it to your .env file")
        return False
    
    print("🔍 Testing Azure Translator connection...")
    print(f"Endpoint: {endpoint}")
    print(f"Region: {region}")
    
    # Test translation
    path = '/translate'
    constructed_url = endpoint + path
    
    params = {
        'api-version': '3.0',
        'from': 'es',
        'to': 'en'
    }
    
    headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Ocp-Apim-Subscription-Region': region,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }
    
    # Test message
    body = [{
        'text': 'Hola, ¿cómo estás?'
    }]
    
    try:
        response = requests.post(constructed_url, params=params, headers=headers, json=body, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        if result and len(result) > 0:
            translated_text = result[0]['translations'][0]['text']
            detected_lang = result[0].get('detectedLanguage', {}).get('language', 'unknown')
            
            print("✅ Azure Translator test successful!")
            print(f"   Original: 'Hola, ¿cómo estás?'")
            print(f"   Translated: '{translated_text}'")
            print(f"   Detected language: {detected_lang}")
            return True
        else:
            print("❌ Empty response from Azure Translator")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Translation error: {e}")
        return False

def print_setup_instructions():
    """Print setup instructions for Azure Translator"""
    print("\n" + "="*60)
    print("📝 AZURE TRANSLATOR SETUP INSTRUCTIONS")
    print("="*60)
    print("1. Go to https://portal.azure.com")
    print("2. Create a 'Translator' resource")
    print("3. Get your subscription key, endpoint, and region")
    print("4. Create a .env file with:")
    print("")
    print("AZURE_TRANSLATOR_KEY=your_subscription_key")
    print("AZURE_TRANSLATOR_ENDPOINT=https://api.cognitive.microsofttranslator.com")
    print("AZURE_TRANSLATOR_REGION=your_region")
    print("")
    print("See azure_setup_guide.md for detailed instructions!")
    print("="*60)

if __name__ == "__main__":
    if not test_azure_translator():
        print_setup_instructions()
    else:
        print("\n🎉 Ready to use Azure Translator with your bot!")
        print("💰 Benefits: 2M free chars/month, 50% cheaper than Google!") 