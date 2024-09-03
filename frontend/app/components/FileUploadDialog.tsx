// FileUploadDialog.tsx
import React, { useCallback, useMemo } from 'react';
import { useDropzone } from 'react-dropzone';
import { FiUploadCloud, FiCheckCircle, FiAlertCircle } from 'react-icons/fi';
import { toast } from 'react-toastify'; // Add this import
import { useAuthStore } from '../store';
import { useFileUploadStore } from '../store';

interface FileUploadDialogProps {
  onUploadComplete: (files: File[]) => void;
}

const FileUploadDialog: React.FC<FileUploadDialogProps> = ({ onUploadComplete }) => {
  const { isUploading, uploadStatus, setIsUploading, setUploadStatus, setUploadedFiles, clearUploadedFiles } = useFileUploadStore();
  const { getAuthHeader } = useAuthStore.getState();

  const allowedExtensions = ['.pdf', '.txt', '.docx', '.csv'];

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const invalidFiles = acceptedFiles.filter(file => {
      const extension = '.' + file.name.split('.').pop()?.toLowerCase();
      return !allowedExtensions.includes(extension);
    });

    if (invalidFiles.length > 0) {
      const invalidFileNames = invalidFiles.map(file => file.name).join(', ');
      alert(`The following files are not allowed: ${invalidFileNames}\nPlease only upload .pdf, .txt, .docx, or .csv files.`);
      return;
    }

    clearUploadedFiles();
    setIsUploading(true);
    setUploadedFiles(acceptedFiles);
    onUploadComplete(acceptedFiles);
    console.log('Files selected:', acceptedFiles.map(f => ({name: f.name, size: f.size})));
    setUploadStatus('Uploading files...');

    try {
      const headers = await getAuthHeader();
      // Remove Content-Type header to let the browser set it with the boundary
      delete (headers as Record<string, string>)['Content-Type'];

      const formData = new FormData();
      acceptedFiles.forEach((file) => {
        formData.append('files', file, file.name);
      });

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 seconds timeout

      const response = await fetch('/api/actions/uploadFile', {
        method: 'POST',
        headers: headers,
        body: formData,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      setUploadStatus('Files uploaded successfully!');
      setUploadedFiles(acceptedFiles);
      onUploadComplete(acceptedFiles);
      toast.success('Files uploaded successfully!');
    } catch (error) {
      console.error('Error uploading files:', error);
      let errorMessage = 'Failed to upload files. Please try again.';
      if (error instanceof Error && error.name === 'AbortError') {
        errorMessage = 'Upload timed out. Please try again.';
      }
      setUploadStatus(`Error uploading files: ${errorMessage}`);
      toast.error(errorMessage);
    } finally {
      setIsUploading(false);
    }
  }, [getAuthHeader, onUploadComplete, setIsUploading, setUploadStatus, setUploadedFiles, allowedExtensions, clearUploadedFiles]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/csv': ['.csv']
    }
  });

  return (
    <div className="flex items-center justify-center h-full bg-gray-50">
      <div className="w-full max-w-md p-8 bg-white rounded-lg shadow-lg">
        <div 
          {...getRootProps()} 
          className={`flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-lg transition-colors duration-200 ease-in-out ${
            isDragActive ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-blue-400'
          }`}
        >
          <input {...getInputProps()} />
          <FiUploadCloud className="w-12 h-12 mb-4 text-gray-400" />
          {isDragActive ? (
            <p className="text-lg font-medium text-blue-500">Drop the files here ...</p>
          ) : (
            <p className="text-lg font-medium text-gray-600">
              Drag & drop files or click to select
            </p>
          )}
          <p className="mt-2 text-sm text-gray-500">
            Supported formats: PDF, TXT, DOCX, CSV
          </p>
        </div>
        {uploadStatus && (
          <div className={`mt-4 p-3 rounded-lg flex items-center ${
            isUploading ? 'bg-blue-50 text-blue-700' : 
            uploadStatus.includes('Error') ? 'bg-red-50 text-red-700' : 
            'bg-green-50 text-green-700'
          }`}>
            {isUploading ? (
              <FiUploadCloud className="w-5 h-5 mr-2" />
            ) : uploadStatus.includes('Error') ? (
              <FiAlertCircle className="w-5 h-5 mr-2" />
            ) : (
              <FiCheckCircle className="w-5 h-5 mr-2" />
            )}
            <p className="text-sm">{uploadStatus}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default FileUploadDialog;
