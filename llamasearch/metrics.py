from deepeval.test_case import LLMTestCaseParams
from deepeval.metrics import (
    AnswerRelevancyMetric, FaithfulnessMetric, ContextualPrecisionMetric,
    ContextualRecallMetric, ContextualRelevancyMetric, GEval
)
from typing import Dict, Any
from config import ConfigLoader

from deepeval.models import GPTModel

#model = GPTModel(max_tokens=512)
#metric = AnswerRelevancyMetric(model=model)

class MetricsEvaluator:
    """Class to initialize and manage evaluation metrics based on configuration."""
    
    def __init__(self, config_path: str = 'eval_metrics_config.yaml'):
        """
        Initializes the MetricsEvaluator instance.

        Args:
            config_path: Path to the YAML configuration file for evaluation metrics.
        """
        self.config_loader = ConfigLoader(config_path)
        self.config_loader.update_model_in_config()
        self.metrics = self.initialize_metrics()

    def initialize_metrics(self) -> Dict[str, Any]:
        """Initialize evaluation metrics using the configuration."""
        return {
            'answer_relevancy': self._init_answer_relevancy_metric(),
            'faithfulness': self._init_faithfulness_metric()
            # 'contextual_precision': self._init_contextual_precision_metric(),
            # 'contextual_recall': self._init_contextual_recall_metric(),
            # 'contextual_relevancy': self._init_contextual_relevancy_metric(),
            # 'coherence': self._init_coherence_metric(),
        }

    def _init_answer_relevancy_metric(self) -> AnswerRelevancyMetric:
        """Initializes the AnswerRelevancyMetric."""
        config = self.config_loader.config['metrics']['answer_relevancy']
        return AnswerRelevancyMetric(**config)

    def _init_faithfulness_metric(self) -> FaithfulnessMetric:
        """Initializes the FaithfulnessMetric."""
        config = self.config_loader.config['metrics']['faithfulness']
        return FaithfulnessMetric(**config)

    def _init_contextual_precision_metric(self) -> ContextualPrecisionMetric:
        """Initializes the ContextualPrecisionMetric."""
        config = self.config_loader.config['metrics']['contextual_precision']
        return ContextualPrecisionMetric(**config)

    def _init_contextual_recall_metric(self) -> ContextualRecallMetric:
        """Initializes the ContextualRecallMetric."""
        config = self.config_loader.config['metrics']['contextual_recall']
        return ContextualRecallMetric(**config)

    def _init_contextual_relevancy_metric(self) -> ContextualRelevancyMetric:
        """Initializes the ContextualRelevancyMetric."""
        config = self.config_loader.config['metrics']['contextual_relevancy']
        return ContextualRelevancyMetric(**config)

    def _init_coherence_metric(self) -> GEval:
        """Initializes the GEval (coherence) metric."""
        coherence_config = self.config_loader.config['metrics']['coherence']
        evaluation_params = [getattr(LLMTestCaseParams, param.upper()) for param in coherence_config['evaluation_params']]
        return GEval(
            name=coherence_config['name'],
            model=coherence_config['model'],
            criteria=coherence_config['criteria'],
            evaluation_params=evaluation_params
        )

    def get_metric_name(self, metric) -> str:
        """
        Retrieves the name of the metric. If the metric has a 'name' attribute, it uses that.
        Otherwise, it uses the class name of the metric.

        Args:
            metric: The metric object.

        Returns:
            The name of the metric.
        """
        # Check if the metric has a 'name' attribute and return it if exists
        metric_name = getattr(metric, 'name', None)
        if metric_name is not None:
            return metric_name
        return metric.__class__.__name__
