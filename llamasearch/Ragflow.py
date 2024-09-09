
import argparse
from typing import Any, Dict, List, Optional, Sequence
from llama_index.core.callbacks.base import CallbackManager
from llama_index.core.node_parser.interface import NodeParser
from llama_index.core.node_parser.node_utils import build_nodes_from_splits
from llama_index.core.schema import BaseNode, MetadataMode, TextNode
from llama_index.core.utils import get_tqdm_iterable
from llamasearch.logger import logger
from llamasearch.ragflow.rag.app.one import chunk


class RagflowNodeParser(NodeParser):
    """A custom Node Parser using deepDoc
    Splits a document into chunks with positional metadata to create better chunk relationships using Ragflow 
    Args:
        include_metadata (bool): whether to include metadata in nodes
        heading_level (int): level of heading to split on
    """

    @classmethod
    def from_defaults(
        cls,
        include_metadata: bool = True,
        include_prev_next_rel: bool = True,
        callback_manager: Optional[CallbackManager] = None,
    ) -> "CustomNodeParser":
        callback_manager = callback_manager or CallbackManager([])

        return cls(
            include_metadata=include_metadata,
            include_prev_next_rel=include_prev_next_rel,
            callback_manager=callback_manager,
        )

    @classmethod
    def class_name(cls) -> str:
        """Get class name."""
        return "RagflowNodeParser"
    
    
    def get_nodes_from_documents(
        self,
        documents,
        **kwargs: Any,
    ) -> List[BaseNode]:
        """Parse documents into Nodes.

        Args:
            documents (Sequence[Document]): documents to parse
            show_progress (bool): whether to show progress bar
        """
        document_path=list(set([x.metadata ['file_path'] for x in documents]))
        nodes=self._parse_nodes(document_path)
        return nodes
    
    def _parse_nodes(
        self,
        paths: List[str],
        **kwargs: Any,
    ) -> List[BaseNode]:
        def dummy(prog=None, msg=""):
            pass
        all_nodes=[]
        for path in paths:  
            
            docs,chunks_with_meta_data=chunk(path,from_page=0, to_page=10,callback=dummy)
            if path.endswith('pdf'):
                for chunks in chunks_with_meta_data:
                    all_nodes.append(TextNode(text=chunks['text']))
            else :
                for chunks in docs:
                   
                    all_nodes.append(TextNode(text=chunks['content_ltks']))

        return all_nodes
    
if __name__ == "__main__":
    def dummy(prog=None, msg=""):
        pass
    logger = CustomLogger.setup_logger(__name__, save_to_disk=True, log_dir='./logs', log_name='app.log')
    logger.debug("This debug message includes the file and line number.")
    logger.info("This info message does not include the file and line number.")
    logger.warning("This is a warning message.")
    logger.error("This error message includes the file and line number.")
    logger.critical("This critical message includes the file and line number.")
