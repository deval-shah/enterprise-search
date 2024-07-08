// app/actions/uploadFiles.ts

'use server'

import { revalidatePath } from 'next/cache'

export async function updateUploadState(prevState: any, formData: FormData) {
  const response = await fetch('/api/actions/uploadFile', {
    method: 'POST',
    body: formData,
  })

  const data = await response.json()

  if (!response.ok) {
    return { error: data.error || 'Failed to upload files' }
  }

  revalidatePath('/chat')
  return { success: true, fileUpload: data.fileUpload }
}