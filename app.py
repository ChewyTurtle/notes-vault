"""
app.py
Entry point for the Notes Vault API Flask application.
Configures the Flask app, initializes the database, and defines the API endpoints.
"""

from flask import Flask, jsonify, request
from models import db, Note

def create_app():
    # Create_app seems to be a Flask best practice
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    with app.app_context():
        db.create_all()
    
    return app

app = create_app()

@app.route('/notes', methods=['POST'])
def create_note():
    """
    Description: Create a new row in the database with the data sent to the post Endpoint
    """
    data = request.get_json()
    content = data.get('content', '') if data else ""
    
    # could just check for 'not content' but python short circuits with or statements, and this explicit approach reads cleaner
    if not data or not content:
         # immediately return error and 400, cannot write invalid content to db
         return jsonify({"error": "Request body must include content"}), 400

    elif len(content) > 10000:
        # immediately return error and 400, cannot write invalid content to db
         return jsonify({"error": "Content exceeds limit of 10,000 characters"}), 400
    # Only will create new not object and commit to db if post body is valid
    new_note = Note(content=content,
                    title=data.get('title') # will set None if no title is passed
                    )
    db.session.add(new_note)
    db.session.commit()
    return jsonify(new_note.to_dict()), 201

@app.route('/notes', methods=['GET'])
def get_notes():
    """
    Description: Run a select all on the notes db and return the results
    """
    notes = Note.query.all()
    # query.all() returns list, so either all notes will be returned, or a blank
    # list will be returned, following API conventions

    # list comprehension embedded directly in jsonify() call for conciseness
    # could extract to a separate variable if readability is a concern
    return jsonify([note.to_dict() for note in notes]), 200

@app.route('/notes/search', methods=['GET'])
# Rest path will be like /notes/search?title=shopping
def search_notes():
    """
    Description: query the database using a like filter for the title column
    """
    title = request.args.get('title', '').strip()
    if not title:
        return jsonify({"error": "Search requires a title parameter"}), 400
    notes = Note.query.filter(Note.title.ilike(f'%{title}%')).all()
    # Will return blank list or list of matches
    return jsonify([note.to_dict() for note in notes]), 200
    
@app.route('/notes/<int:id>', methods=['GET'])
def get_note(id):
    """
    Description: find note by id and return that note
    """
    note = db.session.get(Note, id)
    if not note:
        return jsonify({"error": f"Note {id} not found"}), 404
    return jsonify(note.to_dict()), 200

@app.route('/notes/<int:id>', methods=['DELETE'])
def delete_note(id):
    """
    Description: find existing note by id, verify it's present and delete that record from the db
    """
    # first retrieve note, verify it's there
    note = db.session.get(Note, id)
    if not note:
        return jsonify({"error": f"Note {id} not found"}), 404
    # then send delete command
    db.session.delete(note)
    # finally commit the delete so it's removed from the db entirely
    db.session.commit()
    return jsonify({"message": f"Note {id} deleted"}), 200

@app.route('/notes/<int:id>', methods=['PATCH'])
def update_note(id):
    """
    Description: find existing note by id and update that notes content using the PATH endpoint
    """
    note = db.session.get(Note, id)
    if not note: # Can't update note if there isn't one
        return jsonify({"error": f"Note {id} not found"}), 404
    data = request.get_json()
    if not data: # Cannot update note if there is no body data to update
        return jsonify({"error": "Request body required"}), 400
    if 'content' in data:
        content = data.get('content', '').strip()
        if len(content) > 10000: # new content has to still be less than 10,000 characters
            return jsonify({"error": "Content exceeds limit of 10,000 characters"}), 400
        note.content = content
    if 'title' in data: # optionally add title
        note.title = data.get('title')
    db.session.commit()
    return jsonify(note.to_dict()), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')