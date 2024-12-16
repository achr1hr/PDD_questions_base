from flask import Flask, render_template, send_file
import sqlite3
from io import BytesIO

app = Flask(__name__)


# Database connection function
def get_db_connection():
    conn = sqlite3.connect('pdd_tickets.db')
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name
    return conn


# Route to display a specific ticket (question)
@app.route('/ticket/<int:ticket_id>')
def ticket(ticket_id):
    conn = get_db_connection()
    ticket = conn.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,)).fetchone()
    conn.close()

    print(f"Ticket ID {ticket_id}: {ticket}")  # Debugging output to check the ticket data

    if ticket is None:
        return f"Ticket with ID {ticket_id} not found.", 404

    # Prepare the image (if available)
    image_data = ticket['image']
    image = None
    if image_data:
        image = BytesIO(image_data)

    return render_template('ticket.html', ticket=ticket, image=image)


# Route to display a list of all tickets
@app.route('/')
def index():
    conn = get_db_connection()
    tickets = conn.execute('SELECT * FROM tickets').fetchall()
    conn.close()

    return render_template('index.html', tickets=tickets)


# Route to serve images
@app.route('/image/<int:ticket_id>')
def image(ticket_id):
    conn = get_db_connection()
    ticket = conn.execute('SELECT image FROM tickets WHERE id = ?', (ticket_id,)).fetchone()
    conn.close()

    if ticket and ticket['image']:
        return send_file(BytesIO(ticket['image']), mimetype='image/png')
    else:
        return "Image not found.", 404


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
