from youtube_transcript_api import YouTubeTranscriptApi
import re


def extract_video_id(url: str) -> str:
    """Извлекает ID видео из URL."""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'youtu\.be\/([0-9A-Za-z_-]{11})',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_transcript(video_id: str, languages=['ru', 'en']) -> list:
    """Получает субтитры для видео."""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        return transcript
    except Exception as e:
        print(f"Ошибка при получении субтитров: {e}")
        return None


def save_transcript(transcript: list, video_id: str):
    """Сохраняет только текст субтитров в txt файл."""
    if not transcript:
        return

    filename = f'sugar_transcript_{video_id}.txt'
    with open(filename, 'w', encoding='utf-8') as f:
        full_text = ' '.join(entry['text'] for entry in transcript)
        f.write(full_text)

    print(f"Текст сохранен в файл: {filename}")


def process_youtube_url(url: str):
    """Основная функция для обработки YouTube URL."""
    # Получаем ID видео
    video_id = extract_video_id(url)
    if not video_id:
        print("Не удалось извлечь ID видео из URL")
        return

    # Получаем субтитры
    transcript = get_transcript(video_id)
    if not transcript:
        print("Не удалось получить субтитры")
        return

    # Сохраняем только текст
    save_transcript(transcript, video_id)


if __name__ == "__main__":
    url = "https://www.youtube.com/watch?v=pxBQLFLei70&t=509s"
    process_youtube_url(url)