#you can send query like this
# query {
#   authors{
#     name
#     books{
#       title
#       author{
#         name
#       }
#     }
#   }
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

# Connect to MongoDB
client = AsyncIOMotorClient('mongodb://localhost:27017')
db = client['library']
books_collection = db['books']
authors_collection = db['authors']

# Define your queries
@strawberry.type
class Query:
    @strawberry.field
    async def books(self) -> List[Book]:
        books = []
        async for document in books_collection.find():
            author_id = str(document['author'])
            author_document = await authors_collection.find_one({'_id': ObjectId(author_id)})
            author = Author(id=author_id, name=author_document['name'], books=[])
            books.append(Book(id=str(document['_id']), title=document['title'], author=author))
        return books

    @strawberry.field
    async def authors(self) -> List[Author]:

        #simple query
        # authors = []
        # async for document in authors_collection.find():
        #     author_books = []
        #     async for book_document in books_collection.find({'author': document['_id']}):
        #         author_books.append(Book(id=str(book_document['_id']), title=book_document['title'], author=document['_id']))
        #     authors.append(Author(id=str(document['_id']), name=document['name'], books=author_books))
        # return authors


        #complex query
        authors = []
        async for author_document in authors_collection.find():
            books = []
            async for book_document in books_collection.find({'author': author_document['_id']}):
                author = Author(id=str(author_document['_id']),name=author_document['name'], books=[])
                book = Book(id=str(book_document['_id']),title=book_document['title'], author=author)
                books.append(book)
            author = Author(id=str(author_document['_id']),name=author_document['name'], books=books)
            authors.append(author)
        return authors

# Define your mutations
@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_author(self, name: str) -> Author:
        result = await authors_collection.insert_one({'name': name})
        return Author(id=str(result.inserted_id), name=name, books=[])

    @strawberry.mutation
    async def update_author(self, author_id: str, name: str) -> Author:
        result = await authors_collection.update_one({'_id': ObjectId(author_id)}, {'$set': {'name': name}})
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Author not found")
        return Author(id=author_id, name=name, books=[])

    @strawberry.mutation
    async def delete_author(self, author_id: str) -> str:
        result = await authors_collection.delete_one({'_id': ObjectId(author_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Author not found")
        await books_collection.delete_many({'author': ObjectId(author_id)})
        return author_id

    @strawberry.mutation
    async def create_book(self, title: str, author_id: str) -> Book:
        result = await books_collection.insert_one({'title': title, 'author': ObjectId(author_id)})
        return Book(id=str(result.inserted_id), title=title, author=author_id)

    @strawberry.mutation
    async def update_book(self, book_id: str, title: str) -> Book:
        result = await books_collection.update_one({'_id': ObjectId(book_id)}, {'$set': {'title': title}})
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Book not found")
        return Book(id=book_id, title=title, author=None)

    @strawberry.mutation
    async def delete_book(self, book_id: str) -> str:
        result = await books_collection.delete_one({'_id': ObjectId(book_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Book not found")
        return book_id

# Create GraphQL app
graphql_app = GraphQL(schema=strawberry.Schema(query=Query, mutation=Mutation))

# Mount GraphQL app to FastAPI
app.mount("/graphql", graphql_app)

if __name__ == "__main__":
    import uvicorn 
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True ,workers=4)


