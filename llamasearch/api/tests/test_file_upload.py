import asyncio
import os
import hashlib
from fastapi import UploadFile
from llamasearch.api.utils import handle_file_upload, get_file_size_and_partial_md5
import tempfile

async def simulate_http_upload(file_path, user_upload_dir):
    with open(file_path, 'rb') as f:
        file_content = f.read()
    
    temp_file = tempfile.SpooledTemporaryFile()
    temp_file.write(file_content)
    temp_file.seek(0)

    upload_file = UploadFile(filename=os.path.basename(file_path), file=temp_file)
    results = await handle_file_upload([upload_file], user_upload_dir)
    return upload_file, results

async def simulate_ws_upload(file_path, user_upload_dir):
    with open(file_path, 'rb') as f:
        file_content = f.read()
    
    file_data = [{
        'filename': os.path.basename(file_path),
        'content': file_content
    }]
    results = await handle_file_upload(file_data, user_upload_dir)
    return results

async def main():
    user_upload_dir = 'test_uploads'
    os.makedirs(user_upload_dir, exist_ok=True)

    pdf_files = [
        '/home/deval/Documents/Work/Deval/ES/LlamaSearch/data/sample-docs/slim/uploads/T0wDP1JGrmdKSZWSRLBPRAT8zvE2/RAG_Survey_Paper.pdf',
        '/home/deval/Documents/Work/Deval/ES/LlamaSearch/data/sample-docs/slim/uploads/T0wDP1JGrmdKSZWSRLBPRAT8zvE2/Reduce_Hallucinations_RAG_Paper.pdf'
    ]

    for pdf_file in pdf_files:
        print(f"\nTesting file: {os.path.basename(pdf_file)}")

        # HTTP Upload
        print("Simulating HTTP upload...")
        upload_file, http_results = await simulate_http_upload(pdf_file, user_upload_dir)
        print(f"HTTP upload results: {http_results}")

        # Get initial MD5 for HTTP upload
        http_size, http_md5 = await get_file_size_and_partial_md5(upload_file)
        print(f"Initial HTTP File - Size: {http_size}, MD5: {http_md5}")

        # WebSocket Upload
        print("\nSimulating WebSocket upload...")
        ws_results = await simulate_ws_upload(pdf_file, user_upload_dir)
        print(f"WebSocket upload results: {ws_results}")

        # Get initial MD5 for WebSocket upload
        with open(pdf_file, 'rb') as f:
            content = f.read()
        ws_size, ws_md5 = await get_file_size_and_partial_md5({'filename': os.path.basename(pdf_file), 'content': content})
        print(f"Initial WS File   - Size: {ws_size}, MD5: {ws_md5}")

        # Compare initial MD5 hashes
        if http_md5 == ws_md5:
            print("\nSuccess: Initial MD5 hashes match for both upload methods.")
        else:
            print("\nFailure: Initial MD5 hashes do not match for the upload methods.")

if __name__ == "__main__":
    asyncio.run(main())
