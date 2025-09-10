"""
Ollama Manager - Handles Llama 3.2:3b Q4_K_M model
Optimized for 8K context window
"""

import subprocess
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
import aiohttp
import time
from pathlib import Path

logger = logging.getLogger(__name__)

class OllamaManager:
    """
    Manages Ollama service and Llama 3.2:3b model interactions
    """
    
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.model_name = "llama3.2:3b"  # Will use Q4_K_M quantization
        self.context_window = 8192  # 8K context
        self.max_tokens = 2048
        self.temperature = 0.7
        self.is_running = False
        self.session = None
        
    async def initialize(self):
        """Initialize Ollama service and ensure model is loaded"""
        try:
            # Check if Ollama is running
            await self.check_service()
            
            # Ensure model is available
            await self.ensure_model()
            
            # Create aiohttp session
            self.session = aiohttp.ClientSession()
            
            self.is_running = True
            logger.info("Ollama manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Ollama: {e}")
            self.is_running = False
    
    async def check_service(self):
        """Check if Ollama service is running"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        logger.info("Ollama service is running")
                        return True
        except:
            # Try to start Ollama service
            logger.info("Starting Ollama service...")
            subprocess.Popen(['ollama', 'serve'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            
            # Wait for service to start
            await asyncio.sleep(3)
            
            # Check again
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.base_url}/api/tags") as response:
                        if response.status == 200:
                            logger.info("Ollama service started successfully")
                            return True
            except:
                raise Exception("Failed to start Ollama service")
        
        return False
    
    async def ensure_model(self):
        """Ensure Llama 3.2:3b model is available"""
        try:
            # Check if model exists
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [m['name'] for m in data.get('models', [])]
                        
                        if self.model_name in models:
                            logger.info(f"Model {self.model_name} is available")
                            return True
            
            # Model not found, need to pull it
            logger.info(f"Pulling {self.model_name} model (Q4_K_M quantization)...")
            
            # Pull model with quantization
            pull_process = subprocess.Popen(
                ['ollama', 'pull', self.model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for download to complete
            stdout, stderr = pull_process.communicate()
            
            if pull_process.returncode == 0:
                logger.info(f"Model {self.model_name} downloaded successfully")
                return True
            else:
                raise Exception(f"Failed to download model: {stderr}")
                
        except Exception as e:
            logger.error(f"Error ensuring model: {e}")
            raise
    
    async def query(self, prompt: str, context: Optional[str] = None) -> str:
        """
        Query the Llama model with automotive log context
        """
        if not self.is_running:
            logger.error("Ollama service is not running")
            return "AI service is not available"
        
        try:
            # Prepare the prompt with context
            full_prompt = self._prepare_prompt(prompt, context)
            
            # Ensure prompt fits in context window
            full_prompt = self._truncate_to_context(full_prompt)
            
            # Generate response
            payload = {
                "model": self.model_name,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "num_ctx": self.context_window,
                    "num_predict": self.max_tokens,
                    "temperature": self.temperature,
                    "top_p": 0.9,
                    "top_k": 40,
                    "repeat_penalty": 1.1
                }
            }
            
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('response', '')
                else:
                    error_text = await response.text()
                    logger.error(f"Ollama API error: {error_text}")
                    return "Error generating response"
                    
        except asyncio.TimeoutError:
            logger.error("Query timeout")
            return "Response generation timed out"
        except Exception as e:
            logger.error(f"Error querying model: {e}")
            return f"Error: {str(e)}"
    
    async def analyze_log_errors(self, errors: List[Dict], context: str) -> Dict[str, Any]:
        """
        Analyze log errors using AI
        """
        prompt = f"""You are an automotive diagnostics expert analyzing CAN bus errors.

Context: {context}

Errors found:
{json.dumps(errors[:10], indent=2)}  # Limit to first 10 errors

Please analyze these errors and provide:
1. Root cause analysis
2. Potential impacts
3. Recommended fixes
4. Priority level (Critical/High/Medium/Low)

Format your response as JSON."""

        response = await self.query(prompt)
        
        try:
            # Try to parse as JSON
            return json.loads(response)
        except:
            # Return as text if not valid JSON
            return {
                "analysis": response,
                "format": "text"
            }
    
    async def suggest_fix(self, error_code: str, error_description: str) -> str:
        """
        Suggest fix for specific error
        """
        prompt = f"""As an automotive expert, suggest a fix for:
Error Code: {error_code}
Description: {error_description}

Provide:
1. Likely cause
2. Step-by-step fix
3. Prevention tips

Keep response concise and practical."""

        return await self.query(prompt)
    
    async def explain_can_message(self, can_id: str, data: str, dbc_info: Optional[Dict] = None) -> str:
        """
        Explain a CAN message in plain English
        """
        prompt = f"""Explain this CAN message in simple terms:
CAN ID: {can_id}
Data: {data}
"""
        
        if dbc_info:
            prompt += f"\nDBC Info: {json.dumps(dbc_info, indent=2)}"
        
        prompt += "\nExplain what this message means and any potential issues."
        
        return await self.query(prompt)
    
    async def predict_failure(self, patterns: List[Dict]) -> Dict[str, Any]:
        """
        Predict potential failures based on patterns
        """
        prompt = f"""Analyze these patterns from automotive logs and predict potential failures:

Patterns detected:
{json.dumps(patterns[:5], indent=2)}

Provide:
1. Failure probability (High/Medium/Low)
2. Estimated time to failure
3. Warning signs to watch for
4. Preventive actions

Format as JSON if possible."""

        response = await self.query(prompt)
        
        try:
            return json.loads(response)
        except:
            return {"prediction": response, "format": "text"}
    
    def _prepare_prompt(self, prompt: str, context: Optional[str] = None) -> str:
        """
        Prepare prompt with system instructions and context
        """
        system_prompt = """You are an expert automotive diagnostics AI assistant specializing in:
- CAN bus communication analysis
- J1939 protocol interpretation  
- UDS (Unified Diagnostic Services) troubleshooting
- ECU error diagnosis
- Predictive failure analysis

Provide clear, actionable insights for automotive engineers.
Focus on practical solutions and root cause analysis.
"""
        
        full_prompt = system_prompt + "\n\n"
        
        if context:
            full_prompt += f"Log Context:\n{context}\n\n"
        
        full_prompt += f"User Query: {prompt}\n\nResponse:"
        
        return full_prompt
    
    def _truncate_to_context(self, text: str, max_tokens: int = 7000) -> str:
        """
        Truncate text to fit in context window (leaving room for response)
        Approximate: 1 token ≈ 4 characters
        """
        max_chars = max_tokens * 4
        if len(text) > max_chars:
            # Keep the beginning and end, truncate middle
            half = max_chars // 2
            return text[:half] + "\n...[truncated]...\n" + text[-half:]
        return text
    
    async def stream_query(self, prompt: str, context: Optional[str] = None):
        """
        Stream response from model for real-time display
        """
        if not self.is_running:
            yield "AI service is not available"
            return
        
        try:
            full_prompt = self._prepare_prompt(prompt, context)
            full_prompt = self._truncate_to_context(full_prompt)
            
            payload = {
                "model": self.model_name,
                "prompt": full_prompt,
                "stream": True,
                "options": {
                    "num_ctx": self.context_window,
                    "num_predict": self.max_tokens,
                    "temperature": self.temperature
                }
            }
            
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload
            ) as response:
                async for line in response.content:
                    if line:
                        try:
                            data = json.loads(line)
                            if 'response' in data:
                                yield data['response']
                            if data.get('done', False):
                                break
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.error(f"Error in stream query: {e}")
            yield f"Error: {str(e)}"
    
    def is_available(self) -> bool:
        """Check if Ollama service is available"""
        return self.is_running
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
        self.is_running = False
        logger.info("Ollama manager cleaned up")

# Singleton instance
ollama_manager = OllamaManager()
