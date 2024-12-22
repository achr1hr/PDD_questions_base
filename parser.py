import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import sqlite3
import time

# Соединение с базой данных
conn = sqlite3.connect('pdd_tickets.db')
cursor = conn.cursor()

# Создаём таблицу
cursor.execute('''
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT UNIQUE,
    question_lower TEXT UNIQUE,
    correct_answer TEXT,
    image BLOB,
    explanation TEXT
)
''')
conn.commit()


def save_image(image_url):
    # Сохранение изображений, как BLOB в базе данных
    try:
        response = requests.get(image_url)
        response.raise_for_status()  # Check for errors
        image = Image.open(BytesIO(response.content))
        image_data = BytesIO()
        image.save(image_data, format='PNG')
        image_data.seek(0)
        return image_data.read()
    except requests.RequestException as e:
        print(f"Error downloading image: {e}")
        return None


def clean_answer(answer):
    # Обрезание порядкового номера при парсинге
    if answer[0].isdigit() and answer[1] == '.' and answer[2] == ' ':
        return answer[3:].strip()
    return answer.strip()



def parse_ticket_page(ticket_url):
    # Парсинг всей страницы
    try:
        response = requests.get(ticket_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        question_tags = soup.find_all('div', style="padding:5px; font-weight: bold;")
        answer_tags = soup.find_all('div', style="padding:5px; color: forestgreen; font-weight: bold;")
        image_tags = soup.find_all('div',
                                   style="margin: 0 auto !important; float: none !important; display: block; width:auto; max-width:725px;")
        explanation_tags = soup.find_all('div', id=lambda x: x and x.startswith('idDivHint'))

        # Разделение вопросов, правильных ответов, изображений и пояснений
        for question_tag, answer_tag, image_tag, explanation_tag in zip(question_tags, answer_tags, image_tags,
                                                                        explanation_tags):
            question = question_tag.text.strip() if question_tag else 'No question found'
            correct_answer = answer_tag.text.strip() if answer_tag else 'No answer found'

            correct_answer = clean_answer(correct_answer)

            # Скачивание ссылки на изображение
            image_url = None
            img_tag = image_tag.find('img') if image_tag else None
            if img_tag:
                image_url = img_tag['src']
                if image_url and not image_url.startswith('http'):
                    image_url = f"https://avto-russia.ru/pdd_abma1b1/{image_url}"  # Prepend base URL if relative path

            # Если изображение существует - сохраняем
            image_data = None
            if image_url:
                image_data = save_image(image_url)

            # Сохраняем пояснения, если существуют
            explanation = explanation_tag.text.strip() if explanation_tag else 'No explanation found'

            # Проверка, есть ли этот вопрос уже в базе данных
            cursor.execute('''
                SELECT id FROM tickets WHERE question = ?
            ''', (question,))
            existing_ticket = cursor.fetchone()

            if existing_ticket:
                # Обновление записи в бд, если уже есть такой вопрос
                cursor.execute('''
                    UPDATE tickets
                    SET correct_answer = ?, image = ?, explanation = ?
                    WHERE id = ?
                ''', (correct_answer, image_data, explanation, existing_ticket[0]))
            else:
                # Вставляем новую запись
                cursor.execute('''
                    INSERT INTO tickets (question, question_lower, correct_answer, image, explanation)
                    VALUES (?, ?, ?, ?, ?)
                ''', (question, question.lower(), correct_answer, image_data, explanation))

            conn.commit()

    except requests.RequestException as e:
        print(f"Error scraping page {ticket_url}: {e}")


def update_data():
    # Генерация ссылок, с которых парсим
    while True:
        for i in range(1, 40):
            ticket_url = f"https://avto-russia.ru/pdd_abma1b1/vesbilet{i}.html"
            parse_ticket_page(ticket_url)

        # Обновление данных происходит каждые 20 минут
        print("Waiting for 20 minutes before the next update...")
        time.sleep(1200)


update_data()

conn.close()
