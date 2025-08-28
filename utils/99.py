# from playwright.sync_api import sync_playwright
# from youtube_transcript_api import YouTubeTranscriptApi
# import time
# from datetime import datetime
# import re
#
#
# def get_full_url(partial_url):
#     return f"https://coda.io{partial_url}"
#
#
# def clean_title(title):
#     """Очищает заголовок от лишних элементов."""
#     return title.replace(' · LATOKEN', '').strip()
#
#
# def clean_text(text):
#     """Очищает текст от лишних пробелов и форматирования."""
#     # Удаляем множественные пробелы и переносы строк
#     text = re.sub(r'\s+', ' ', text)
#     # Удаляем лишние пробелы перед знаками препинания
#     text = re.sub(r'\s+([.,!?])', r'\1', text)
#     return text.strip()
#
#
# def extract_video_id_from_page(page):
#     """Извлекает ID видео из страницы."""
#     try:
#         # Пытаемся найти iframe от iframely
#         iframe = page.locator('iframe[src*="iframe.ly"]').first
#         if iframe and iframe.is_visible():
#             return "x_DMyF3GjCk"  # Для известного видео о стрессе
#
#         # Ищем обычный YouTube iframe
#         youtube_iframe = page.locator('iframe[src*="youtube.com/embed"]').first
#         if youtube_iframe and youtube_iframe.is_visible():
#             src = youtube_iframe.get_attribute('src')
#             if 'youtube.com/embed/' in src:
#                 return src.split('/')[-1].split('?')[0]
#
#     except Exception as e:
#         print(f"Error finding video ID: {e}")
#     return None
#
#
# def get_transcript(video_id: str, languages=['ru', 'en']) -> str:
#     """Получает субтитры для видео и возвращает их в виде простого текста."""
#     try:
#         transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
#         return ' '.join(entry['text'] for entry in transcript_list)
#     except Exception as e:
#         print(f"Error getting transcript: {e}")
#         return None
#
#
# def extract_page_content(page):
#     try:
#         page.wait_for_load_state('networkidle')
#         page.wait_for_timeout(2000)
#
#         title = clean_title(page.title())
#         content = page.locator('body').inner_text()
#         content = clean_text(content)
#
#         video_id = extract_video_id_from_page(page)
#         transcript = None
#         if video_id:
#             transcript = get_transcript(video_id)
#             if transcript:
#                 transcript = clean_text(transcript)
#
#         return {
#             'title': title,
#             'content': content,
#             'video_id': video_id,
#             'transcript': transcript
#         }
#     except Exception as e:
#         print(f"Error extracting content: {e}")
#         return None
#
#
# def scrape_latoken_content():
#     start_time = datetime.now()
#
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=False)
#         page = browser.new_page()
#
#         # Собираем все ссылки
#         page.goto("https://coda.io/@latoken/latoken-talent/culture-139")
#         page.wait_for_load_state('networkidle')
#         page.wait_for_timeout(2000)
#
#         # Обработка куки
#         try:
#             cookie_button = page.locator('button[aria-label="Accept cookies"]').first
#             if cookie_button.is_visible():
#                 cookie_button.click()
#                 page.wait_for_timeout(1000)
#         except:
#             print("No cookie popup or already accepted")
#
#         collected_links = []
#         elements = page.locator('[aria-expanded]').all()
#
#         # Собираем ссылки
#         for element in elements:
#             try:
#                 if not element.is_visible():
#                     continue
#
#                 if element.get_attribute('aria-expanded') == "false":
#                     element.scroll_into_view_if_needed()
#                     page.wait_for_timeout(500)
#                     element.click()
#                     page.wait_for_timeout(1000)
#
#                 links = page.locator('a[data-kr-interactive="true"]').all()
#                 for link in links:
#                     try:
#                         href = link.get_attribute('href')
#                         if href and '/@latoken/latoken-talent/' in href:
#                             full_url = get_full_url(href)
#                             if full_url not in [l['url'] for l in collected_links]:
#                                 collected_links.append({
#                                     'url': full_url
#                                 })
#                     except Exception as e:
#                         print(f"Error processing link: {e}")
#
#             except Exception as e:
#                 print(f"Error processing element: {e}")
#
#         # Посещаем каждую страницу и собираем контент
#         all_content = []
#
#         for i, link in enumerate(collected_links):
#             try:
#                 print(f"\nProcessing page {i + 1} of {len(collected_links)}")
#                 print(f"URL: {link['url']}")
#
#                 page.goto(link['url'])
#                 content = extract_page_content(page)
#
#                 if content:
#                     content['url'] = link['url']
#                     all_content.append(content)
#                     print(f"Successfully extracted content from: {content['title']}")
#                     if content['video_id']:
#                         print(f"Found video ID: {content['video_id']}")
#                         if content['transcript']:
#                             print("Successfully extracted video transcript")
#                             print(f"Transcript length: {len(content['transcript'])} characters")
#
#                 time.sleep(1)
#
#             except Exception as e:
#                 print(f"Error processing page {link['url']}: {e}")
#
#         browser.close()
#
#         # Сохраняем результаты в текстовый файл
#         timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
#         filename = f'clear_latoken_content_{timestamp}.txt'
#
#         with open(filename, 'w', encoding='utf-8') as f:
#             # Записываем метаданные
#             f.write("=== Scraping Metadata ===\n")
#             f.write(f"Start time: {start_time.isoformat()}\n")
#             f.write(f"End time: {datetime.now().isoformat()}\n")
#             f.write(f"Total pages processed: {len(all_content)}\n")
#             f.write(f"Pages with videos: {len([p for p in all_content if p.get('video_id')])}\n")
#             f.write(f"Pages with transcripts: {len([p for p in all_content if p.get('transcript')])}\n")
#             f.write("\n" + "=" * 80 + "\n\n")
#
#             # Записываем контент каждой страницы
#             for page_content in all_content:
#                 f.write(f"### {page_content['title']} ###\n")
#                 f.write(f"URL: {page_content['url']}\n\n")
#                 f.write(f"Content:\n{page_content['content']}\n\n")
#
#                 if page_content.get('transcript'):
#                     f.write("--- Video Transcript ---\n")
#                     f.write(f"{page_content['transcript']}\n")
#
#                 f.write("\n" + "=" * 80 + "\n\n")
#
#         print(f"\nResults saved to {filename}")
#         return all_content
#
#
# # Запускаем скрапинг
# content = scrape_latoken_content()
#
# # Выводим статистику
# print("\nScraping completed!")
# print(f"Total pages processed: {len(content)}")
# print(f"Pages with videos: {len([p for p in content if p.get('video_id')])}")
# print(f"Pages with transcripts: {len([p for p in content if p.get('transcript')])}")