from pydantic import BaseModel
from fastapi import FastAPI, Request
from fastapi import Depends, HTTPException, status, Cookie, Response
from typing import Annotated
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
class User(BaseModel):
    nome: str
    senha: str
    bio: str

users_db = [
    {"nome": "joão", "bio": "Professor de Python", "senha":"12345"},
    {"nome": "maria", "bio": "Desenvolvedora Web", "senha":"123456789"},
]

@app.get("/", response_class=HTMLResponse)
async def getRoot(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="signin.html",
        context={}
    )

@app.post("/users")
async def postUser(user: User, response: Response):
    for u in users_db:
        if u["nome"] == user.nome:
            raise HTTPException(status_code=418, detail="Usuário já existe")
    users_db.append(user.dict())
    response.set_cookie(key="session_user", value=user.nome)
    return {"usuario": user.nome}

@app.get("/login", response_class=HTMLResponse)
async def getLogin(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="login.html",
        context={}
    )

@app.post("/login")
async def postLogin(user: User, response: Response):
    usuario_encontrado = None
    for u in users_db:
        if u["nome"] == user.nome:
            usuario_encontrado = u
            break
    
    if not usuario_encontrado:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # O servidor diz ao navegador: "Guarde esse nome no cookie 'session_user'"
    response.set_cookie(key="session_user", value=user.nome)
    return {"message": "Logado com sucesso", "usuario": user.nome}


async def get_active_user(session_user: Annotated[str | None, Cookie()] = None):
    # O FastAPI busca automaticamente um cookie chamado 'session_user'
    if not session_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acesso negado: você não está logado."
        )
    
    user = next((u for u in users_db if u["nome"] == session_user), None)
    if not user:
        raise HTTPException(status_code=401, detail="Sessão inválida")
    
    return user

@app.get("/home", response_class=HTMLResponse)
async def getHome(request: Request, user: dict = Depends(get_active_user)):
     return templates.TemplateResponse(
        request=request, 
        name="home.html",
        context={ "user": user }
    )