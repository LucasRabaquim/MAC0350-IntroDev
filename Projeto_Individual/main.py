from contextlib import asynccontextmanager
import string
from typing import Annotated

from fastapi import Cookie, Depends, FastAPI, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import SQLModel, Session, create_engine, delete, select
from models import Annotation, Book, Cookies, User

@asynccontextmanager
async def initFunction(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=initFunction)
arquivo_sqlite = "projeto.db"
url_sqlite = f"sqlite:///{arquivo_sqlite}"

engine = create_engine(url_sqlite)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory=["Templates", "Templates/Partials"])

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@app.get("/")
async def root(cookies: Annotated[Cookies | None, Cookie()]):
    return RedirectResponse(url="/signin")
    # if(not cookies.session_user or not cookies.session_password):
    #     return RedirectResponse(url="/signin")
    # user = select_user_by_username(cookies.session_user)
    # if(user == None or user.password != cookies.session_password):
    #     return RedirectResponse(url="/signin")
    # return RedirectResponse(url="/books")

def select_user_by_username(username:str):
    with Session(engine) as session:
        query = select(User).where(User.username == username)
        return session.exec(query).first()

def select_annotations_by_username(username:str, user:User):
    if(username == user.username):
        query = select(Annotation).where(Annotation.username == username)
    else:
        query = select(Annotation).where(Annotation.username == username, Annotation.public == True)
    with Session(engine) as session:
        return session.exec(query).all()
    
def select_books_by_id(id:int):
    with Session(engine) as session:
        query = select(Book).where(Book.id == id)
        return session.exec(query).first()
    
def delete_books_by_id(id:int):
    with Session(engine) as session:
        query = delete(Annotation).where(Annotation.book_id == id)
        session.exec(query)
        session.commit()

def select_books_by_username(username:str, user:User):
    if(username == user.username):
        query = select(Book).where(Book.user_id == user.id)
    else:
        owner = select_user_by_username(username)
        query = select(Book).where(Book.user_id == owner.id, Book.public == True)
    with Session(engine) as session:
        return session.exec(query).all()
    

def select_annotations_by_book(book:Book, user:User):
    with Session(engine) as session:
        if(book.user_id == user.id):
            query = select(Annotation).where(Annotation.book_id == book.id)
        else:
            query = select(Annotation).where(Annotation.book_id == book.id, Annotation.public == True)
        return session.exec(query).all()

def select_annotations_by_id(id:int):
    with Session(engine) as session:
        query = select(Annotation).where(Annotation.id == id)
        return session.exec(query).first()


# Tag = aba quem que aparece na documentação do swagger
@app.get("/books", tags=["books"],response_class=HTMLResponse)
async def get_saved_books_page(request: Request, cookies: Annotated[Cookies, Cookie()]):
    user = get_logged_user(cookies)
    books = select_books_by_username(user.username, user)
    return templates.TemplateResponse(request, "books.html", context={"username":user.username,"user":user,"books":books})

# Tag = aba quem que aparece na documentação do swagger
@app.get("/books/{username}", tags=["books"],response_class=HTMLResponse)
async def get_user_book_page(username:str, request: Request, cookies: Annotated[Cookies, Cookie()]):
    user = get_logged_user(cookies)
    books = select_books_by_username(username, user)
    return templates.TemplateResponse(request, "books.html", context={"username":username,"user":user,"books":books})



@app.get("/annotation/{id}", tags=["annotation"],response_class=HTMLResponse)
async def get_book_page(id:int, request: Request, cookies: Annotated[Cookies, Cookie()]):
    user = get_logged_user(cookies)
    book = select_books_by_id(id)
    if(book == None):
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Livro não encontrado")
    if(book.user_id != user.id and book.public == False):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Você não pode ver essas anotações.")
    annotations = select_annotations_by_book(book,user)
    return templates.TemplateResponse(request, "bookannotation.html", context={"user":user,"annotations":annotations,"book":book})


@app.post("/books", tags=["books"], status_code = status.HTTP_201_CREATED)
async def post_book(request: Request, response: Response, cookies: Annotated[Cookies, Cookie()], title: str = Form(), author: str = Form(), summary: Annotated[str | None, Form()] = "", visibility : Annotated[str | None, Form()] = None):
    user = get_logged_user(cookies)
    public = (visibility != None)
    with Session(engine) as session:
        book = Book(public=public,summary=summary,title=title,user_id=user.id, author=author)
        session.add(book)
        session.commit()
        session.refresh(book)
    return templates.TemplateResponse(request, "savedBooks.html", context={"book": book ,"user":user})

@app.put("/books/{id}", tags=["books"], status_code = status.HTTP_200_OK)
async def update_book(request: Request, response: Response, cookies: Annotated[Cookies, Cookie()], id: int, title: str = Form(), author: str = Form(), summary:  Annotated[str | None, Form()] = "", visibility : Annotated[str | None, Form()] = None):
    user = get_logged_user(cookies)
    public = (visibility != None)
    book = select_books_by_id(id)
    if(book == None):
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Livro não encontrado")
    if(book.user_id != user.id):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Você não pode alterar esse livro.")
    with Session(engine) as session:
        book.title = title
        book.author = author
        book.public = public
        book.summary = summary
        session.add(book)
        session.commit()
        session.refresh(book)
    return templates.TemplateResponse(request, "savedBooks.html", context={"book": book ,"user":user})

@app.delete("/books/{id}", tags=["books"], status_code = status.HTTP_200_OK)
async def delete_book(request: Request, response: Response, cookies: Annotated[Cookies, Cookie()], id: int):
    user = get_logged_user(cookies)
    book = select_books_by_id(id)
    if(book == None):
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Livro não encontrado")
    if(book.user_id != user.id):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Você não pode deletar esse livro.")
    delete_books_by_id(book.id)
    with Session(engine) as session:
        session.delete(book)
        session.commit()
    return {"ok":"Livro deletado"}


@app.get("/signin",  tags=["users"],response_class=HTMLResponse)
async def get_signin_page(request: Request):
    return templates.TemplateResponse(request, "signin.html")

@app.get("/signup", response_class=HTMLResponse)
async def get_signup_page(request: Request):
    return templates.TemplateResponse(request, "signup.html")

@app.get("/logoff", response_class=HTMLResponse)
async def logoff(request: Request, response : Response):
    response = RedirectResponse(url="/signin")
    forget_logged_user(response)
    return response

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
    response.delete_cookie(key="session_user")
    response.delete_cookie(key="session_password")
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




@app.get("/annotation_options_component",tags=["ui_element"])
async def get_ui_annotation_options(request: Request, id: int = 0, response_class=HTMLResponse):
    if (not "HX-Request" in request.headers):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Use a interface do sistema para fazer isso")
    return templates.TemplateResponse(request, "annotation_options.html", context={"id":id})

@app.get("/book_options_component",tags=["ui_element"])
async def get_ui_book_options(request: Request, id: int = 0, response_class=HTMLResponse):
    if (not "HX-Request" in request.headers):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Use a interface do sistema para fazer isso")
    return templates.TemplateResponse(request, "book_options.html", context={"id":id})


@app.get("/add_component",tags=["ui_element"])
async def get_ui_add(request: Request, response_class=HTMLResponse):
    if (not "HX-Request" in request.headers):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Use a interface do sistema para fazer isso")
    return templates.TemplateResponse(request, "bookwrite.html",  context={"book":{"title":"","author":"","summary":""}})

@app.get("/write_component",tags=["ui_element"])
async def get_ui_write(book_id:int, request: Request, response_class=HTMLResponse):
    if (not "HX-Request" in request.headers):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Use a interface do sistema para fazer isso")
    return templates.TemplateResponse(request, "write.html", context={"id": book_id,"annotation":{"text":""}})

@app.get("/add_update_component/{id}",tags=["ui_element"])
async def get_ui_add_update(request: Request, id:int,  cookies: Annotated[Cookies, Cookie()], response_class=HTMLResponse):
    if (not "HX-Request" in request.headers):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Use a interface do sistema para fazer isso")
    user = get_logged_user(cookies)
    book = select_books_by_id(id)
    if(book == None):
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Livro não encontrada")
    if(book.user_id != user.id):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Você não pode alterar esse livro.")
    return templates.TemplateResponse(request, "bookwrite.html", context={"book":book})

def book_annotation_auth(annotation: Annotation, user: User):
    book = select_books_by_id(annotation.book_id)
    if(book == None):
        return False
    return (book.user_id == user.id)

@app.get("/update_component/{id}",tags=["ui_element"])
async def get_ui_update(request: Request, id:int,  cookies: Annotated[Cookies, Cookie()], response_class=HTMLResponse):
    if (not "HX-Request" in request.headers):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Use a interface do sistema para fazer isso")
    user = get_logged_user(cookies)
    annotation = select_annotations_by_id(id)
    if(annotation == None):
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Anotação não encontrada")
    if(not book_annotation_auth(annotation, user)):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Você não pode atualizar essa anotação.")
    return templates.TemplateResponse(request, "write.html", context={"annotation":annotation})

# # Tag = aba quem que aparece na documentação do swagger
# @app.get("/annotation/{id}", tags=["annotation"],response_class=HTMLResponse)
# async def get_bannotation_page(request: Request, cookies: Annotated[Cookies, Cookie()]):
#     user = get_logged_user(cookies)
#     annotation = select_annotations_by_username(user.username, user)
#     return templates.TemplateResponse(request, "bookannotation.html", context={"user":user,"annotation":"annotation"})

@app.get("/search")
async def search(request: Request, response: Response,cookies: Annotated[Cookies, Cookie()],name:str = "", page:int = 0):
    user = get_logged_user(cookies)
    return templates.TemplateResponse(request, "searchUser.html",context={"user":user,"users":[]})

limit = 5
@app.get("/users", tags=["users"])
async def get_users(request: Request, response: Response, cookies: Annotated[Cookies, Cookie()],name:str = "", page:int = 0):
    with Session(engine) as session:
        user = get_logged_user(cookies)
        query = select(User).where((User.name).contains(name)).offset(page*limit).limit(limit)
        users = session.exec(query).all()
        return templates.TemplateResponse(request, "searchUser.html", context={"users":users, "last_page" : len(users) < limit, "user":user,"page":page},status_code = status.HTTP_201_CREATED)


# limit = 5
# @app.get("/users", tags=["users"])
# async def get_users(request: Request, response: Response,name:str = "", page:int = 0):
#     with Session(engine) as session:
#         query = select(User).where((User.name).contains(name)).offset(page*limit).limit(limit)
#         users = session.exec(query).all()
#         return templates.TemplateResponse(request,"searchUser.html",context={"request": request, "user":user,"usersr": users,"last_page": len(users) < limit,"page": page,"name": name})


@app.post("/annotation", tags=["annotation"], status_code = status.HTTP_201_CREATED)
async def post_annotation(request: Request, response: Response, cookies: Annotated[Cookies, Cookie()], book_id: int, text: str = Form(), visibility : Annotated[str | None, Form()] = None):
    user = get_logged_user(cookies)
    public = (visibility != None)
    with Session(engine) as session:
        annotation = Annotation(public=public,username=user.username,text=text,book_id=book_id)
        session.add(annotation)
        session.commit()
        session.refresh(annotation)
    return templates.TemplateResponse(request, "annotation.html", context={"annotation": annotation, "user":user},status_code = status.HTTP_201_CREATED)


@app.put("/annotation/{id}", tags=["annotation"], status_code = status.HTTP_200_OK)
async def update_annotation(request: Request, response: Response, cookies: Annotated[Cookies, Cookie()], id: int, text: str = Form(), visibility : Annotated[str | None, Form()] = None):
    user = get_logged_user(cookies)
    public = (visibility != None)
    annotation = select_annotations_by_id(id)
    if(annotation == None):
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Anotação não encontrada")
    if(not book_annotation_auth(annotation, user)):
         raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Você não pode alterar essa anotação.")
    with Session(engine) as session:
        annotation.text = text
        annotation.public = public
        session.add(annotation)
        session.commit()
        session.refresh(annotation)
    return templates.TemplateResponse(request, "annotation.html", context={"annotation": annotation, "user":user})

@app.delete("/annotation/{id}", tags=["annotation"], status_code = status.HTTP_200_OK)
async def delete_annotation(request: Request, response: Response, cookies: Annotated[Cookies, Cookie()], id: int):
    user = get_logged_user(cookies)
    annotation = select_annotations_by_id(id)
    if(annotation == None):
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Anotação não encontrada")
    if(not book_annotation_auth(annotation, user)):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Você não pode deletar essa anotação.")
    with Session(engine) as session:
        session.delete(annotation)
        session.commit()
    return ""