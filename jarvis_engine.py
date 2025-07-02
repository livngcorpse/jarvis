import google.generativeai as genai
import json
import os
from pathlib import Path

class JarvisEngine:
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-pro')
        
    async def process_prompt(self, prompt: str, user_id: int) -> str:
        try:
            # Build context with current file structure
            context = self.build_context()
            
            full_prompt = f"""
You are JARVIS, an AI assistant that can modify its own code and create new features.

Current bot structure:
{context}

User request: {prompt}

Respond naturally and execute any code modifications needed.
If creating new features, use the proper folder structure.
"""
            
            response = self.model.generate_content(full_prompt)
            return response.text
            
        except Exception as e:
            return f"🤖 Processing error: {str(e)}"
    
    def build_context(self) -> str:
        """Build current file structure context"""
        context = {"files": {}}
        
        # Add main files
        for file_path in ['main.py', 'api.py', 'config/settings.json']:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        context["files"][file_path] = f.read()[:1000]  # Limit size
                except:
                    pass
        
        return json.dumps(context, indent=2)