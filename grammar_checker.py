import os
import json
import requests
import re
from spellchecker import SpellChecker
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from google import genai
from google.genai import types

class GrammarChecker:
    def __init__(self):
        self._model_name = "vennify/t5-base-grammar-correction"
        self._tokenizer = None
        self._model = None

    def load_local_model(self):
        """Lazy-loads the local Hugging Face transformer model and tokenizer to save memory."""
        if self._tokenizer is None or self._model is None:
            # Using T5-base fine-tuned for grammar correction
            # This runs entirely locally and free of cost
            self._tokenizer = AutoTokenizer.from_pretrained(self._model_name)
            self._model = AutoModelForSeq2SeqLM.from_pretrained(self._model_name)

    def local_spell_correct(self, text: str) -> str:
        """Corrects spelling mistakes in the text locally while preserving punctuation and spacing."""
        try:
            spell = SpellChecker()
            # Extract all alphabetical words
            words = re.findall(r'\b[a-zA-Z]+\b', text)
            misspelled = spell.unknown(words)
            
            corrected_text = text
            for word in misspelled:
                # Find the best spelling suggestion
                correction = spell.correction(word)
                if correction and correction.lower() != word.lower():
                    # Match casing of original word
                    if word.istitle():
                        correction = correction.title()
                    elif word.isupper():
                        correction = correction.upper()
                    # Replace only matching word boundary
                    corrected_text = re.sub(rf'\b{word}\b', correction, corrected_text)
            return corrected_text
        except Exception:
            return text

    def check_local(self, text: str) -> dict:
        """Corrects grammar locally using a sentence-by-sentence hybrid SpellChecker + T5 Transformer pipeline."""
        try:
            self.load_local_model()
            
            # Split text into paragraphs to preserve line breaks, headers, and spacing
            paragraphs = text.split("\n")
            corrected_paragraphs = []
            
            for paragraph in paragraphs:
                # If a line is empty, a Markdown header, a divider, or a list bullet, preserve it as is
                stripped = paragraph.strip()
                if not stripped or stripped.startswith("#") or stripped.startswith("==") or stripped.startswith("---") or stripped.startswith("-"):
                    corrected_paragraphs.append(paragraph)
                    continue
                
                # Split paragraph into sentences using regex (split by punctuation followed by space)
                sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                corrected_sentences = []
                
                for sentence in sentences:
                    if not sentence.strip():
                        continue
                    
                    # Stage 1: Fast local spell checking preprocessing (e.g. "disguisting" -> "disgusting")
                    spelled_sentence = self.local_spell_correct(sentence)
                    
                    # Stage 2: Transformer grammar correction (e.g. "I has a orange" -> "I have an orange.")
                    input_text = f"gec: {spelled_sentence}"
                    inputs = self._tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)
                    
                    # Generate corrected sentence tokens
                    outputs = self._model.generate(**inputs, max_length=512)
                    
                    # Decode predictions
                    corrected_sentence = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
                    corrected_sentences.append(corrected_sentence.strip())
                
                # Re-stitch sentences back into a single paragraph
                corrected_paragraphs.append(" ".join(corrected_sentences))
            
            # Re-stitch paragraphs back into a single text with original line breaks
            final_corrected_text = "\n".join(corrected_paragraphs)
            
            return {
                "success": True,
                "corrected_text": final_corrected_text,
                "method": "Local Transformer (T5)",
                "details": "The text was corrected locally using a sentence-by-sentence hybrid SpellChecker + T5 Transformer model."
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def check_huggingface_api(self, text: str, api_token: str = None) -> dict:
        """Corrects grammar online using Hugging Face's Free serverless Cloud Inference API (No local downloads required)."""
        try:
            api_url = f"https://api-inference.huggingface.co/models/{self._model_name}"
            headers = {}
            if api_token:
                headers["Authorization"] = f"Bearer {api_token}"
                
            payload = {"inputs": f"gec: {text}"}
            response = requests.post(api_url, headers=headers, json=payload)
            res_data = response.json()
            
            # If the server is currently booting the model, Hugging Face returns loading details
            if isinstance(res_data, dict) and "estimated_time" in res_data:
                wait_sec = int(res_data["estimated_time"])
                return {
                    "success": False,
                    "error": f"The Hugging Face server is currently booting up the T5 model. Please wait {wait_sec} seconds and try again!"
                }
            
            # If Hugging Face returns an error response
            if isinstance(res_data, dict) and "error" in res_data:
                return {"success": False, "error": res_data["error"]}
                
            corrected_text = res_data[0]['generated_text']
            return {
                "success": True,
                "corrected_text": corrected_text,
                "method": "Hugging Face Cloud API (T5)",
                "details": "The text was processed online using Hugging Face's Free Cloud Inference API (no local computing needed)."
            }
        except Exception as e:
            return {"success": False, "error": f"Could not connect to Hugging Face Cloud: {str(e)}"}

    def check_gemini(self, text: str, api_key: str) -> dict:
        """Detects errors, categorizes them, and provides explanations using Gemini via a direct REST call."""
        if not api_key:
            return {"success": False, "error": "API Key is required for Gemini Backend."}
        
        try:
            # We use the stable gemini-2.5-flash model first, and fallback to gemini-1.5-flash if needed.
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
            
            system_prompt = (
                "You are an expert academic writing assistant. Analyze the user's text for grammar, spelling, "
                "punctuation, and stylistic issues. Provide a detailed analysis and correction in JSON format. "
                "The JSON must have the following structure:\n"
                "{\n"
                "  \"corrected_text\": \"Fully corrected version of the text.\",\n"
                "  \"errors\": [\n"
                "    {\n"
                "      \"original\": \"the word or phrase with error\",\n"
                "      \"replacement\": \"the corrected word or phrase\",\n"
                "      \"category\": \"Grammar\" or \"Spelling\" or \"Punctuation\" or \"Style\",\n"
                "      \"explanation\": \"Brief explanation of why this was corrected.\"\n"
                "    }\n"
                "  ]\n"
                "}"
            )
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": f"Analyze and correct this academic text:\n\n{text}"
                    }]
                }],
                "systemInstruction": {
                    "parts": [{
                        "text": system_prompt
                    }]
                },
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "temperature": 0.2
                }
            }
            
            response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
            
            # If gemini-2.5-flash gives a 404 or other error, fallback to gemini-1.5-flash
            if response.status_code != 200:
                url_fallback = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                response = requests.post(url_fallback, json=payload, headers={"Content-Type": "application/json"})
                
            if response.status_code != 200:
                return {"success": False, "error": f"API Error (Status {response.status_code}): {response.text}"}
                
            response_json = response.json()
            candidate_text = response_json['candidates'][0]['content']['parts'][0]['text']
            
            result_json = json.loads(candidate_text)
            result_json["success"] = True
            result_json["method"] = "Google Gemini AI"
            return result_json
            
        except Exception as e:
            return {"success": False, "error": f"Gemini API execution failed: {str(e)}"}
