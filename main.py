from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from models import Usuario, Base, SessionLocal, engine
import hashlib
from jose import JWTError, jwt
from datetime import datetime, timedelta
import bcrypt



# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Inicializar la aplicación FastAPI
app = FastAPI()

# Configurar archivos estáticos y plantillas
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Dependencia para obtener la sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Página de formulario de registro
@app.get("/")
async def mostrar_formulario(request: Request):
    return templates.TemplateResponse("registro.html", {"request": request})

# Página de formulario de login
@app.get("/login")
async def mostrar_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Procesar login con respuesta genérica
@app.post("/login")
def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == email).first()

    if usuario and bcrypt.checkpw(password.encode(), usuario.password.encode()):
        # Generar token
        expiration = datetime.utcnow() + timedelta(minutes=30)
        token = jwt.encode(
            {"sub": usuario.email, "exp": expiration},
            "ab1234",  # Puedes cambiar esta clave
            algorithm="HS256"
        )
        return JSONResponse(content={"mensaje": "Login exitoso", "token": token}, status_code=200)

    # Mensaje genérico para prevenir enumeración
    return JSONResponse(content={"mensaje": "Credenciales inválidas"}, status_code=200)


# Crear nuevo usuario con respuesta genérica
@app.post("/usuarios/")
async def crear_usuario(nombre: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    usuario_existente = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario_existente:
        # Mensaje genérico para evitar enumeración
        return JSONResponse(content={"mensaje": "Registro fallido"}, status_code=200)

    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    nuevo_usuario = Usuario(nombre=nombre, email=email, password=hashed_password.decode())


    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    return {"mensaje": f"Usuario creado con ID: {nuevo_usuario.id}"}

# Crear usuario de prueba
@app.get("/crear-prueba")
def crear_usuario_prueba(db: Session = Depends(get_db)):
    hashed_password = bcrypt.hashpw("admin".encode(), bcrypt.gensalt())
    usuario = Usuario(nombre="juan", email="juan@example.com", password=hashed_password.decode())
    db.add(usuario)
    db.commit()
    return {"mensaje": "Usuario de prueba creado"}
