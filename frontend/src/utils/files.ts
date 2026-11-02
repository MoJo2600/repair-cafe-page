export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} kB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function isImage(contentType: string): boolean {
  return contentType.startsWith('image/')
}

export function fileIcon(contentType: string): string {
  if (isImage(contentType)) return 'mdi-image'
  if (contentType === 'application/pdf') return 'mdi-file-pdf-box'
  return 'mdi-file-outline'
}

export function dataUrlToFile(dataUrl: string, filename: string): File {
  const [header = '', data = ''] = dataUrl.split(',')
  const mime = header.match(/:(.*?);/)?.[1] || 'image/jpeg'
  const bytes = atob(data)
  const arr = new Uint8Array(bytes.length)
  for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i)
  return new File([arr], filename, { type: mime })
}
