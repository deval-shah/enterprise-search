import pytest
import os
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core import SimpleDirectoryReader
from llamasearch.Ragflow import RagflowNodeParser  


class TestResultPrinter:
    @staticmethod
    def print_test_result(test_name: str, response):
        print(f"\n{'=' * 80}")
        print(f"Test: {test_name}")
        print(f"{'-' * 80}")
        print(f"Response: {response}")
        print(f"{'-' * 80}")

        print(f"{'=' * 80}\n")

class TestRagflowNodeParser:
    @pytest.fixture(scope="class")
    def parser(self):
        return RagflowNodeParser()

    @pytest.fixture(scope="class")
    def test_documents(self):
        return SimpleDirectoryReader("data/test_docs/", filename_as_id=True, required_exts=[".pdf"]).load_data()

    def test_ragflow_parser_initialization(self, parser):
        assert isinstance(parser, RagflowNodeParser)
        TestResultPrinter.print_test_result("Test Ragflow Parser Initialization", type(parser))

    def test_ragflow_parser_with_documents(self, parser, test_documents):
        pipeline = IngestionPipeline(transformations=[parser])
        nodes = pipeline.run(documents=test_documents)
        TestResultPrinter.print_test_result("Test Ragflow Parser with Documents", len(nodes))
        assert len(nodes) > 0, "Parser should produce at least one node"

    def test_ragflow_parser_node_content(self, parser, test_documents):
        pipeline = IngestionPipeline(transformations=[parser])
        nodes = pipeline.run(documents=test_documents)
        TestResultPrinter.print_test_result("Test Ragflow Parser Node Content", nodes[0].get_content() if nodes else "No nodes")
        assert all(node.get_content() for node in nodes), "All nodes should have content"

    
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
        

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
