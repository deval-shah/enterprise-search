import pytest
from unittest.mock import patch, MagicMock
from llamasearch.generate_datasets import DatasetGenerator  # Replace with the correct import path

@pytest.fixture
def mock_config():
    with patch('llamasearch.settings.config') as mock_config:
        mock_config.dataset_generator.use_openai = True
        mock_config.dataset_generator.model_name = 'gpt-3.5-turbo'
        yield mock_config

@pytest.fixture
def mock_logger():
    with patch('llamasearch.logger.logger') as mock_logger:
        yield mock_logger

@pytest.fixture
def mock_openai():
    with patch('llama_index.llms.openai.OpenAI') as mock_openai:
        yield mock_openai

@pytest.fixture
def mock_ollama():
    with patch('llama_index.llms.ollama.Ollama') as mock_ollama:
        yield mock_ollama

@pytest.fixture
def mock_sentence_splitter():
    with patch('llama_index.core.node_parser.SentenceSplitter') as mock_sentence_splitter:
        yield mock_sentence_splitter

@pytest.fixture
def mock_directory_reader():
    with patch('llama_index.core.SimpleDirectoryReader') as mock_directory_reader:
        yield mock_directory_reader

@pytest.fixture
def mock_generate_qa_pairs():
    with patch('llamasearch.embeddings.generate_qa_embedding_pairs') as mock_generate_qa_pairs:
        yield mock_generate_qa_pairs

@pytest.fixture
def dataset_generator(mock_config, mock_openai, mock_ollama, mock_sentence_splitter, mock_directory_reader):
    return DatasetGenerator(data_path="mock_data_path", result_file_path="mock_result_file_path")

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