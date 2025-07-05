from fastapi import FastAPI, HTTPException, Header, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
import json
import os

app = FastAPI()

# ---------------------------
# MODELOS
# ---------------------------

class Libro(BaseModel):
    id: int
    titulo: str
    autor: str
    anio: int
    categoria: str

class LibroPatch(BaseModel):
    titulo: Optional[str] = None
    autor: Optional[str] = None
    anio: Optional[int] = None
    categoria: Optional[str] = None

# ---------------------------
# AUTH
# ---------------------------

TOKEN_VALIDO = "milibrotoken123"

def verificar_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Formato de token inválido")
    token = authorization.split(" ")[1]
    if token != TOKEN_VALIDO:
        raise HTTPException(status_code=403, detail="Token inválido")

# ---------------------------
# ARCHIVO JSON
# ---------------------------

ARCHIVO_JSON = "libros.json"

def cargar_libros() -> List[Libro]:
    if os.path.exists(ARCHIVO_JSON):
        with open(ARCHIVO_JSON, "r", encoding="utf-8") as f:
            datos = json.load(f)
            return [Libro(**d) for d in datos]
    return []

def guardar_libros():
    with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
        json.dump([libro.dict() for libro in libros_db], f, indent=4, ensure_ascii=False)

# ---------------------------
# BASE DE DATOS
# ---------------------------

libros_db: List[Libro] = cargar_libros()

# ---------------------------
# ENDPOINTS
# ---------------------------

@app.get("/books", response_model=List[Libro], dependencies=[Depends(verificar_token)])
def listar_libros(skip: int = Query(0, ge=0), limit: int = Query(10, le=100)):
    return libros_db[skip:skip + limit]

@app.get("/books/{book_id}", response_model=Libro, dependencies=[Depends(verificar_token)])
def obtener_libro(book_id: int):
    for libro in libros_db:
        if libro.id == book_id:
            return libro
    raise HTTPException(status_code=404, detail="Libro no encontrado")

@app.post("/books", response_model=Libro, dependencies=[Depends(verificar_token)])
def agregar_libro(libro: Libro):
    if any(l.id == libro.id for l in libros_db):
        raise HTTPException(status_code=400, detail="Ya existe un libro con ese ID")
    libros_db.append(libro)
    guardar_libros()
    return libro

@app.patch("/books/{book_id}", response_model=Libro, dependencies=[Depends(verificar_token)])
def actualizar_libro(book_id: int, datos: LibroPatch):
    for libro in libros_db:
        if libro.id == book_id:
            update_data = datos.dict(exclude_unset=True)
            for campo, valor in update_data.items():
                setattr(libro, campo, valor)
            guardar_libros()
            return libro
    raise HTTPException(status_code=404, detail="Libro no encontrado")

@app.delete("/books/{book_id}", dependencies=[Depends(verificar_token)])
def eliminar_libro(book_id: int):
    for i, libro in enumerate(libros_db):
        if libro.id == book_id:
            del libros_db[i]
            guardar_libros()
            return {"mensaje": f"Libro con ID {book_id} eliminado"}
    raise HTTPException(status_code=404, detail="Libro no encontrado")
