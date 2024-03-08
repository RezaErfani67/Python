
from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['flask_mongodb_crud']
collection = db['tasks']

# Routes for CRUD operations
@app.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = list(collection.find())
    return jsonify({'tasks': tasks}), 200

@app.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    task = collection.find_one({'_id': ObjectId(task_id)})
    if task:
        return jsonify(task), 200
    return jsonify({'error': 'Task not found'}), 404

@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.json
    task_id = collection.insert_one(data).inserted_id
    socketio.emit('task_created', str(task_id))
    return jsonify({'task_id': str(task_id)}), 201

@app.route('/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.json
    result = collection.update_one({'_id': ObjectId(task_id)}, {'$set': data})
    if result.modified_count == 1:
        socketio.emit('task_updated', task_id)
        return jsonify({'message': 'Task updated successfully'}), 200
    return jsonify({'error': 'Task not found'}), 404

@app.route('/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    result = collection.delete_one({'_id': ObjectId(task_id)})
    if result.deleted_count == 1:
        socketio.emit('task_deleted', task_id)
        return jsonify({'message': 'Task deleted successfully'}), 200
    return jsonify({'error': 'Task not found'}), 404

# Socket.IO events
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, debug=True)
