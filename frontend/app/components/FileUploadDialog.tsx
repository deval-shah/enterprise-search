// FileUploadDialog.tsx
import React, { useState, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useDropzone } from 'react-dropzone';
import { FiUploadCloud, FiCheckCircle, FiAlertCircle } from 'react-icons/fi';

interface FileUploadDialogProps {
  onUploadComplete: (files: File[]) => void;
}

const FileUploadDialog: React.FC<FileUploadDialogProps> = ({ onUploadComplete }) => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const { getAuthHeader } = useAuth();

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

    setIsUploading(true);
    setUploadStatus('Uploading files...');

    try {
      const headers = await getAuthHeader();
      delete (headers as Record<string, string>)['Content-Type'];

      const formData = new FormData();
      acceptedFiles.forEach((file) => {
        formData.append('files', file);
      });

      const response = await fetch('/api/v1/uploadfile', {  // Note: no trailing slash
        method: 'POST',
        headers: headers,
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      setUploadStatus('Files uploaded successfully!');
      onUploadComplete(acceptedFiles);
    } catch (error) {
      console.error('Error uploading files:', error);
      setUploadStatus(`Error uploading files: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsUploading(false);
    }
  }, [getAuthHeader, onUploadComplete]);

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
