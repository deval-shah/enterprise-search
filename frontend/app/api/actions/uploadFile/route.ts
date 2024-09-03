import { NextRequest, NextResponse } from 'next/server';
import { apiConfig } from '@/config';

export async function POST(request: NextRequest) {
  const authHeader = request.headers.get('Authorization');
  console.log("Auth header received:", authHeader);

  if (!authHeader) {
    return NextResponse.json({ error: 'No authorization header provided' }, { status: 401 });
  }

  try {
    const formData = await request.formData();
    const files = formData.getAll('files');

    if (files.length === 0) {
      return NextResponse.json({ error: 'No files provided' }, { status: 400 });
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), apiConfig.timeout);

    // Create a new FormData object to send to the backend
    const backendFormData = new FormData();
    files.forEach((file, index) => {
      backendFormData.append('files', file as Blob, (file as File).name);
    });

    const response = await fetch(`${apiConfig.baseUrl}/api/v1/uploadfile`, {
      method: 'POST',
      headers: {
        'Authorization': authHeader,
      },
      body: backendFormData,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    console.log("Backend response status:", response.status);

    if (!response.ok) {
      const errorData = await response.text();
      console.log("Backend error:", errorData);
      return NextResponse.json({ error: `Failed to upload files: ${errorData}` }, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json({ fileUpload: data.file_upload });
  } catch (error) {
    console.error('Error uploading files:', error);
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        return NextResponse.json({ error: 'Request timed out' }, { status: 504 });
      }
    }
    return NextResponse.json({ error: 'Server error' }, { status: 500 });
  }
}
