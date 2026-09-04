from llama_cpp import Llama


MODEL_PATH = r"C:\\Users\\Mahendra\\.cache\\huggingface\\hub\\models--unsloth--Qwen3.5-2B-GGUF\\snapshots\\f6d5376be1edb4d416d56da11e5397a961aca8ae\\qwen3.5-2b-ud-q4_k_xl.gguf"


llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=4096,
    n_threads=8,
    n_batch=256,
    verbose=True,
)


response = llm.create_chat_completion(
    messages=[
        {
            "role": "system",
            "content": "You are a helpful AI assistant."
        },
        {
            "role": "user",
            "content": "Explain Kubernetes in two sentences."
        }
    ],
    temperature=0.2,
)


print("\n========== RESPONSE ==========\n")
print(response["choices"][0]["message"]["content"])