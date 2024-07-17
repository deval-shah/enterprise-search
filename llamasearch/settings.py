from pydantic import BaseModel
import yaml
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

class VectorStoreConfig(BaseModel):
    collection_name: str = "default"
    vector_size: int = 1536
    distance: str = "Cosine"
    batch_size: int = 30
    alpha: float = 0.5 
    top_k: int = 10
    use_async: bool = False

class QdrantClientConfig(BaseModel):
    url: str = "http://localhost:6333"
    prefer_grpc: bool = False

class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379

class Embedding(BaseModel):
    # model: str = "local:BAAI/bge-small-en-v1.5"
    model: str = "local:Alibaba-NLP/gte-Qwen2-1.5B-instruct" # 13048 MiB memory
    use_openai: bool = False

class Llm(BaseModel):
    modelfile: str = "modelfile.yaml"
    use_openai: bool = False

class Reranker(BaseModel):
    model: str = "BAAI/bge-reranker-large"

class Eval(BaseModel):
    custom_model_grammar_path: str = "./model_files/json_arr.gbnf"
    model_name: str = "TheBloke/Mistral-7B-Instruct-v0.2-GGUF"
    filename: str = "mistral-7b-instruct-v0.2.Q5_K_M.gguf"
    chat_format: str = "chatml"

class ApplicationConfig(BaseModel):
    config_path: str = "/app/config.yaml"
    data_path: str = "./data/sample-docs/"
    log_dir: str = "/data/app/logs"
    upload_subdir: str = "uploads"
    enable_prometheus: bool = False

class Config(BaseModel):
    application: ApplicationConfig = ApplicationConfig()
    qdrant_client_config: QdrantClientConfig = QdrantClientConfig()
    vector_store_config: VectorStoreConfig = VectorStoreConfig()
    redis_config: RedisConfig = RedisConfig()
    embedding: Embedding = Embedding()
    reranker: Reranker = Reranker()
    llm: Llm = Llm()
    eval: Eval = Eval()

def check_openai_api_key():
    if not os.getenv('OPENAI_API_KEY'):
        print("ERROR :: OPENAI_API_KEY is not set in the environment.")
        exit(1)

def load_config(config_path: str) -> Config:
    config_file = Path(config_path)
    if config_file.is_file():
        with open(config_file, 'r') as file:
            config_data = yaml.safe_load(file)
            config = Config(**config_data)
            if config.embedding.use_openai or config.llm.use_openai:
                check_openai_api_key()
            # Adjust paths for Docker environment
            if os.getenv('DOCKER_ENV') == 'true':
                config.llm.modelfile = f"/app/{config.llm.modelfile}"
            return config
    else:
        raise FileNotFoundError(f"No configuration file found at {config_path}")

config_path = os.getenv('CONFIG_PATH', '/app/config.dev.yaml')
config = load_config(config_path)
