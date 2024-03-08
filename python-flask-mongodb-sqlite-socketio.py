from flask import Flask, request, jsonify, send_from_directory, url_for
from flask_socketio import SocketIO
from pymongo import MongoClient
from bson import ObjectId
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
import jwt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

class DatabaseManager:
    def __init__(self, use_mongodb=True):
        self.use_mongodb = use_mongodb
        if self.use_mongodb:
            # Connect to MongoDB
            self.client = MongoClient('mongodb://localhost:27017/')
            self.db = self.client['flask_mongodb_crud']
            self.collection = self.db['tasks']
        else:
            # Configure SQLite database
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
            self.db = SQLAlchemy(app)

            # Task model for SQLite
            class Task(self.db.Model):
                id = self.db.Column(self.db.Integer, primary_key=True)
                title = self.db.Column(self.db.String(100), nullable=False)
                description = self.db.Column(self.db.String(200), nullable=False)
                image = self.db.Column(self.db.String(100), nullable=True)

                def __repr__(self):
                    return f'Task(id={self.id}, title={self.title}, description={self.description}, image={self.image})'

            # Create SQLite database tables
            with app.app_context():
                self.db.create_all()

    def get_tasks(self, query_params=None):
        if self.use_mongodb:
            query = {}
            if query_params:
                query.update(query_params)
            tasks = list(self.collection.find(query))
            return tasks
        else:
            tasks = Task.query.filter_by(**query_params).all()
            return tasks

    def get_task(self, task_id):
        if self.use_mongodb:
            task = self.collection.find_one({'_id': ObjectId(task_id)})
        else:
            task = Task.query.get(task_id)
        return task

    def create_task(self, data):
        if self.use_mongodb:
            task_id = self.collection.insert_one(data).inserted_id
        else:
            new_task = Task(title=data['title'], description=data['description'], image=data.get('image'))
            self.db.session.add(new_task)
            self.db.session.commit()
            task_id = new_task.id
        return str(task_id)

    def update_task(self, task_id, data):
        if self.use_mongodb:
            result = self.collection.update_one({'_id': ObjectId(task_id)}, {'$set': data})
            return result.modified_count == 1
        else:
            task = Task.query.get(task_id)
            if task:
                task.title = data['title']
                task.description = data['description']
                task.image = data.get('image')
                self.db.session.commit()
                return True
            return False

    def delete_task(self, task_id):
        if self.use_mongodb:
            result = self.collection.delete_one({'_id': ObjectId(task_id)})
            return result.deleted_count == 1
        else:
            task = Task.query.get(task_id)
            if task:
                self.db.session.delete(task)
                self.db.session.commit()
                return True
            return False

database_manager = DatabaseManager()

def validate_token(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return 'Token expired. Please log in again.'
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.'

@app.before_request
def check_jwt():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'No token provided'}), 401
    token = token.split('Bearer ')[-1]
    payload = validate_token(token)
    if isinstance(payload, str):
        return jsonify({'error': payload}), 401
    # Attach payload to request for use in subsequent functions
    request.jwt_payload = payload

# Routes for CRUD operations
@app.route('/tasks', methods=['GET'])
def get_tasks():
    query_params = request.args.to_dict()
    tasks = database_manager.get_tasks(query_params)
    return jsonify({'tasks': tasks}), 200

@app.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    task = database_manager.get_task(task_id)
    if task:
        return jsonify(task), 200
    return jsonify({'error': 'Task not found'}), 404

@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.form.to_dict()
    if 'image' in request.files:
        image_file = request.files['image']
        if image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            data['image'] = url_for('uploaded_file', filename=filename)
    task_id = database_manager.create_task(data)
    socketio.emit('task_created', task_id)
    return jsonify({'task_id': task_id}), 201

@app.route('/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.form.to_dict()
    if 'image' in request.files:
        image_file = request.files['image']
        if image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            data['image'] = url_for('uploaded_file', filename=filename)
    if database_manager.update_task(task_id, data):
        socketio.emit('task_updated', task_id)
        return jsonify({'message': 'Task updated successfully'}), 200
    return jsonify({'error': 'Task not found'}), 404

@app.route('/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    if database_manager.delete_task(task_id):
        socketio.emit('task_deleted', task_id)
        return jsonify({'message': 'Task deleted successfully'}), 200
    return jsonify({'error': 'Task not found'}), 404

# Route to serve uploaded images
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Socket.IO events
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, debug=True)
