import os
import json
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
import ollama
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, RetryError

def is_rate_limit_error(retry_state):
    exception = retry_state.outcome.exception()
    if exception is None:
        return False
    error_msg = str(exception).lower()
    return ("429" in error_msg or "quota" in error_msg or "limit" in error_msg or 
            isinstance(exception, ResourceExhausted))

@retry(
    retry=is_rate_limit_error,
    wait=wait_exponential(multiplier=2, min=10, max=120), 
    stop=stop_after_attempt(3),
    before_sleep=lambda retry_state: print(f'⚠️ Rate Limit hit. Retrying in {retry_state.next_action.sleep} seconds...')
)
async def get_gemini_response(prompt: str) -> str:
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(None, model.generate_content, prompt),
            timeout=60.0
        )
        return response.text
    except Exception as e:
        print(f"Exception type: {type(e).__name__}, Message: {str(e)}")
        if isinstance(e, ResourceExhausted):
            pass  
        raise

async def get_llama_response(prompt: str) -> str:
    try:
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: ollama.generate(model='llama3.1:latest', prompt=prompt, options={'num_ctx': 4096})),
            timeout=60.0
        )
        return response['response']
    except asyncio.TimeoutError:
        raise TimeoutError("Llama API call timed out after 60 seconds")
    except Exception as e:
        raise

async def engine_debate(prompt: str) -> dict:
    gemini_answer, llama_answer = await asyncio.gather(
        get_gemini_response(prompt),
        get_llama_response(prompt)
    )
    print(f'✓ Stage 1: Parallel Inference Complete')
    
    gemini_review_prompt = f"""You are a skeptical technical reviewer. Please review this answer to the question '{prompt}': 

{llama_answer}

IMPORTANT FORMATTING REQUIREMENTS:
- DO NOT use Markdown tables 
- DO NOT use ASCII tables
- DO NOT use vertical bars (|)
- Use ## Headers, ### Sub-headers, and * Bullet points for all comparisons
- Write in clear paragraphs and lists

Provide a thorough technical review."""
    
    llama_review_prompt = f"""You are a skeptical technical reviewer. Please review this answer to the question '{prompt}': 

{gemini_answer}

IMPORTANT FORMATTING REQUIREMENTS:
- DO NOT use Markdown tables 
- DO NOT use ASCII tables
- DO NOT use vertical bars (|)
- Use ## Headers, ### Sub-headers, and * Bullet points for all comparisons
- Write in clear paragraphs and lists

Provide a thorough technical review."""
    
    gemini_review, llama_review = await asyncio.gather(
        get_gemini_response(gemini_review_prompt),
        get_llama_response(llama_review_prompt)
    )
    print(f'✓ Stage 2: Peer Reviews Complete')
    
    synthesis_prompt = f"""You are a consensus synthesizer. Create a final answer to '{prompt}' based on this analysis:

## Gemini's Answer
{gemini_answer}

## Llama's Answer  
{llama_answer}

## Gemini's Review of Llama
{gemini_review}

## Llama's Review of Gemini
{llama_review}

IMPORTANT FORMATTING REQUIREMENTS:
- DO NOT use Markdown tables 
- DO NOT use ASCII tables
- DO NOT use vertical bars (|)
- Use ## Headers, ### Sub-headers, and * Bullet points for all comparisons
- Write in clear paragraphs and lists

Synthesize the most accurate and comprehensive response."""
    
    consensus = await get_gemini_response(synthesis_prompt)
    print(f'✓ Stage 3: Consensus Synthesis Complete')
    
    return {
        "gemini_answer": gemini_answer,
        "llama_answer": llama_answer,
        "gemini_review": gemini_review,
        "llama_review": llama_review,
        "consensus": consensus
    }
