import os
import shutil
import tempfile
from typing import Any, List

import patoolib


class TempFilesService:
    """Сервис для работы с временными файлами."""

    @staticmethod
    def save_uploaded_file_to_temp_zip(file: Any) -> str:
        """Сохраняет загруженный архив во временный ZIP-файл."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_zip_file:
            file.save(temp_zip_file.name)
            return temp_zip_file.name

    @staticmethod
    def extract_and_store_files(zip_path: str) -> List[str]:
        """Извлекает файлы из ZIP-архива и сохраняет их во временные файлы."""
        extracted_files = []
        temp_dir = (
            tempfile.mkdtemp()
        )  # Создаем временную директорию для распаковки архива

        try:
            # Распаковываем архив в временную директорию
            patoolib.extract_archive(zip_path, outdir=temp_dir)

            # Перебираем все файлы в этой директории и сохраняем их во временные файлы
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    with open(file_path, "rb") as f:
                        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                            temp_file.write(f.read())
                            extracted_files.append(temp_file.name)

        finally:
            # Удаляем временную директорию с распакованными файлами
            shutil.rmtree(temp_dir)

        return extracted_files

    @staticmethod
    def clean_up_temp_file(temp_file: str) -> None:
        """Удаляет временный файл."""
        if os.path.exists(temp_file):
            os.remove(temp_file)

    @staticmethod
    def clean_up_temp_files(files_list: List[str]) -> None:
        """Удаляет все временные файлы из списка."""
        for temp_file in files_list:
            TempFilesService.clean_up_temp_file(temp_file)
