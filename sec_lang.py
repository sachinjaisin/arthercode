from krutrim_cloud import KrutrimCloud
import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

Krutrim_Api_Key = os.getenv("Krutrim_Api_Key") 
client=KrutrimCloud(api_key="Krutrim_Api_Key")
language_codes = {
            'hindi': 'hin',
            'tamil': 'tam',
            'telugu': 'tel',
            'kannada': 'kan',
            'bengali': 'ben',
            'gujarati': 'guj',
            'english': 'eng'
        }
tts_url = "https://cloud.olakrutrim.com/api/v1/languagelabs/tts"
headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer peRaEh89TpUZU_zuAFPMNxFX_QE'
        }


async def translate_question(client,question_text, question_hint,language):
        language = language_codes.get(language.lower(), 'english')
        
        try:
            response = client.chat.completions.create(
                model="Mistral-Nemo-Krutrim",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"You are a financial translator. Provide explanations in {language} "
                            "using simple terms that modern generations can understand. "
                            "Note: Do not simply translate the text word-for-word; instead, provide a simple explanation which is **maximum 3 sentences**."
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Question: {question_text}\nHint: {question_hint}\n\nProvide bilingual explanation:"
                        )
                    }
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return (f"Translation error: {e}")

async def generate_and_play_audio(client,text,language):

        try:
            lang_code = language_codes.get(language.lower(), 'eng')
            
            payload = json.dumps({
                "input_text": text,
                "input_language": lang_code,
                "input_speaker": "male"
            })
            
            response = requests.request("POST", tts_url, headers=headers, data=payload)
            return response.text

        except Exception as e:
            return (f"Audio generation error: {e}")
