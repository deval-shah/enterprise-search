// api/actions/handleMessage/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  const token = request.headers.get('Authorization')?.split('Bearer ')[1];
  if (!token || token === 'undefined') {
    return NextResponse.json({ error: 'No valid token provided' }, { status: 401 });
  }

  try {
    const formData = await request.formData();
    const query = formData.get('query') as string;
    const files = formData.getAll('files') as File[];

    if (!query) {
      return NextResponse.json({ error: 'No query provided' }, { status: 400 });
    }

    const formDataToSend = new FormData();
    formDataToSend.append('query', query);
    files.forEach((file) => {
      formDataToSend.append('files', file);
    });

    const response = await fetch('http://localhost:8010/api/v1/query/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formDataToSend,
    });

    if (!response.ok) {
      return NextResponse.json({ error: 'Failed to process query' }, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error processing query:', error);
    return NextResponse.json({ error: 'Server error' }, { status: 500 });
  }
}
