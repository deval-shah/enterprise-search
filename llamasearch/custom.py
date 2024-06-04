from deepeval.models.base_model import DeepEvalBaseLLM
from llama_cpp import Llama
from deepeval.metrics import AnswerRelevancyMetric
import requests

import requests
import json

#Define additional options
options = {
    "temperature": 0.,
    "num_predict": 4096,
    "num_ctx": 8192,
    "seed": 42,
    "top_k": 20,
    "top_p": 0.95,
    "tfs_z": 0.5,
    "typical_p": 0.7,
    "repeat_last_n": 33,
    "repeat_penalty": 1.2,
    "presence_penalty": 1.5,
    "frequency_penalty": 1.0,
    "mirostat": 1,
    "mirostat_tau": 0.8,
    "mirostat_eta": 0.6,
    "penalize_newline": True,
    #"stop": ["\n", "user:"],
    "stop": ["\n\n"],
    "numa": False,
    "num_batch": 2,
    "num_gpu": 1,
    "main_gpu": 0,
    "low_vram": False,
    "f16_kv": True,
    "vocab_only": False,
    "use_mmap": True,
    "use_mlock": False,
    "num_thread": 64
}


def log_to_file(data, filename="api_logs.json"):
    """
    Logs data to a JSON file in a structured and pretty format.

    Args:
    data (dict): The data to log.
    filename (str): The filename of the log file.

    """
    with open(filename, 'a') as file:  # Open the file in append mode
        json.dump(data, file, indent=2)  # Write data with indentation for readability
        file.write('\n')  # Add a newline for separating entries

class CustomModel(DeepEvalBaseLLM):
    def __init__(self, model="llama3:70b", base_url='http://localhost:11435'):
        self.base_url = base_url
        self.model = model

    def load_model(self):
        return self.model

    def generate(self, user_message, only_message=True):
        url = f"{self.base_url}/api/chat"
        data = {
            "model": self.model,
            #"prompt": user_message,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant that strictly follows the given instructions"
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "stream": False,
            "format": "json",
            "grammar": "./model_files/json_arr.gbnf",
            #"raw": True,
            "keep_alive": "30m"
        }
        # print("\n\n")   
        # print("OLLAMA :: Sending the data to the API:")
        # print(json.dumps(data, indent=2))
        # print("\n\n")
        # Include provided options in the data payload
        if options:
            print("Using options ", options)
            data.update(options)

        response = requests.post(url, json=data)

        if response.status_code == 200:
            try:
                response_data = response.json()
                if only_message:
                    response_data = response_data.get('message', {}).get('content', 'Empty response from LLM')
                    #response_data = response_data.get('response', '{"message": "Empty response from LLM"}')
                # #############################
                # log_data = {
                #     "prompt": user_message,
                #     "response": response_data
                # }
                # log_to_file(log_data)
                # #############################
                return response_data
            except ValueError:
                print("Failed to decode JSON response")
                return None
        else:
            print(f"Failed to get valid response, status code: {response.status_code}")
            return None
    
    async def a_generate(self, prompt: str) -> str:
        return self.generate(prompt)

    def get_model_name(self):
        return "Llama 3 70B"

# class CustomModel(DeepEvalBaseLLM):
#     def __init__(
#         self
#     ):
#         self.model = Llama(model_path="./models/Meta-Llama-3-70B-Instruct.Q4_K_M.gguf", chat_format="chatml", n_ctx=8192, n_gpu_layers=35)

#     def load_model(self):
#         return self.model

#     def generate(self, prompt: str) -> str:
#         res = self.model.create_chat_completion(
#             messages=[
#                 {
#                     "role": "system",
#                     "content": "You are a helpful assistant that outputs in JSON. Only return a valid json when specifically asked",
#                     "features": [
#                         "Understand and analyze user inputs effectively.",
#                         "Generate responses in valid JSON format.",
#                         "Ensure accuracy and relevance of the information provided.",
#                         "Maintain a structured and coherent output format.",
#                         "Include necessary fields and data as per user instructions.",
#                         "Handle a variety of topics and contexts efficiently.",
#                         "Provide detailed and context-aware responses."
#                     ],
#                     "tone": {
#                         "style": "Professional and informative",
#                         "guidelines": "Use clear and concise language. Ensure the information is accurate and well-organized. Maintain a professional tone throughout the response."
#                     },
#                 },
#                 {"role": "user", "content": prompt},
#             ],
#             response_format={
#                 "type": "json_object"
#             },
#             temperature=0.
#         )
#         message = res["choices"][0]["message"]["content"]
#         return message

#     async def a_generate(self, prompt: str) -> str:
#         return self.generate(prompt)

#     def get_model_name(self):
#         return "Llama 3 70B"


# llama38b = LLaMA38B()
# print(llama38b.generate("Write me a joke"))
# metric = AnswerRelevancyMetric(model=llama38b)