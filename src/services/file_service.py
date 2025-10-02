class FileService:
    async def process_uploaded_files(self, form_data, comment_service) -> dict:
        file_path = None
        file_type = None
        image_w = None
        image_h = None

        # Для файлов используем оригинальный form_data
        image = form_data.get("image")
        text_file = form_data.get("text_file")

        if image and image.file:
            file_path, file_type, image_w, image_h = await comment_service.save_image(image)
        elif text_file and text_file.file:
            file_path, file_type = await comment_service.save_text_file(text_file)

        return {
            "file_path": file_path,
            "file_type": file_type,
            "image_w": image_w,
            "image_h": image_h
        }