import time
from utils.model_loader import load_llama_model
from utils.prompt_formatter import format_tinyllama_prompt
import os
from dotenv import load_dotenv

load_dotenv()

llm = load_llama_model()
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 512))

def generate_response(prompt: str):
    """Generate model response with streaming"""
    full_prompt = format_tinyllama_prompt(prompt)
    start = time.time()
    
    # Streaming output
    output_text = ""
    print("Assistant: ", end='', flush=True)
    
    stream = llm(
        full_prompt,
        max_tokens=MAX_TOKENS,
        temperature=0.7,
        top_p=0.9,
        stop=["</s>"],
        stream=True
    )
    
    for chunk in stream:
        text = chunk['choices'][0]['text']
        print(text, end='', flush=True)
        output_text += text
        
    generation_time = time.time() - start
    tokens_sec = len(output_text.split()) / generation_time
    
    return {
        "response": output_text.strip(),
        "time": f"{generation_time:.2f}s",
        "speed": f"{tokens_sec:.1f} words/s"
    }

if __name__ == "__main__":
    print("TinyLlama Offline Assistant (1.1B parameters)")
    print(f"Model: {os.getenv('MODEL_PATH')}")
    print("Type 'exit' to quit\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        stats = generate_response(user_input)
        print(f"\n\n[Stats] Time: {stats['time']} | Speed: {stats['speed']}\n")
