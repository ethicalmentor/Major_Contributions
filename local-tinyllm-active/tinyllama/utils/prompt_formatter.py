def format_tinyllama_prompt(message: str, system_prompt: str = "") -> str:
    """Format for TinyLlama ChatML format"""
    return f"""<|system|>
{system_prompt}</s>
<|user|>
{message}</s>
<|assistant|>
"""
