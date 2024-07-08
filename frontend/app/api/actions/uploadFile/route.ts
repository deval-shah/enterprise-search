// api/actions/uploadFile/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  const authHeader = request.headers.get('Authorization');
  console.log("Auth header received:", authHeader);

  if (!authHeader) {
    return NextResponse.json({ error: 'No authorization header provided' }, { status: 401 });
  }

  try {
    const formData = await request.formData();
    const files = formData.getAll('files') as File[];

    if (files.length === 0) {
      return NextResponse.json({ error: 'No files provided' }, { status: 400 });
    }

    const response = await fetch('http://localhost:8010/api/v1/uploadfile/', {
      method: 'POST',
      headers: {
        'Authorization': authHeader,
      },
      body: formData,
      credentials: 'include',
    });

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
    return NextResponse.json({ error: 'Server error' }, { status: 500 });
  }
}

