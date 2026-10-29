import sqlite3

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

BD = "biblioteca.db"


def conectar():
    conexion = sqlite3.connect(BD)
    conexion.row_factory = sqlite3.Row
    return conexion


def preparar_bd():
    conexion = conectar()
    conexion.execute("""
        CREATE TABLE IF NOT EXISTS libro (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            autor TEXT NOT NULL,
            anio INTEGER
        )
    """)
    total = conexion.execute("SELECT COUNT(*) FROM libro").fetchone()[0]
    if total == 0:
        conexion.executemany(
            "INSERT INTO libro (titulo, autor, anio) VALUES (?, ?, ?)",
            [
                ("Cien años de soledad", "Gabriel García Márquez", 1967),
                ("Pedro Páramo", "Juan Rulfo", 1955),
                ("Fundamentos de bases de datos", "Silberschatz", 2006),
            ],
        )
    conexion.commit()
    conexion.close()


preparar_bd()


@app.get("/")
def inicio():
    return {"mensaje": "Mi primera API funciona"}


@app.get("/libros")
def listar_libros():
    conexion = conectar()
    filas = conexion.execute("SELECT id, titulo, autor, anio FROM libro").fetchall()
    conexion.close()
    return [dict(fila) for fila in filas]

@app.get("/libros/{libro_id}")
def obtener_libro(libro_id: int):
    conexion = conectar()
    fila = conexion.execute(
        "SELECT id, titulo, autor, anio FROM libro WHERE id = ?", (libro_id,)
    ).fetchone()
    conexion.close()
    if fila is None:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return dict(fila)

class LibroNuevo(BaseModel):
    titulo: str
    autor: str
    anio: int


@app.post("/libros", status_code=201)
def crear_libro(libro: LibroNuevo):
    conexion = conectar()
    cursor = conexion.execute(
        "INSERT INTO libro (titulo, autor, anio) VALUES (?, ?, ?)",
        (libro.titulo, libro.autor, libro.anio),
    )
    conexion.commit()
    nuevo_id = cursor.lastrowid
    conexion.close()
    return {"id": nuevo_id, "titulo": libro.titulo, "autor": libro.autor, "anio": libro.anio}

@app.get("/total")
def contar_libros():
    conexion = conectar()
    total = conexion.execute("SELECT COUNT(*) FROM libro").fetchone()[0]
    conexion.close()
    return {"total": total}
