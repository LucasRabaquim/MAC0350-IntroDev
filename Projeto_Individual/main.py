from contextlib import asynccontextmanager
import string
from typing import Annotated

from fastapi import Cookie, Depends, FastAPI, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import SQLModel, Session, create_engine, select
from models import Annotation, Cookies, User

@asynccontextmanager
async def initFunction(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=initFunction)
open_library_url = "https://openlibrary.org/search.json?q=test"
arquivo_sqlite = "projeto.db"
url_sqlite = f"sqlite:///{arquivo_sqlite}"

engine = create_engine(url_sqlite)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory=["Templates", "Templates/Partials"])

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@app.get("/")
async def root():
    return RedirectResponse(url="/signin")


def select_user_by_username(username:str):
    with Session(engine) as session:
        query = select(User).where(User.username == username)
        return session.exec(query).first()

def select_annotations_by_username(username:str, user:User):
    if(username == user.username):
        query = select(Annotation).where(Annotation.username == username)
    else:
        query = select(Annotation).where(Annotation.username == username and Annotation.public == True)
    with Session(engine) as session:
        return session.exec(query).all()

def select_annotations_by_id(id:int, user:User):
    with Session(engine) as session:
        query = select(Annotation).where(Annotation.id == id)
        return session.exec(query).first()

# Tag = aba quem que aparece na documentação do swagger
@app.get("/profile", tags=["users"],response_class=HTMLResponse)
async def get_profile_page(request: Request, cookies: Annotated[Cookies, Cookie()]):
    user = get_logged_user(cookies)
    annotations = select_annotations_by_username(user.username, user)
    print(annotations)
    return templates.TemplateResponse(request, "bookannotation.html", context={"user":user,"type":"annotation" ,"annotations":annotations})

@app.get("/signin",  tags=["users"],response_class=HTMLResponse)
async def get_signin_page(request: Request):
    return templates.TemplateResponse(request, "signin.html")

@app.get("/signup", response_class=HTMLResponse)
async def get_signup_page(request: Request):
    return templates.TemplateResponse(request, "signup.html")

@app.get("/logoff", response_class=HTMLResponse)
async def logoff(request: Request, response : Response):
    forget_logged_user(response)
    return RedirectResponse(url="/signin")

def get_logged_user(cookies: Cookies):
    # O FastAPI busca automaticamente um cookie chamado 'session_user'
    if not cookies.session_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acesso negado: você não está logado."
        )
    user = select_user_by_username(cookies.session_user)
    if(user == None):
        raise HTTPException(status_code=401, detail="Sessão inválida")
    if(user.password != cookies.session_password):
        raise HTTPException(status_code=401, detail="Senha incorreta")
    return user



def set_logged_user(user : User, response: Response):
    response.set_cookie(key="session_user", value=user.username)
    response.set_cookie(key="session_password", value=user.password)

def forget_logged_user(response: Response):
    response.set_cookie(key="session_user", value="")
    response.set_cookie(key="session_password", value="")
    # response.delete_cookie("session_user", path='/', domain=None)
    # response.delete_cookie("session_password", path='/', domain=None)


@app.post("/signup", tags=["users"], status_code = status.HTTP_201_CREATED)
async def signup(user: User, response: Response, response_class=HTMLResponse):
    if(select_user_by_username(user.username) != None):
        raise HTTPException(status.HTTP_409_CONFLICT, f"Usuário {user.username} já está cadastrado.")
    with Session(engine) as session:
        session.add(user)
        session.commit()
        session.refresh(user)
    set_logged_user(user, response);
    return {"msg":"ok"}
    
@app.post("/signin", tags=["users"], status_code = status.HTTP_200_OK)
async def signin(user:User, response: Response, response_class=HTMLResponse):
    logging_user = select_user_by_username(user.username) 
    if(logging_user == None):
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Usuário {user.username} não está cadastrado.")
    if(logging_user.password != user.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Senha incorreta para {user.username}.")
    set_logged_user(user, response);
    return {"msg":"ok"}



@app.get("/post_options_component",tags=["ui_element"])
async def get_ui_post_options(request: Request, type: str | None='', response_class=HTMLResponse):
    if (not "HX-Request" in request.headers):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Use a interface do sistema para fazer isso")
    if(type == 'annotation'):
        return templates.TemplateResponse(request, "post_options.html", context={"type": "annotation"})
    return templates.TemplateResponse(request, "post_options.html", context={"type": "post"})

@app.get("/write_component",tags=["ui_element"])
async def get_ui_write(request: Request, type: str | None='', response_class=HTMLResponse):
    if (not "HX-Request" in request.headers):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Use a interface do sistema para fazer isso")
    if(type == 'annotation'):
        return templates.TemplateResponse(request, "write.html", context={"type": "annotation"})
    return templates.TemplateResponse(request, "write.html", context={"type": "post"})


@app.post("/annotation", tags=["annotation"], status_code = status.HTTP_201_CREATED)
async def post_annotation(request: Request, response: Response, cookies: Annotated[Cookies, Cookie()], text: str = Form(), visibility : Annotated[str | None, Form()] = None):
    user = get_logged_user(cookies)
    public = (visibility != None)
    with Session(engine) as session:
        annotation = Annotation(user_id=user.id,public=public,username=user.username,text=text,book="a")
        session.add(annotation)
        session.commit()
        session.refresh(annotation)
    return templates.TemplateResponse(request, "post.html", context={"post": annotation, "type":"annotation" ,"user":user})

@app.delete("/annotation", tags=["annotation"], status_code = status.HTTP_200_OK)
async def delete_annotation(request: Request, response: Response, cookies: Annotated[Cookies, Cookie()], savedannotation: Annotation):
    user = get_logged_user(cookies)
    annotation = select_annotations_by_id(savedannotation.id, user)
    if(annotation == None):
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Anotação não encontrada")
    if(annotation.user_id != user.id):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Você não pode deletar essa anotação.")
    with Session(engine) as session:
        session.delete(annotation)
        session.commit()
    return ""

# @app.get("/search/books")
# async def GetByTitle(title : str, skip : int = 0, limit : int = 10):
#     title = title.replace(" ", "+")
#     url = f"https://openlibrary.org/search.json?q={title}&offset={skip}&limit={limit}"
#     response = await requests.get(url).json()
#     return response
