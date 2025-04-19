from typing import List, Dict
from transformers import MarianMTModel, MarianTokenizer

from app.core.config import settings

class TranslationService:
    def __init__(self):
        self.models = {}
        self.tokenizers = {}
    
    async def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text from source language to target language"""
        # Check if we already have the model loaded
        model_name = self._get_model_name(source_lang, target_lang)
        
        if model_name not in self.models:
            # Load the model and tokenizer
            self._load_model(model_name)
        
        model = self.models[model_name]
        tokenizer = self.tokenizers[model_name]
        
        # Tokenize the text
        batch = tokenizer([text], return_tensors="pt", padding=True)
        
        # Generate translation
        translated = model.generate(**batch)
        
        # Decode the translation
        translated_text = tokenizer.batch_decode(translated, skip_special_tokens=True)[0]
        
        return translated_text
    
    async def translate_ocr_results(self, ocr_results: List[Dict], source_lang: str, target_lang: str) -> List[Dict]:
        """Translate OCR results from source language to target language"""
        # Extract all text into a single list
        texts = [item['text'] for item in ocr_results]
        
        # Translate all texts
        translated_texts = []
        for text in texts:
            translated = await self.translate_text(text, source_lang, target_lang)
            translated_texts.append(translated)
        
        # Create new OCR results with translated text
        translated_results = []
        for i, item in enumerate(ocr_results):
            new_item = item.copy()
            new_item['text'] = translated_texts[i]
            translated_results.append(new_item)
        
        return translated_results
    
    def _load_model(self, model_name: str):
        """Load a model and tokenizer"""
        try:
            tokenizer = MarianTokenizer.from_pretrained(model_name)
            model = MarianMTModel.from_pretrained(model_name)
            
            self.tokenizers[model_name] = tokenizer
            self.models[model_name] = model
        except Exception as e:
            print(f"Error loading model {model_name}: {e}")
            raise
    
    def _get_model_name(self, source_lang: str, target_lang: str) -> str:
        """Get the appropriate model name for a language pair"""
        # Map language names to ISO codes
        lang_to_iso = {
            "Japanese": "jap",
            "English": "en",
            "Chinese": "zh",
            "Korean": "kor",
            "Spanish": "es",
            "French": "fr",
            "German": "de",
            "Russian": "ru",
            "Italian": "it",
            "Portuguese": "pt",
            "Arabic": "ar"
        }
        
        source_iso = lang_to_iso.get(source_lang, "en")
        target_iso = lang_to_iso.get(target_lang, "en")
        
        # Return the appropriate model name
        return f"Helsinki-NLP/opus-mt-{source_iso}-{target_iso}"

translation_service = TranslationService() 