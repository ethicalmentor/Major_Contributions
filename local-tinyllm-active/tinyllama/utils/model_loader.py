import os
from dotenv import load_dotenv
from llama_cpp import Llama

load_dotenv()

def load_llama_model():
    return Llama(
        model_path=os.getenv("MODEL_PATH"),
        n_ctx=int(os.getenv("N_CTX", 2048)),
        n_threads=os.cpu_count() - 1,
        n_gpu_layers=int(os.getenv("N_GPU_LAYERS", 0)),
        use_mmap=True,
        use_mlock=True,
        verbose=False
    )
