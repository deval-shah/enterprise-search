import pytest
from unittest.mock import patch, MagicMock
from llamasearch.generate_datasets import DatasetGenerator  # Replace with the correct import path

class TestResultPrinter:
    @staticmethod
    def print_test_result(test_name: str, response):
        print(f"\n{'=' * 80}")
        print(f"Test: {test_name}")
        print(f"{'-' * 80}")
        print(f"Response: {response}")
        print(f"{'-' * 80}")

        print(f"{'=' * 80}\n")
class TestDatasetGenerator:
    
    def test_data_integrity(self): 
        generator=DatasetGenerator(data_path="./data/eval/document/",result_file_path="./tests/",no_node_limit=1)
        generator.no_node_limit=self.no_node_limit=2
        self.dataset=generator.generate_dataset(save_results_flag=True)
        TestResultPrinter.print_test_result("test_data_integrity", self.dataset)
        assert len(self.dataset)>0
        assert "queries" in self.dataset, "queries key missing from dataset"
        assert "corpus" in self.dataset, "corpus key missing from dataset"
        assert "relevant_docs" in self.dataset, "relevant_docs is missing"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])