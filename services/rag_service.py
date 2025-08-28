import logging
from typing import Any, List

import numpy as np
import magic

from db.repos.embedding_repo import EmbeddingRepo
from db.repos.rag_source_repo import RagSourceRepo
from services.temp_file_service import TempFilesService
from services.text_service import TextService
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader, JSONLoader
from utils.custom_loaders import ExcelLoader

logger = logging.getLogger(__name__)


class RagArchiveProcessor:
    """Сервис для обработки архивов и создания векторных представлений."""

    def __init__(
            self,
            source_repo: RagSourceRepo,
            embedding_repo: EmbeddingRepo,
            text_service: TextService,
            temp_files: TempFilesService,
            model_name_or_path: str,
    ):
        self.source_repo = source_repo
        self.embedding_repo = embedding_repo
        self.text_service = text_service
        self.temp_files = temp_files
        self.model_name_or_path = model_name_or_path

    async def process_archive(self, archive_file: Any, source_id: str) -> int:
        """
        Обработка архива и создание векторных представлений.
        Возвращает количество обработанных чанков.
        """
        logger.info("Starting archive processing")
        chunks_count = 0
        files_list = None

        try:
            # Очистка старых эмбеддингов
            self.embedding_repo.delete_by_source_id(source_id)

            # Распаковка архива и получение списка файлов
            files_list = self.temp_files.extract_and_store_files(archive_file)

            # Загрузка и обработка файлов
            combined_text = self._load_files(files_list)

            # Создание и сохранение чанков
            chunks = self.text_service.split_text_into_chunks(combined_text)
            chunks_count = len(chunks)  #

            embeddings = self.text_service.create_embeddings_from_chunks(
                chunks,
                self.model_name_or_path,
            )
            self.embedding_repo.insert_data(embeddings, chunks, source_id)

            logger.info(f"Archive processing completed successfully. Processed {chunks_count} chunks")
            return chunks_count

        except Exception as e:
            logger.error(f"Error processing archive: {str(e)}")
            raise

        finally:
            if files_list:
                self.temp_files.clean_up_temp_files(files_list)

    def _load_files(self, file_paths: List[str]) -> str:
        """Загрузка и объединение содержимого файлов."""
        combined_text = []

        for file_path in file_paths:
            try:
                loader = self._get_loader(file_path)
                if loader:
                    logger.info(f"Loading file: {file_path}")
                    documents = loader.load()
                    for doc in documents:
                        if doc.page_content.strip():  # проверяем, что контент не пустой
                            combined_text.append(doc.page_content)
                            logger.info(f"Successfully loaded content from {file_path}")
                else:
                    logger.warning(f"No suitable loader found for file: {file_path}")
            except Exception as e:
                logger.error(f"Error loading file {file_path}: {str(e)}", exc_info=True)

        if not combined_text:
            logger.warning("No text was extracted from any files")

        return "\n".join(combined_text)

    @staticmethod
    def _get_loader(file_path: str) -> Any:
        """Определение подходящего загрузчика для файла."""
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(file_path)
        logger.info(f"Detected MIME type for {file_path}: {file_type}")

        if file_type == "application/json":
            logger.info(f"Using JSONLoader for {file_path}")
            return JSONLoader(
                file_path=file_path,
                jq_schema='. | tostring',
                text_content=True
            )

        if file_type.startswith("text"):
            logger.info(f"Using TextLoader for {file_path}")
            return TextLoader(file_path)

        elif file_type == "application/pdf":
            logger.info(f"Using PyPDFLoader for {file_path}")
            return PyPDFLoader(file_path)

        elif file_type in [
            "application/vnd.ms-excel",  # .xls
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
            "application/x-excel",
        ]:
            logger.info(f"Using ExcelLoader for {file_path}")
            return ExcelLoader(file_path)

        elif file_type in [
            "application/msword",  # .doc
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
            "application/vnd.ms-word.document.12",
        ]:
            logger.info(f"Using Docx2txtLoader for {file_path}")
            return Docx2txtLoader(file_path)

        logger.warning(f"No suitable loader found for file type: {file_type}")
        return None
