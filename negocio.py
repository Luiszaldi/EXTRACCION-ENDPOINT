import sqlite3
import xml.etree.ElementTree as ET

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

app = FastAPI(title="API de Los Hambriados")

BD = "negocio.db"


def conectar():
    conexion = sqlite3.connect(BD)
    conexion.row_factory = sqlite3.Row
    return conexion


def preparar_bd():
    conexion = conectar()
    # Tabla adaptada a tu esquema de menu
    conexion.execute("""
        CREATE TABLE IF NOT EXISTS menu (
            id_platillo INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_plato TEXT NOT NULL,
            precio REAL NOT NULL,
            descripcion TEXT
        )
    """)
    total = conexion.execute("SELECT COUNT(*) FROM menu").fetchone()[0]
    if total == 0:
        # Datos de ejemplo para tu restaurante
        conexion.executemany(
            "INSERT INTO menu (nom_plato, precio, descripcion) VALUES (?, ?, ?)",
            [
                ("Hamburguesa Doble", 125.50, "Carne 100% de res con queso cheddar y tocino"),
                ("Tacos al Pastor (5 pzas)", 85.00, "Acompañados de piña, cebolla y cilantro"),
                ("Refresco 600ml", 35.00, "Frío en lata o botella"),
            ],
        )
    conexion.commit()
    conexion.close()


preparar_bd()


# Modelo de datos recibido al crear o actualizar
class DatosPlatillo(BaseModel):
    nom_plato: str
    precio: float
    descripcion: str | None = None


@app.get("/")
def inicio():
    return {"mensaje": "La API de Los Hambriados funciona correctamente"}


# R de CRUD (leer todos los platillos)
@app.get("/menu")
def listar_platillos():
    conexion = conectar()
    filas = conexion.execute(
        "SELECT id_platillo, nom_plato, precio, descripcion FROM menu"
    ).fetchall()
    conexion.close()
    return [dict(fila) for fila in filas]


# R de CRUD (leer un platillo por ID)
@app.get("/menu/{id_platillo}")
def obtener_platillo(id_platillo: int):
    conexion = conectar()
    fila = conexion.execute(
        "SELECT id_platillo, nom_plato, precio, descripcion FROM menu WHERE id_platillo = ?",
        (id_platillo,),
    ).fetchone()
    conexion.close()
    if fila is None:
        raise HTTPException(status_code=404, detail="Platillo no encontrado")
    return dict(fila)


# C de CRUD (crear platillo)
@app.post("/menu", status_code=201)
def crear_platillo(datos: DatosPlatillo):
    conexion = conectar()
    cursor = conexion.execute(
        "INSERT INTO menu (nom_plato, precio, descripcion) VALUES (?, ?, ?)",
        (datos.nom_plato, datos.precio, datos.descripcion),
    )
    conexion.commit()
    nuevo_id = cursor.lastrowid
    conexion.close()
    return {"id_platillo": nuevo_id, **datos.model_dump()}


# U de CRUD (actualizar platillo)
@app.put("/menu/{id_platillo}")
def actualizar_platillo(id_platillo: int, datos: DatosPlatillo):
    conexion = conectar()
    cursor = conexion.execute(
        "UPDATE menu SET nom_plato = ?, precio = ?, descripcion = ? WHERE id_platillo = ?",
        (datos.nom_plato, datos.precio, datos.descripcion, id_platillo),
    )
    conexion.commit()
    cambiadas = cursor.rowcount
    conexion.close()
    if cambiadas == 0:
        raise HTTPException(status_code=404, detail="Platillo no encontrado")
    return {"id_platillo": id_platillo, **datos.model_dump()}


# D de CRUD (eliminar platillo)
@app.delete("/menu/{id_platillo}")
def eliminar_platillo(id_platillo: int):
    conexion = conectar()
    cursor = conexion.execute("DELETE FROM menu WHERE id_platillo = ?", (id_platillo,))
    conexion.commit()
    borradas = cursor.rowcount
    conexion.close()
    if borradas == 0:
        raise HTTPException(status_code=404, detail="Platillo no encontrado")
    return {"mensaje": f"Platillo con ID {id_platillo} eliminado"}


# Reto: la misma lista del menú, pero en formato XML
@app.get("/menu-xml")
def listar_menu_xml():
    conexion = conectar()
    filas = conexion.execute("SELECT * FROM menu").fetchall()
    conexion.close()
    raiz = ET.Element("menu")
    for fila in filas:
        registro = ET.SubElement(raiz, "platillo")
        for columna in fila.keys():
            ET.SubElement(registro, columna).text = str(fila[columna])
    xml_texto = ET.tostring(raiz, encoding="unicode")
    return Response(content=xml_texto, media_type="application/xml")