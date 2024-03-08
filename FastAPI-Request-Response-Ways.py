# 4 way of send request and recieve response in fastapi



from fastapi import FastAPI, Depends, HTTPException, status, Request, File, UploadFile, Form , Query

#------------------------------------------------------
#------------------------------------------------------
#------------------------------------------------------
#------------First Way----------InBrowser--------------

const response = await fetch("http://localhost:8000/token/", {
  method: "POST",
  headers: {
    "Content-Type": "application/x-www-form-urlencoded",
  },
  body: `username=john_doe&password=password`
});
if (!response.ok) {
  const responseData = await response.json();
  throw new Error(responseData.detail);
}
const responseData = await response.json();
const accessToken = responseData.access_token;
console.log("Access Token:", accessToken);
const responseData = await response.json();
const accessToken = responseData.access_token;
console.log("Access Token:", accessToken);

#------------------------------------------------------
#------------------------------------------------------
#------------------------------------------------------
#------------First Way-----------InServer--------------

@app.post("/token/")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    print(form_data.username)
    print(form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"} 











#------------------------------------------------------
#------------------------------------------------------
#------------------------------------------------------
#------------Second Way---------InBrowser--------------
const postData = {
  dataframe:{
    username: "john_doe",
    password: "password"
  }
};
const requestOptions = {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify(postData)
};
const apiUrl = 'http://localhost:8000/token/';
fetch(apiUrl, requestOptions)
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        console.log('Response:', data);
    })
    .catch(error => {
        console.error('There was a problem with the fetch operation:', error);
    });


#------------------------------------------------------
#------------------------------------------------------
#------------------------------------------------------
#------------Second Way-----------InServer-------------
from pydantic import BaseModel,Json
from typing import Dict
class ArbitraryJson(BaseModel):
    dataframe:Dict
@app.post("/token/")
async def login_for_access_token(arbitraryjson:ArbitraryJson):
    print(arbitraryjson.dataframe)
    return arbitraryjson










#------------------------------------------------------
#------------------------------------------------------
#------------------------------------------------------
#------------Third Way----------InBrowser--------------
let uploader = ref();
function Submit() {
  let formData = new FormData();
  formData.append("username", "john_doe");
  formData.append("password", "password");
  formData.append("file", uploader.value.files[0]);

  fetch("http://localhost:8000/token/", {
    body: formData,
    method: "post",
  }).then((response) => {
    if (!response.ok) {
      throw new Error("Network response was not ok");
    }
    return response.json();
  });
}


#------------------------------------------------------
#------------------------------------------------------
#------------------------------------------------------
#------------Third Way-----------InServer--------------
@app.post("/token/")
async def login_for_access_token(request: Request):
    try:
        form = await request.form()
        file_data = form.get('file')

        if file_data is None:
            raise HTTPException(status_code=400, detail="No file provided")

        filename = file_data.filename
        file_contents = await file_data.read()

        with open(filename, "wb") as f:
            f.write(file_contents)

        return JSONResponse(content={"filename": filename, "message": "File uploaded successfully"})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)




#------------------------------------------------------
#------------------------------------------------------
#------------------------------------------------------
#------------Forth Way----------InBrowser--------------
let uploader = ref();
  function Submit() {
  let formData = new FormData();
  formData.append("username", "john_doe");
  formData.append("password", "password");
  if(uploader.value.files[0]){ 
    formData.append("file", uploader.value.files[0]);
  }
  fetch("http://localhost:8000/items/", {
    body: formData,
    method: "post",
  }).then((response) => {
    if (!response.ok) {
      throw new Error("Network response was not ok");
    }
    return response.json();
  });
}


#------------------------------------------------------
#------------------------------------------------------
#------------------------------------------------------
#------------Forth Way-----------InServer--------------
@app.post("/items/")
async def create_item(username: str = Form(), password: str = Form(), file: UploadFile = File(None)):
    try:
        image_contents = None
        if file:
            # Read image contents if provided
            image_contents = await file.read()

        # Insert test item into MongoDB
        result = await collection.insert_one({"name": username, "description": password, "file": image_contents})

        return {"id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


