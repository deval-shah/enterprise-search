import yaml
from typing import Dict, Any
from llamasearch.custom import CustomModel
from llamasearch.logger import logger

class ConfigLoader:
    """Class for loading and processing evaluation metrics configuration."""
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from a YAML file."""
        with open(self.config_path, 'r') as file:
            return yaml.safe_load(file)

    """Update model based on type"""
    def get_model(self, model_type, model_name):
        # Return custom model instance
        if model_type == 'custom':
            return CustomModel()
        else:
            # For API models, return the model_name as deepeval internally creates the model instance
            return model_name

    def update_model_in_config(self):
        """Updates the model in the config based on the model_type directly."""
        for metric_name, metric_config in self.config['metrics'].items():
            model_type = metric_config.get('model_type', 'api')
            if model_type == 'custom':
                logger.info("Using custom model for evalution....")
                # Assuming a function or a way to get a custom model instance
                metric_config['model'] = self.get_model(model_type, metric_config['model'])
                logger.info("Using custom model for evalution....", metric_config['model'])
            else:
                # For API models, assume using the model identifier as is or another way to handle API models
                metric_config['model'] = metric_config['model']
        for metric_name, metric_config in self.config['metrics'].items():
            del metric_config['model_type']
