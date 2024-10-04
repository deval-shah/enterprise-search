from deepeval.models.base_model import DeepEvalBaseLLM
from typing import Any, Dict, Optional
import requests

# Model options
model_params = {
    "temperature": 0.2,
    "num_predict": 4096,
    "num_ctx": 8192,
    "seed": 42,
    "top_k": 20,
    "top_p": 0.95,
    "tfs_z": 0.5,
    "typical_p": 0.7,
    "repeat_last_n": 33,
    "repeat_penalty": 1.2,
    "presence_penalty": -0.5,
    "frequency_penalty": 1.0,
    "mirostat": 1,
    "mirostat_tau": 0.8,
    "mirostat_eta": 0.6,
    "penalize_newline": True,
    "stop": ["\n", "user:"],
    # "stop": ["\n\n"],
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

class CustomModel(DeepEvalBaseLLM):
    """
    A custom model class to interact with an LLM based on the Llama3:70b model,
    providing functionalities to load the model, generate responses, and manage model settings.
    """

    def __init__(self, model: str = "llama3:70b", base_url: str = 'http://localhost:11435') -> None:
        """
        Initializes the CustomModel with a specific LLM model and API base URL.

        Args:
            model (str): The model identifier, default is "llama3:70b".
            base_url (str): The base URL for the API endpoint, default is 'http://localhost:11435'.
        """
        self.base_url = base_url
        self.model = model

    def load_model(self) -> str:
        """
        Loads the model configuration.

        Returns:
            str: The model identifier.
        """
        return self.model

    def generate(self, user_message: str, only_message: bool = True, model_params: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Generates a response from the model based on the user's message.

        Args:
            user_message (str): The message from the user to which the model should respond.
            only_message (bool): Flag to determine if only the message content should be returned, default is True.
            model_params (Optional[Dict[str, Any]]): Additional model parameters to be sent to the API.

        Returns:
            Optional[str]: The generated response or None if an error occurs.
        """
        url = f"{self.base_url}/api/chat"
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant that strictly follows the given instructions"},
                {"role": "user", "content": user_message}
            ],
            "stream": False,
            "format": "json",
            #"grammar": "./model_files/json_arr.gbnf",
            "keep_alive": "30m"
        }

        if model_params:
            print("Using model params ", model_params)
            data.update(model_params)

        try:
            response = requests.post(url, json=data)
            response.raise_for_status()  # Raises HTTPError for bad requests (4XX, 5XX)
            response_data = response.json()
            if only_message:
                return response_data.get('message', {}).get('content', 'Empty response from LLM')
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {str(e)}")
            return None
        except ValueError:
            print("Failed to decode JSON response")
            return None

    async def a_generate(self, prompt: str) -> Optional[str]:
        """
        Asynchronous wrapper for the generate method.

        Args:
            prompt (str): The user's prompt for which a response is generated.

        Returns:
            Optional[str]: The generated response or None if an error occurs.
        """
        return self.generate(prompt)

    def get_model_name(self) -> str:
        """
        Retrieves the name of the model.

        Returns:
            str: The name of the model.
        """
        return self.model

def main():
    # Create an instance of the model
    model = CustomModel()
    # Load the model, which currently just returns the model name
    model_name = model.load_model()
    print(f"Loaded model: {model_name}")
    # Take input from the user and generate responses
    try:
        while True:
            # Take input from the user
            user_input = input("Enter your message (type 'exit' to quit): ")
            if user_input.lower() == 'exit':
                break
            # Generate a response using the custom model
            response = model.generate(user_input, only_message=True)
            print(f"Response: {response}")
    except KeyboardInterrupt:
        print("\nExited by user")

if __name__ == "__main__":
    main()