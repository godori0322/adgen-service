export function blobToBase64(
  blob: Blob,
  type: "image" | "video" | "audio" = "image"
): Promise<string> {
  return new Promise<string>((resolve) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result as string);

    const ext = type === "image" ? "png" : type === "video" ? "mp4" : "mp3";
    reader.readAsDataURL(new File([blob], `file.${ext}`, { type: blob.type }));
  });
}

export function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

export function blobToFile(blob: Blob, fileName: string = "file.png"): File {
  return new File([blob], fileName, { type: blob.type });
}

export function base64ToBlob(base64: string): Blob {
  const arr = base64.split(",");
  const mime = arr[0].match(/:(.*?);/)?.[1] || "";
  const bstr = atob(arr[arr.length - 1]);
  let n = bstr.length;
  const u8arr = new Uint8Array(n);
  while (n--) {
    u8arr[n] = bstr.charCodeAt(n);
  }
  return new Blob([u8arr], { type: mime });
}
