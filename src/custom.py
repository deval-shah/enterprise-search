from typing import Awaitable
from deepeval.models.base_model import DeepEvalBaseLLM
from llama_cpp import Llama, LlamaGrammar
from logger import CustomLogger
import os

logger = CustomLogger.setup_logger(__name__)

class CustomModel(DeepEvalBaseLLM):
    """
    Custom model class that wraps around the LLaMA model to generate text based on prompts.
    """
    
    def __init__(self) -> None:
        """
        Initializes the custom model with a LLaMA model.

        Args:
            model (Llama): The LLaMA model instance.
        """
        self.load_model()
        logger.info(f"{self.get_model_name()} initialized.")

    def load_model(self, model_name = "TheBloke/Mistral-7B-Instruct-v0.2-GGUF", filename = "mistral-7b-instruct-v0.2.Q5_K_M.gguf") -> Llama:   

        """
        Returns the loaded LLaMA model.

        Returns:
            Llama: The LLaMA model instance.
        """
        try:
            self.model = Llama.from_pretrained(
                repo_id=model_name,
                filename=filename,
                n_ctx=4096,
                n_batch=8,
                # chat_format="mistral-instruct",
                # verbose=True,
                n_gpu_layers=35
            )
        except Exception as e:
            logger.error(f"An error occurred in creating custom model instance: {e}")
    
    def load_grammar(self, file_path = "../model_files/json.gbnf") -> LlamaGrammar:
        """
        Loads the grammar from a specified file path.

        Returns:
            LlamaGrammar: The loaded grammar object.
        """
        try:
            with open(file_path, "r") as handler:
                content = handler.read()
            return LlamaGrammar.from_string(content)
        except FileNotFoundError as e:
            logger.error(f"Grammar file not found: {e}")
            raise

    def generate(self, prompt: str) -> str:
        """
        Generates text based on a given prompt using the model.

        Args:
            prompt (str): The prompt to generate text for.

        Returns:
            str: The generated text.
        """
        try:
            if self.model is None:
                logger.error(f"Custom model is not initialised. Terminating....")
                os._exit(-1)
            response = self.model.create_completion(
                prompt,
                max_tokens=-1, 
                grammar=self.load_grammar()
            )
            output = response["choices"][0]["text"]
            output = output.replace("'", '"').strip().rstrip(",")
            return output
        except Exception as e:
            logger.error(f"Error generating completion: {e}")
            raise

    async def a_generate(self, prompt: str) -> Awaitable[str]:
        """
        Asynchronously generates text based on a given prompt using the model.

        Args:
            prompt (str): The prompt to generate text for.

        Returns:
            Awaitable[str]: An awaitable that resolves to the generated text.
        """
        return self.generate(prompt)

    def get_model_name(self) -> str:
        """
        Returns the name of the model.

        Returns:
            str: The model name.
        """
        return "Custom model"

def main() -> None:
    """
    Main function to demonstrate the usage of CustomModel.
    """
    try:
        custom_model = CustomModel()
        prompt = "Explain the difference between water and ice."
        output = custom_model.generate(prompt)
        logger.info(f"Generated text: {output}")
    except Exception as e:
        logger.error(f"An error occurred in main: {e}")

if __name__ == "__main__":
    main()