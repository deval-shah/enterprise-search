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

    def test_generate_dataset(self, dataset_generator, mock_directory_reader, mock_sentence_splitter, mock_generate_qa_pairs):
        # Arrange
        mock_documents = [MagicMock()]  # Mock documents returned by SimpleDirectoryReader
        mock_nodes = [MagicMock(), MagicMock()]  # Mock nodes returned by SentenceSplitter
        mock_directory_reader.return_value.load_data.return_value = mock_documents
        mock_sentence_splitter.return_value.get_nodes_from_documents.return_value = mock_nodes

        mock_generate_qa_pairs.return_value = {"mock_key": "mock_value"}  # Mocked QA pairs

        # Act
        dataset_generator.generate_dataset(save_results_flag=False)

        # Assert
        mock_directory_reader.return_value.load_data.assert_called_once()
        mock_sentence_splitter.return_value.get_nodes_from_documents.assert_called_once_with(mock_documents)

        # Check that each node got a unique id
        for idx, node in enumerate(mock_nodes):
            assert node.id_ == f"node_{idx}"

        mock_generate_qa_pairs.assert_called_once_with(
            mock_nodes, llm=dataset_generator.llm, num_questions_per_chunk=dataset_generator.num_questions_per_chunk
        )

    def test_generate_dataset_with_save(self, dataset_generator, mock_directory_reader, mock_sentence_splitter, mock_generate_qa_pairs, mocker):
        # Arrange
        mock_documents = [MagicMock()]
        mock_nodes = [MagicMock()]
        mock_directory_reader.return_value.load_data.return_value = mock_documents
        mock_sentence_splitter.return_value.get_nodes_from_documents.return_value = mock_nodes

        mock_generate_qa_pairs.return_value = {"mock_key": "mock_value"}

        # Mock save_results method
        mock_save_results = mocker.patch.object(dataset_generator, 'save_results')

        # Act
        dataset_generator.generate_dataset(save_results_flag=True)

        # Assert
        mock_directory_reader.return_value.load_data.assert_called_once()
        mock_sentence_splitter.return_value.get_nodes_from_documents.assert_called_once_with(mock_documents)
        mock_generate_qa_pairs.assert_called_once_with(
            mock_nodes, llm=dataset_generator.llm, num_questions_per_chunk=dataset_generator.num_questions_per_chunk
        )

        # Ensure save_results was called
        mock_save_results.assert_called_once()



if __name__ == "__main__":
    pytest.main([__file__, "-v"])