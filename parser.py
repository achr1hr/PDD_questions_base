import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import sqlite3
import time

# Setup database connection
conn = sqlite3.connect('pdd_tickets.db')
cursor = conn.cursor()

# Create the table if it doesn't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT UNIQUE,
    correct_answer TEXT,
    image BLOB,
    explanation TEXT
)
''')
conn.commit()


def save_image(image_url):
    """Downloads and saves an image as BLOB to database."""
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


def parse_ticket_page(ticket_url):
    """Scrapes a single ticket page and saves data."""
    try:
        response = requests.get(ticket_url)
        response.raise_for_status()  # Check for errors
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all questions on the page (this assumes that all questions have the same structure)
        question_tags = soup.find_all('div', style="padding:5px; font-weight: bold;")
        answer_tags = soup.find_all('div', style="padding:5px; color: forestgreen; font-weight: bold;")
        image_tags = soup.find_all('div', style="margin: 0 auto !important; float: none !important; display: block; width:auto; max-width:725px;")
        explanation_tags = soup.find_all('div', id=lambda x: x and x.startswith('idDivHint'))

        # Loop through all questions, answers, and explanations (assuming there are the same number of each)
        for question_tag, answer_tag, image_tag, explanation_tag in zip(question_tags, answer_tags, image_tags, explanation_tags):
            question = question_tag.text.strip() if question_tag else 'No question found'
            correct_answer = answer_tag.text.strip() if answer_tag else 'No answer found'

            # Extract the image URL (if it exists)
            image_url = None
            img_tag = image_tag.find('img') if image_tag else None
            if img_tag:
                image_url = img_tag['src']
                if image_url and not image_url.startswith('http'):
                    image_url = f"https://avto-russia.ru/pdd_abma1b1/{image_url}"  # Prepend base URL if relative path

            # Save image if it exists
            image_data = None
            if image_url:
                image_data = save_image(image_url)

            # Extract the explanation (if it exists)
            explanation = explanation_tag.text.strip() if explanation_tag else 'No explanation found'

            # Check if the question already exists in the database
            cursor.execute('''
                SELECT id FROM tickets WHERE question = ?
            ''', (question,))
            existing_ticket = cursor.fetchone()

            if existing_ticket:
                # Update the existing record if it exists
                cursor.execute('''
                    UPDATE tickets
                    SET correct_answer = ?, image = ?, explanation = ?
                    WHERE id = ?
                ''', (correct_answer, image_data, explanation, existing_ticket[0]))
            else:
                # Insert a new record if it doesn't exist
                cursor.execute('''
                    INSERT INTO tickets (question, correct_answer, image, explanation)
                    VALUES (?, ?, ?, ?)
                ''', (question, correct_answer, image_data, explanation))

            conn.commit()

    except requests.RequestException as e:
        print(f"Error scraping page {ticket_url}: {e}")


def update_data():
    """Main function to periodically scrape pages and update the database."""
    while True:
        for i in range(1, 40):  # Assuming ticket pages are numbered from 1 to 40
            ticket_url = f"https://avto-russia.ru/pdd_abma1b1/vesbilet{i}.html"
            parse_ticket_page(ticket_url)

        # Wait for 20 minutes before updating the data again
        print("Waiting for 20 minutes before the next update...")
        time.sleep(1200)  # 1200 seconds = 20 minutes


# Start updating data every 20 minutes
update_data()

conn.close()
