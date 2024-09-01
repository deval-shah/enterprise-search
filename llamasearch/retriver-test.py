from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.openai import OpenAI
from llama_index.llms.ollama import Ollama

documents = SimpleDirectoryReader("/home/sam/Desktop/AIML-Work/Enterprise-Search/ES-Workflow_MR2/LlamaSearch/data/eval/").load_data()


node_parser = SentenceSplitter(chunk_size=512)
nodes = node_parser.get_nodes_from_documents(documents)


for idx, node in enumerate(nodes):
    node.id_ = f"node_{idx}"


llm = Ollama(model="llama3:8b", base_url="http://localhost:11434")
vector_index = VectorStoreIndex(nodes,embed_model="local")
retriever = vector_index.as_retriever(similarity_top_k=2)

print(type(retriever))

# retrieved_nodes = retriever.retrieve("What did the author do growing up?")
# from llama_index.core.evaluation import (
#     generate_question_context_pairs,
#     EmbeddingQAFinetuneDataset,
# )
# qa_dataset = generate_question_context_pairs(
#     nodes, llm=llm, num_questions_per_chunk=2
# )
# queries = qa_dataset.queries.values()
# print(list(queries)[2])
# # [optional] save
# qa_dataset.save_json("pg_eval_dataset.json")


# from llama_index.core.evaluation import RetrieverEvaluator

# metrics = ["hit_rate", "mrr", "precision", "recall", "ap", "ndcg"]

# retriever_evaluator = RetrieverEvaluator.from_metric_names(
#     metrics, retriever=retriever
# )


# # try it out on a sample query
# sample_id, sample_query = list(qa_dataset.queries.items())[0]
# sample_expected = qa_dataset.relevant_docs[sample_id]

# eval_result = retriever_evaluator.evaluate(sample_query, sample_expected)
# print(eval_result)