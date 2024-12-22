from flask import Flask, render_template, send_file, request, jsonify, url_for
import sqlite3
from io import BytesIO

app = Flask(__name__)


def get_db_connection():
    conn = sqlite3.connect('pdd_tickets.db')
    conn.row_factory = sqlite3.Row
    return conn



@app.route('/')
def index():
    return render_template('index.html')


@app.route('/load_tickets', methods=['GET'])
def load_tickets():
    page = int(request.args.get('page', 1))
    search_query = request.args.get('search', '').lower()
    tickets_per_page = 21

    query = 'SELECT * FROM tickets'
    params = []

    if search_query:
        query += ' WHERE question_lower LIKE ?'
        params.append(f'%{search_query}%')

    query += ' LIMIT ? OFFSET ?'
    params.extend([tickets_per_page, (page - 1) * tickets_per_page])

    conn = get_db_connection()
    tickets = conn.execute(query, params).fetchall()
    conn.close()

    ticket_data = []
    for ticket in tickets:
        ticket_data.append({
            'id': ticket['id'],
            'question': ticket['question'],
            'image': url_for('image', ticket_id=ticket['id']) if ticket['image'] else None
        })

    return jsonify(ticket_data)

@app.route('/ticket/<int:ticket_id>')
def ticket(ticket_id):
    conn = get_db_connection()
    ticket = conn.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,)).fetchone()
    conn.close()

    if ticket is None:
        return f"Ticket with ID {ticket_id} not found.", 404

    image_url = url_for('image', ticket_id=ticket_id) if ticket['image'] else None

    return render_template('ticket.html', ticket=ticket, image_url=image_url)



@app.route('/image/<int:ticket_id>')
def image(ticket_id):
    conn = get_db_connection()
    ticket = conn.execute('SELECT image FROM tickets WHERE id = ?', (ticket_id,)).fetchone()
    conn.close()

    if ticket and ticket['image']:
        return send_file(BytesIO(ticket['image']), mimetype='image/png')
    else:
        return "Image not found.", 404

@app.route('/random_question', methods=['GET'])
def random_question():
    conn = get_db_connection()
    question = conn.execute('SELECT id FROM tickets ORDER BY RANDOM() LIMIT 1').fetchone()
    conn.close()
    if question:
        return jsonify({'id': question['id']})
    else:
        return jsonify({'error': 'Questions not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
