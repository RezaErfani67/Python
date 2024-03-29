query {
#  lessons{
#   name
#   teacher{
#     name
#     lessons{
#       name
#     }
#   }
# }
# }
from fastapi import FastAPI, HTTPException
from bson import ObjectId
import strawberry
from strawberry.asgi import GraphQL
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List

# Define your GraphQL types
@strawberry.type
class Book:
    id: str
    title: str
    author: "Author"

@strawberry.type
class Author:
    id: str
    name: str
    books: List[Book]

# Initialize FastAPI app
app = FastAPI()

lessons = [
    { 'id': "1", "name": "GraphQL", 'group': "Front", 'teacherId': '1' },
    { 'id': "2", "name": "React", 'group': "Front", 'teacherId': '1' },
    { 'id': "3", "name": "express", 'group': "Back", 'teacherId': '2' },
]

teachers = [
    { 'id': "1", 'name': "ali alaei", 'age': 32 },
    { 'id': "2", 'name': "farhad majidi", 'age': 33 },
    { 'id': "3", 'name': "masih", 'age': 34 },
]

@strawberry.type
class Lesson:
    id: str
    name: str
    group: str
    teacherId: str

    @strawberry.field
    async def teacher(self, info) -> 'Teacher': 
        for teacher in teachers:
            if teacher["id"] == self.teacherId:
                return Teacher(id=teacher['id'], name=teacher['name'], age=teacher['age'])
        return None

@strawberry.type
class Teacher:
    id: str
    name: str
    age: int
    lessons: List[Lesson]

    @strawberry.field
    async def lessons(self, info) -> List[Lesson]:
        
        teacher_id = self.id 
        teacher_lessons = [lesson for lesson in lessons if lesson['teacherId'] == teacher_id]
        return [Lesson(**lesson) for lesson in teacher_lessons]
    


@strawberry.type
class Query:
    @strawberry.field
    def lesson(self, id: str) -> Lesson:
        x=  next((lesson for lesson in lessons if lesson['id'] == id), None)
        

        lesson_data = next((lesson for lesson in lessons if lesson['id'] == id), None) 
        return Lesson(id=lesson_data['id'], name=lesson_data['name'], group=lesson_data['group'], teacherId=lesson_data['teacherId'])

    @strawberry.field
    def lessons(self) -> List[Lesson]:
        return [Lesson(id=lesson['id'], name=lesson['name'], group=lesson['group'], teacherId=lesson['teacherId']) for lesson in lessons]


# Create GraphQL app
graphql_app = GraphQL(schema=strawberry.Schema(query=Query))

# Mount GraphQL app to FastAPI
app.mount("/graphql", graphql_app)
if __name__ == "__main__":
    import uvicorn 
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True ,workers=4)
