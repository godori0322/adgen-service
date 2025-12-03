export async function resizeImage(file: File, maxSize = 1024): Promise<File> {
  return new Promise((resolve) => {
    const img = new Image();
    img.src = URL.createObjectURL(file);

    img.onload = () => {
      let { width, height } = img;
      const scale = maxSize / Math.max(width, height);

      if (scale >= 1) return resolve(file); // 리사이즈 불필요 시 원본 반환

      width = width * scale;
      height = height * scale;

      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext("2d");
      ctx!.drawImage(img, 0, 0, width, height);

      canvas.toBlob(
        (blob) => {
          resolve(
            new File([blob!], file.name, {
              type: file.type,
            })
          );
        },
        file.type,
        0.9
      );
    };
  });
}
