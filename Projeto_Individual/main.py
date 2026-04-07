from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import Cookie, FastAPI, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import SQLModel, Session, create_engine, delete, select
from models import Annotation, Book, Cookies, Following, User

### Inicializações do banco de dados
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

### Funções para comuncação com o banco de dados

# Busca usuário pelo username
# Entrada: username do usuário
# Saida: usuário com o username especificado
def select_user_by_username(username:str):
    with Session(engine) as session:
        query = select(User).where(User.username == username)
        return session.exec(query).first()

# Busca usuário pelo id
# Entrada: id do usuário
# Saida: usuário com o id especificado
def select_user_by_id(id:int):
    with Session(engine) as session:
        query = select(User).where(User.id == id)
        return session.exec(query).first()

# Busca usuários pelo nome
# Entrada: nome do usuário
# Saida: usuários com o nome parecido ao passado
def select_all_users_by_name(name:str,page:int,limit:int):
     with Session(engine) as session:
        query = select(User).where((User.name).like(f"{name}%")).offset(page*limit).limit(limit)
        return session.exec(query).all()

# Busca anotações pelo username
# Entrada: username do usuário, usuário
# Saida: anotações do usuário com o username especificado, limitada as públicas se requisitada por outros usuários
def select_annotations_by_username(username:str, user:User):
    if(username == user.username):
        query = select(Annotation).where(Annotation.username == username).order_by(Annotation.date.desc())
    else:
        query = select(Annotation).where(Annotation.username == username, Annotation.public == True).order_by(Annotation.date.desc())
    with Session(engine) as session:
        return session.exec(query).all()

# Busca anotações pelo livro
# Entrada: livro, usuário
# Saida: anotações do livro do usuário com o username especificado, limitado as públicas se requisitada por outros usuários
def select_annotations_by_book(book:Book, user:User):
    with Session(engine) as session:
        if(book.user_id == user.id):
            query = select(Annotation).where(Annotation.book_id == book.id).order_by(Annotation.date.desc())
        else:
            query = select(Annotation).where(Annotation.book_id == book.id, Annotation.public == True).order_by(Annotation.date.desc())
        return session.exec(query).all()

# Busca anotações pelo id
# Entrada: id da anotação
# Saida: anotação com id especificado
def select_annotations_by_id(id:int):
    with Session(engine) as session:
        query = select(Annotation).where(Annotation.id == id).order_by(Annotation.date.desc())
        return session.exec(query).first()

# Cria uma nova anotação
# Entrada: anotação
# Saida: nenhuma
def create_annotation(annotation:Annotation):
     with Session(engine) as session:
        session.add(annotation)
        session.commit()
        session.refresh(annotation)

# Atualiza uma anotação
# Entrada: anotação
# Saida: nenhuma
def update_annotation(annotation:Annotation,text:str,public:bool):
    with Session(engine) as session:
        annotation.text = text
        annotation.public = public
        session.add(annotation)
        session.commit()
        session.refresh(annotation)

# Deleta anotações pelo id do livro
# Entrada: id do livro
# Saida: nenhuma
def delete_annotations_by_book_id(id:int):
    with Session(engine) as session:
        query = delete(Annotation).where(Annotation.book_id == id)
        session.exec(query)
        session.commit()

# Busca livros pelo id
# Entrada: id do livro
# Saida: livro com id especificado
def select_books_by_id(id:int):
    with Session(engine) as session:
        query = select(Book).where(Book.id == id)
        return session.exec(query).first()

# Cria um novo livro
# Entrada: livro
# Saida: nenhuma
def create_book(book:Book):
    with Session(engine) as session:
        session.add(book)
        session.commit()
        session.refresh(book)

# Atualiza um livro
# Entrada: livro
# Saida: nenhuma
def update_book(book:Book, newBook:Book):
    with Session(engine) as session:
        book.title = newBook.title
        book.author = newBook.author
        book.public = newBook.public
        book.summary = newBook.summary
        session.add(book)
        session.commit()
        session.refresh(book)

# Deleta o livro pelo id
# Entrada: livro
# Saida: nenhuma
def delete_books_by_id(book:Book):
    with Session(engine) as session:
        session.delete(book)
        session.commit()
        
# Busca livros pelo username do usuário
# Entrada: username do usuário, usuário
# Saida: livros do usuário com o username especificado, limitada aos públicos se requisitado por outros usuários
def select_books_by_username(username:str, user:User):
    if(username == user.username):
        query = select(Book).where(Book.user_id == user.id).order_by(Book.date.desc())
    else:
        owner = select_user_by_username(username)
        query = select(Book).where(Book.user_id == owner.id, Book.public == True).order_by(Book.date.desc())
    with Session(engine) as session:
        return session.exec(query).all()

# Verifica se um usuário segue o outro
# Entrada: username do usuário, id de um usuário
# Saida: booleano se o usuário com username espeficicado segue o usuário com id especificado
def select_is_following_by_username(id: int, username:str):
    with Session(engine) as session:
        query = select(Following).where(Following.username == username, Following.user_id == id)
        return (session.exec(query).first() != None)
    

# Busca seguintes pelo username do usuário
# Entrada: username do usuário, usuário
# Saida: Os usuários que o usuário username espeficicado seguem
def select_following_by_username(username:str):
    user = select_user_by_username(username)
    with Session(engine) as session:
        query = select(User).join(Following, Following.username == User.username).where(Following.user_id == user.id)
        return session.exec(query).all()

# Faz com que o usuário com id especificado siga o usuário com username especificado
# Entrada: id do usuário seguidor, username do usuário seguinte
def create_follow(id:int, username:str):
    with Session(engine) as session:
        following = Following()
        following.user_id = id
        following.username = username
        session.add(following)
        session.commit()
        session.refresh(following)

# Faz com que o usuário com id especificado pare de seguir o usuário com username especificado
# Entrada: id do usuário seguidor, username do usuário seguinte
def delete_unfollow(id:int, username:str):
    with Session(engine) as session:
        query = delete(Following).where(Following.user_id == id, Following.username == username)
        session.exec(query)
        session.commit()


# Verifica se o usuário está logado e envia para a página mais relevante
@app.get("/")
async def root(request: Request, response: Response, cookies: Annotated[Cookies, Cookie()]):
    if(not cookies.session_user or not cookies.session_password):
        response = RedirectResponse(url="/signin")
    else:
        response = RedirectResponse(url="/books")
    return response


### Requisições voltadas ao usuário
# Retorna a página de login
@app.get("/signin",  tags=["users"],response_class=HTMLResponse)
async def get_signin_page(request: Request):
    return templates.TemplateResponse(request, "signin.html")

# Retorna a página de cadastro
@app.get("/signup", response_class=HTMLResponse)
async def get_signup_page(request: Request):
    return templates.TemplateResponse(request, "signup.html")

# Remove os cookies de sessão do usuário
@app.get("/logoff", response_class=HTMLResponse)
async def logoff(request: Request, response : Response):
    response = RedirectResponse(url="/signin")
    forget_logged_user(response)
    return response

# Obtem o usuário pelo cookie
def get_logged_user(cookies: Cookies):
    if not cookies.session_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Acesso negado: você não está logado.")
    user = select_user_by_username(cookies.session_user)
    if(user == None):
        raise HTTPException(status_code=401, detail="Sessão inválida")
    if(user.password != cookies.session_password):
        raise HTTPException(status_code=401, detail="Senha incorreta")
    return user

# Salva o cookie do usuário
def set_logged_user(user : User, response: Response):
    response.set_cookie(key="session_user", value=user.username)
    response.set_cookie(key="session_password", value=user.password)

# Apaga o cookie do usuário
def forget_logged_user(response: Response):
    response.delete_cookie(key="session_user")
    response.delete_cookie(key="session_password")

# Envia dados do usuário para cadastros
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

# Envia dados do usuário para login
@app.post("/signin", tags=["users"], status_code = status.HTTP_200_OK)
async def signin(user:User, response: Response, response_class=HTMLResponse):
    logging_user = select_user_by_username(user.username) 
    if(logging_user == None):
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Usuário {user.username} não está cadastrado.")
    if(logging_user.password != user.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Senha incorreta para {user.username}.")
    set_logged_user(user, response);
    return {"msg":"ok"}


### Requisições de busca
# Vai para página de busca quando clicado o botão da navbar
@app.get("/search", tags=["search"])
async def search(request: Request, response: Response,cookies: Annotated[Cookies, Cookie()],name:str = "", page:int = 0):
    user = get_logged_user(cookies)
    return templates.TemplateResponse(request, "searchUser.html",context={"user":user,"name":name,"users":[],"page":page})

# Retorna página com usuários cujo nome parece com oque foi passado
limit = 5
@app.get("/users", tags=["search"])
async def get_users(request: Request, response: Response, cookies: Annotated[Cookies, Cookie()],name:str = "", page:int = 0):
    user = get_logged_user(cookies)
    users = select_all_users_by_name(name,page,limit)
    return templates.TemplateResponse(request, "searchUser.html", context={"users":users, "name":name,"last_page" : len(users) < limit, "user":user,"page":page})


### Requisições de seguintes
# Retorna página com usuários que o usuário com username especificado segue
@app.get("/following/{username}", tags=["following"])
async def get_following(request: Request, response: Response, cookies: Annotated[Cookies, Cookie()],username:str = "", page:int = 0):
    user = get_logged_user(cookies)
    users = select_following_by_username(username)
    return templates.TemplateResponse(request, "following.html", context={"users":users, "name":username,"last_page" : len(users) < limit, "user":user,"page":page})

# Faz o usuário seguir ou parar de seguir outro
@app.post("/follow/{username}", tags=["following"])
async def follow(username:str, request: Request, response: Response,cookies: Annotated[Cookies, Cookie()], follow : Annotated[str | None, Form()] = None):
    user = get_logged_user(cookies)
    if(follow != None):
        delete_unfollow(user.id,username)
    else:
        create_follow(user.id,username)


### Requisições voltadas as anotações
# Retorna página com todos os livros salvos do usuário
@app.get("/books", tags=["books"],response_class=HTMLResponse)
async def get_saved_books_page(request: Request, cookies: Annotated[Cookies, Cookie()]):
    user = get_logged_user(cookies)
    books = select_books_by_username(user.username, user)
    return templates.TemplateResponse(request, "books.html", context={"username":user.username,"user":user,"books":books,"owner":user})

# Retorna página com todos os livros públicos do usuário com username espeficicado
@app.get("/books/{username}", tags=["books"],response_class=HTMLResponse)
async def get_user_book_page(username:str, request: Request, cookies: Annotated[Cookies, Cookie()]):
    user = get_logged_user(cookies)
    books = select_books_by_username(username, user)
    owner = select_user_by_username(username)
    following = select_is_following_by_username(user.id, username);
    return templates.TemplateResponse(request, "books.html", context={"username":username,"user":user,"books":books,"owner":owner,"following":following})

# Envia dados para criação de um livro
@app.post("/books", tags=["books"], status_code = status.HTTP_201_CREATED)
async def post_book(request: Request, response: Response, cookies: Annotated[Cookies, Cookie()], title: str = Form(), author: str = Form(), summary: Annotated[str | None, Form()] = "", visibility : Annotated[str | None, Form()] = None):
    user = get_logged_user(cookies)
    public = (visibility != None)
    book = Book(public=public,summary=summary,title=title,user_id=user.id, author=author)
    create_book(book)
    return templates.TemplateResponse(request, "savedBooks.html", context={"book": book ,"user":user,"owner":user})

# Envia dados para atualizar um livro
@app.put("/books/{id}", tags=["books"], status_code = status.HTTP_200_OK)
async def put_book(request: Request, response: Response, cookies: Annotated[Cookies, Cookie()], id: int, title: str = Form(), author: str = Form(), summary:  Annotated[str | None, Form()] = "", visibility : Annotated[str | None, Form()] = None):
    user = get_logged_user(cookies)
    public = (visibility != None)
    book = select_books_by_id(id)
    if(book == None):
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Livro não encontrado")
    if(book.user_id != user.id):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Você não pode alterar esse livro.")
    newBook = Book(public=public,summary=summary,title=title,user_id=user.id, author=author)
    update_book(book,newBook)
    return templates.TemplateResponse(request, "savedBooks.html", context={"book": book ,"user":user,"owner":user})

# Apaga um livro e suas anotações dado o id
@app.delete("/books/{id}", tags=["books"], status_code = status.HTTP_200_OK)
async def delete_book(request: Request, response: Response, cookies: Annotated[Cookies, Cookie()], id: int):
    user = get_logged_user(cookies)
    book = select_books_by_id(id)
    if(book == None):
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Livro não encontrado")
    if(book.user_id != user.id):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Você não pode deletar esse livro.")
    delete_annotations_by_book_id(book.id)
    delete_books_by_id(book)
    return {"ok":"Livro deletado"}


### Requisições voltadas a anotação
# Retorna a página das anotações de um livro com id espeficicado
@app.get("/annotation/{id}", tags=["annotation"],response_class=HTMLResponse)
async def get_book_page(id:int, request: Request, cookies: Annotated[Cookies, Cookie()]):
    user = get_logged_user(cookies)
    book = select_books_by_id(id)
    if(book == None):
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Livro não encontrado")
    if(book.user_id != user.id and book.public == False):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Você não pode ver essas anotações.")
    owner = select_user_by_id(book.user_id)
    annotations = select_annotations_by_book(book,user)
    return templates.TemplateResponse(request, "bookannotation.html", context={"user":user,"annotations":annotations,"book":book,"owner":owner})

# Verifica se usuário tem permissão para ver a
# Entrada: anotação, usuário
# Saída: booleano se o usuárop tem permissão ou não
def book_annotation_auth(annotation: Annotation, user: User):
    book = select_books_by_id(annotation.book_id)
    if(book == None):
        return False
    return (book.user_id == user.id)

# Envia dados para criar uma anotação
@app.post("/annotation", tags=["annotation"], status_code = status.HTTP_201_CREATED)
async def post_annotation(request: Request, response: Response, cookies: Annotated[Cookies, Cookie()], book_id: int, text: str = Form(), visibility : Annotated[str | None, Form()] = None):
    user = get_logged_user(cookies)
    public = (visibility != None)
    annotation = Annotation(public=public,username=user.username,text=text,book_id=book_id)
    create_annotation(annotation)
    return templates.TemplateResponse(request, "annotation.html", context={"annotation": annotation, "user":user,"owner":user},status_code = status.HTTP_201_CREATED)

# Envia dados para atualizar uma anotação
@app.put("/annotation/{id}", tags=["annotation"], status_code = status.HTTP_200_OK)
async def put_annotation(request: Request, response: Response, cookies: Annotated[Cookies, Cookie()], id: int, text: str = Form(), visibility : Annotated[str | None, Form()] = None):
    user = get_logged_user(cookies)
    public = (visibility != None)
    annotation = select_annotations_by_id(id)
    if(annotation == None):
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Anotação não encontrada")
    if(not book_annotation_auth(annotation, user)):
         raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Você não pode alterar essa anotação.")
    update_annotation(annotation,text,public)
    return templates.TemplateResponse(request, "annotation.html", context={"annotation": annotation, "user":user,"owner":user})

# Apaga uma anotação dado o id
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


### Requisições voltadas a componentes da interface
# Retorna um menu com opções de atualizar/deletar anotação
@app.get("/annotation_options_component",tags=["ui_element"])
async def get_ui_annotation_options(request: Request, id: int = 0, response_class=HTMLResponse):
    if (not "HX-Request" in request.headers):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Use a interface do sistema para fazer isso")
    return templates.TemplateResponse(request, "annotation_options.html", context={"id":id})

# Retorna um menu com opções de atualizar/deletar livro
@app.get("/book_options_component",tags=["ui_element"])
async def get_ui_book_options(request: Request, id: int = 0, response_class=HTMLResponse):
    if (not "HX-Request" in request.headers):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Use a interface do sistema para fazer isso")
    return templates.TemplateResponse(request, "book_options.html", context={"id":id})

# Retorna uma div com uma textarea para o usuário criar um livro
@app.get("/add_component",tags=["ui_element"])
async def get_ui_add(request: Request, response_class=HTMLResponse):
    if (not "HX-Request" in request.headers):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Use a interface do sistema para fazer isso")
    return templates.TemplateResponse(request, "bookwrite.html",  context={"book":{"title":"","author":"","summary":""}})

# Retorna uma div com uma textarea para o usuário criar uma anotação
@app.get("/write_component",tags=["ui_element"])
async def get_ui_write(book_id:int, request: Request, response_class=HTMLResponse):
    if (not "HX-Request" in request.headers):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Use a interface do sistema para fazer isso")
    return templates.TemplateResponse(request, "write.html", context={"id": book_id,"annotation":{"text":""}})

# Retorna uma div com uma textarea para o usuário atualizar um livro que já existe
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

# Retorna uma div com uma textarea para o usuário atualizar uma anotação que já existe
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