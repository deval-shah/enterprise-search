from pydantic import BaseModel
import yaml
from pathlib import Path
import os

class VectorStoreConfig(BaseModel):
    collection_name: str = "default"
    vector_size: int = 384
    distance: str = "Cosine"

class QdrantClientConfig(BaseModel):
    url: str = "http://localhost:6333"
    prefer_grpc: bool = False

class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379

class Embedding(BaseModel):
    embed_model: str = "local:BAAI/bge-small-en-v1.5"

class Llm(BaseModel):
    llm_model: str = "llama3:8b"

class Eval(BaseModel):
    custom_model_grammar_path: str = "./model_files/json.gbnf"
    model_name: str = "TheBloke/Mistral-7B-Instruct-v0.2-GGUF"
    filename: str = "mistral-7b-instruct-v0.2.Q5_K_M.gguf"
    chat_format: str = "chatml"

class ApplicationConfig(BaseModel):
    config_path: str = "/app/config.yaml"
    data_path: str = "/data/files"
    log_dir: str = "/data/app/logs"
    upload_subdir: str = "uploads"

class Config(BaseModel):
    application: ApplicationConfig = ApplicationConfig()
    qdrant_client_config: QdrantClientConfig = QdrantClientConfig()
    vector_store_config: VectorStoreConfig = VectorStoreConfig()
    redis_config: RedisConfig = RedisConfig()
    embedding: Embedding = Embedding()
    llm: Llm = Llm()
    eval: Eval = Eval()

def load_config(config_path: str) -> Config:
    config_file = Path(config_path)
    if config_file.is_file():
        with open(config_file, 'r') as file:
            config_data = yaml.safe_load(file)
            return Config(**config_data)
    else:
        raise FileNotFoundError(f"No configuration file found at {config_path}")

config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
config = load_config(config_path)