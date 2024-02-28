import cProfile
import pstats
import tempfile
import shutil
import os, streamlit as st
from typing import List, Optional, Dict
from pipeline import LlamaIndexApp

def query_app(config_path: str, query: str, data_path: Optional[str] = None) -> Dict:
    """
    Loads documents, runs the ingestion pipeline, indexes documents, and queries the index.

    Args:
        config_path: The path to the configuration file.
        query: The query string to search the index.
        data_path: Optional; The path to the data directory. If provided, overrides the default path.

    Returns:
        A dictionary containing the response from querying the index.
    """
    app = LlamaIndexApp(config_path)
    if data_path:
        app.data_path = data_path
    app.load_documents()
    nodes = app.run_pipeline()
    app.index_documents(nodes)
    response = app.query_index(query)
    return response

def profile_app(config_path: str, query: str) -> None:
    """
    Profiles the performance of the query_app function.

    Args:
        config_path: The path to the configuration file.
        query: The query string to search the index.
    """
    profiler = cProfile.Profile()
    profiler.enable()
    query_app(config_path, query)
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats('cumulative')
    stats.print_stats(10)

def save_uploaded_files(directory: str, uploaded_files: List) -> List[str]:
    """
    Saves uploaded files to the specified directory and returns the list of file paths.

    Args:
        directory: The directory to save the uploaded files.
        uploaded_files: A list of uploaded files.

    Returns:
        A list of paths to the saved files.
    """
    file_paths = []
    for uploaded_file in uploaded_files:
        if uploaded_file is not None:
            file_path = os.path.join(directory, uploaded_file.name)
            # Write the uploaded file to the new file path
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            file_paths.append(file_path)
    return file_paths

if __name__ == "__main__":
    # profile_app(config_path='config.yml')
    st.title("Ask LlamaSearch")
    uploaded_files = st.file_uploader("Choose a file to upload", type=['txt', 'pdf', 'docx', 'xlsx'], accept_multiple_files=True)
    # Check if files were uploaded successfully
    if uploaded_files is not None:
        # Create a temporary directory to store the uploaded files
        temp_dir = tempfile.mkdtemp()
        # Save the uploaded files to the temporary directory
        save_uploaded_files(temp_dir, uploaded_files)
        st.success(f"Uploaded {len(uploaded_files)} files.")
    
    query = st.text_input("What would you like to ask?")
    config_path='config.yml'
    
    if st.button("Submit"):
        if not query.strip():
            st.error("Please provide the search query.")
        elif not uploaded_files:
            st.error("Please upload a file.")
        else:
            try:
                response = query_app(config_path, query, temp_dir)
                st.success(f"Response: {response}")
            except Exception as e:
                st.error(f"An error occurred: {e}")
            finally:
                # Ensure temporary directory is cleaned up
                shutil.rmtree(temp_dir, ignore_errors=True)
