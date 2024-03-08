from quart import Quart, request, jsonify, send_from_directory, url_for
from pymongo import MongoClient
from bson import ObjectId
import os
from werkzeug.utils import secure_filename
import jwt
from flask_socketio import SocketIO

app = Quart(__name__)
socketio = SocketIO(app)

class DatabaseManager:
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['flask_mongodb_crud']
        self.collection = self.db['tasks']

    async def get_tasks(self, query_params=None):
        tasks = await self.collection.find(query_params).to_list(length=None)
        return tasks

    async def get_task(self, task_id):
        task = await self.collection.find_one({'_id': ObjectId(task_id)})
        return task

    async def create_task(self, data):
        task_id = await self.collection.insert_one(data)
        return str(task_id.inserted_id)

    async def update_task(self, task_id, data):
        result = await self.collection.update_one({'_id': ObjectId(task_id)}, {'$set': data})
        return result.modified_count == 1

    async def delete_task(self, task_id):
        result = await self.collection.delete_one({'_id': ObjectId(task_id)})
        return result.deleted_count == 1

database_manager = DatabaseManager()

SECRET_KEY = 'secret!'

def validate_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return 'Token expired. Please log in again.'
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.'

@app.before_request
async def check_jwt():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'No token provided'}), 401
    token = token.split('Bearer ')[-1]
    payload = validate_token(token)
    if isinstance(payload, str):
        return jsonify({'error': payload}), 401
    # Attach payload to request for use in subsequent functions
    request.jwt_payload = payload

@app.route('/tasks', methods=['GET'])
async def get_tasks():
    query_params = await request.args.to_dict()
    tasks = await database_manager.get_tasks(query_params)
    return jsonify({'tasks': tasks}), 200

@app.route('/tasks/<task_id>', methods=['GET'])
async def get_task(task_id):
    task = await database_manager.get_task(task_id)
    if task:
        return jsonify(task), 200
    return jsonify({'error': 'Task not found'}), 404

@app.route('/tasks', methods=['POST'])
async def create_task():
    data = await request.form.to_dict()
    if 'image' in (files := await request.files):
        image_file = files['image']
        if image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_path = os.path.join('uploads', filename)
            await image_file.save(image_path)
            data['image'] = url_for('uploaded_file', filename=filename)
    task_id = await database_manager.create_task(data)
    socketio.emit('task_created', str(task_id))
    return jsonify({'task_id': task_id}), 201

@app.route('/tasks/<task_id>', methods=['PUT'])
async def update_task(task_id):
    data = await request.form.to_dict()
    if 'image' in (files := await request.files):
        image_file = files['image']
        if image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_path = os.path.join('uploads', filename)
            await image_file.save(image_path)
            data['image'] = url_for('uploaded_file', filename=filename)
    if await database_manager.update_task(task_id, data):
        socketio.emit('task_updated', task_id)
        return jsonify({'message': 'Task updated successfully'}), 200
    return jsonify({'error': 'Task not found'}), 404

@app.route('/tasks/<task_id>', methods=['DELETE'])
async def delete_task(task_id):
    if await database_manager.delete_task(task_id):
        socketio.emit('task_deleted', task_id)
        return jsonify({'message': 'Task deleted successfully'}), 200
    return jsonify({'error': 'Task not found'}), 404

@app.route('/uploads/<filename>')
async def uploaded_file(filename):
    return await send_from_directory('uploads', filename)

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, debug=True)
