from pydantic import BaseModel, Field
from dotenv import load_dotenv
import yaml
from pathlib import Path
import os

load_dotenv()

# Determine the base path
BASE_PATH = Path(os.getenv('APP_BASE_PATH', '.')).resolve()

def get_path(relative_path):
    full_path = BASE_PATH / relative_path
    return str(full_path)

class VectorStoreConfig(BaseModel):
    collection_name: str = "default"
    vector_size: int = 1536
    distance: str = "Cosine"
    batch_size: int = 30
    alpha: float = 0.5
    top_k: int = 10
    use_async: bool = False
    multi_tenancy: bool = True
    enable_hybrid: bool = True

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
    modelfile: str = get_path("config/modelfile.yaml")
    use_openai: bool = False

class Reranker(BaseModel):
    model: str = "BAAI/bge-reranker-large"
    top_n: int = 3

class Eval(BaseModel):
    custom_model_grammar_path: str = "./model_files/json_arr.gbnf"
    model_name: str = "TheBloke/Mistral-7B-Instruct-v0.2-GGUF"
    filename: str = "mistral-7b-instruct-v0.2.Q5_K_M.gguf"
    chat_format: str = "chatml"

class ApplicationConfig(BaseModel):
    config_path: str = Field(default="config/config.dev.yaml", env="CONFIG_PATH")
    data_path: str = Field(default="data/sample-docs/", env="DATA_PATH")
    log_dir: str = Field(default="data/app/logs", env="LOG_DIR")
    upload_subdir: str = "uploads"
    enable_prometheus: bool = False
    eval_data_path: str = Field(default="data/eval/document/", env="DATA_PATH")

    def __init__(self, **data):
        super().__init__(**data)
        self.config_path = get_path(self.config_path)
        self.data_path = get_path(self.data_path)
        self.log_dir = get_path(self.log_dir)

    def get_config_path(self):
        return get_path(self.config_path)

    def get_data_path(self):
        return get_path(self.data_path)

    def get_log_dir(self):
        return get_path(self.log_dir)
class DatasetGeneration(BaseModel):
    model_type: str = "custom"
    model_name :str = "llama3:latest"
    use_openai: bool =False
    openai_model: str = "gpt4-o"


    
class Config(BaseModel):
    application: ApplicationConfig = ApplicationConfig()
    qdrant_client_config: QdrantClientConfig = QdrantClientConfig()
    vector_store_config: VectorStoreConfig = VectorStoreConfig()
    redis_config: RedisConfig = RedisConfig()
    embedding: Embedding = Embedding()
    reranker: Reranker = Reranker()
    llm: Llm = Llm()
    eval: Eval = Eval()
    dataset_generator: DatasetGeneration=DatasetGeneration()

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

config_path = os.getenv('CONFIG_PATH', 'config/config.dev.yaml')
config = load_config(config_path)

def pretty_print_paths():
    print("\n" + "="*80)
    print("Path Configuration:")
    print("="*80)
    print(f"BASE_PATH:     {BASE_PATH}")
    print("-"*80)
    print("Resolved Paths:")
    print(f"Config File:   {config.application.get_config_path()}")
    print(f"Data Path:     {config.application.get_data_path()}")
    print(f"Log Directory: {config.application.get_log_dir()}")
    print("="*80 + "\n")

pretty_print_paths()