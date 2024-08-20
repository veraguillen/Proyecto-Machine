from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, text ,func
from sqlalchemy.orm import sessionmaker, Session
import joblib
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.exc import SQLAlchemyError
from typing import List,Union, Dict
import os
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from pathlib import Path
# Crear la aplicación FastAPI
from models import SessionLocal, Movies

app = FastAPI()

from models import SessionLocal, Movies, Genres
from database import get_db  # Ajusta esta importación según la estructura de tu proyecto

BASE_PATH = "//app//joblib"
VECTORIZER_PATH = os.path.join(BASE_PATH, "vectorizer.pkl")
TFIDF_MATRIX_PATH = os.path.join(BASE_PATH, "tfidf_matrix.pkl")


def load_vectorizer():
    if os.path.exists(VECTORIZER_PATH):
        return joblib.load(VECTORIZER_PATH)
    else:
        raise FileNotFoundError(f"No se encontró el archivo del vectorizador en la ruta: {VECTORIZER_PATH}")

def load_tfidf_matrix():
    if os.path.exists(TFIDF_MATRIX_PATH):
        return joblib.load(TFIDF_MATRIX_PATH)
    else:
        raise FileNotFoundError(f"No se encontró el archivo de la matriz TF-IDF en la ruta: {TFIDF_MATRIX_PATH}")

try:
    vectorizer = load_vectorizer()
    tfidf_matrix = load_tfidf_matrix()
except Exception as e:
    print(f"Error al cargar los archivos: {e}")


# Configuración de la base de datos MySQL
DATABASE_URL = "mysql+pymysql://root:root1234@mysql_container/machine"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear una instancia de la base de datos para su uso
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()




@app.get("/cantidad_filmaciones_dia/")
def cantidad_filmaciones_dia(dia: str = Query(..., description="Día de la semana en español")):
    dias_validos = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    dia = dia.lower()  # Convertir a minúsculas para asegurar insensibilidad al caso
    
    if dia not in dias_validos:
        raise HTTPException(status_code=400, detail="Día no válido")
    
    query = text("""
        SELECT 
            CASE DAYOFWEEK(release_date)
                WHEN 1 THEN 'domingo'
                WHEN 2 THEN 'lunes'
                WHEN 3 THEN 'martes'
                WHEN 4 THEN 'miércoles'
                WHEN 5 THEN 'jueves'
                WHEN 6 THEN 'viernes'
                WHEN 7 THEN 'sábado'
            END AS dia_semana,
            COUNT(*) AS cantidad_peliculas
        FROM movies
        GROUP BY dia_semana
        HAVING dia_semana = :dia;
    """)

    try:
        with engine.connect() as connection:
            result = connection.execute(query, {"dia": dia}).fetchone()

        if result:
            return {"dia": dia, "cantidad_peliculas": result[1]}  # Usar índice para acceder a la cantidad
        else:
            return {"dia": dia, "cantidad_peliculas": 0}

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")







@app.get("/cantidad_filmaciones_mes/")
def cantidad_filmaciones_mes(mes: str = Query(..., description="Mes del año en español")):
    meses_validos = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
        "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
    }
    
    mes = mes.lower()  # Convertir el mes a minúsculas
    
    if mes not in meses_validos:
        raise HTTPException(status_code=400, detail="Mes no válido")
    
    mes_numero = meses_validos[mes]
    
    query = text("""
        SELECT 
            MONTH(release_date) AS mes_numero,
            COUNT(*) AS cantidad_peliculas
        FROM movies
        WHERE MONTH(release_date) = :mes
        GROUP BY mes_numero;
    """)

    try:
        with engine.connect() as connection:
            result = connection.execute(query, {"mes": mes_numero}).fetchone()

        if result:
            # Acceso a los resultados usando índices
            return {"mes": mes, "cantidad_peliculas": result[1]}  # result[1] es 'cantidad_peliculas'
        else:
            return {"mes": mes, "cantidad_peliculas": 0}

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")







@app.get("/votos_titulo/", tags=["Votos de Película por Título"])
def votos_titulo(titulo_de_la_filmación: str = Query(..., description="Título de la película"), db: Session = Depends(get_db)):
    titulo_de_la_filmación = titulo_de_la_filmación.lower().strip()
    
    try:
        # Realizar la consulta en SQLAlchemy
        pelicula = db.query(Movies).filter(func.lower(Movies.title) == titulo_de_la_filmación).first()
        
        if pelicula:
            if pelicula.vote_count >= 2000:
                # Extraer el año de la fecha de estreno
                try:
                    release_year = datetime.strptime(pelicula.release_date, "%Y-%m-%d").year
                except ValueError:
                    raise HTTPException(status_code=500, detail="Formato de fecha no válido en la base de datos")
                
                return {
                    "titulo": pelicula.title,
                    "estreno": release_year,
                    "cantidad_votos": pelicula.vote_count,
                    "promedio_votos": pelicula.vote_average
                }
            else:
                return {"mensaje": "La película no cumple con el requisito de tener al menos 2000 valoraciones."}
        else:
            return {"mensaje": "No se encontró ninguna película con ese título."}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Error en la consulta: " + str(e))








@app.get("/score_titulo/", tags=["Puntaje de Película por Título"])
def score_titulo(titulo_de_la_filmación: str = Query(..., description="Título de la película"), db: Session = Depends(get_db)):
    titulo_de_la_filmación = titulo_de_la_filmación.lower().strip()
    
    try:
        pelicula = db.query(Movies).filter(func.lower(Movies.title) == titulo_de_la_filmación).first()
        
        if pelicula:
            return {
                "titulo": pelicula.title,
                "estreno": pelicula.release_date,
                "score": pelicula.vote_average
            }
        else:
            return {"mensaje": "No se encontró ninguna película con ese título."}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al consultar la base de datos")










from models import  actor_movie_association
from models import Actores
@app.get("/get_actor/", tags=["Información de Actor"])
def get_actor(nombre_actor: str = Query(..., description="Nombre del actor"), db: Session = Depends(get_db)):
    nombre_actor = nombre_actor.lower().strip()

    try:
        # Buscar el actor por nombre
        actor = db.query(Actores).filter(func.lower(Actores.nombre_actor) == nombre_actor).first()
        if not actor:
            return {"message": "No se encontró el actor."}

        # Buscar las películas en las que el actor ha participado
        movies = db.query(Movies).join(actor_movie_association).filter(actor_movie_association.c.id_actor == actor.id_actor).all()

        # Construir la lista de películas con detalles requeridos
        movies_info_list = []
        for movie in movies:
            movies_info_list.append({
                "title": movie.title,
                "release_date": movie.release_date,
                "revenue": movie.revenue,
                "budget": movie.budget,
                "profit": (movie.revenue - movie.budget) if movie.revenue is not None and movie.budget is not None else None,
                "roi": movie.roi
            })

        # Calcular el éxito total y ROI total
        total_revenue = sum(movie["revenue"] for movie in movies_info_list if movie["revenue"] is not None)
        total_roi = sum(movie["roi"] for movie in movies_info_list if movie["roi"] is not None)
        
        return {
            "actor": nombre_actor.capitalize(),
            "total_revenue": round(total_revenue, 2),
            "total_roi": round(total_roi, 2),
            "movies": movies_info_list
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="Error en la consulta: " + str(e))












from models import Directores

@app.get("/get_director/", tags=["Información de Director"])
def get_director(nombre_director: str = Query(..., description="Nombre del director"), db: Session = Depends(get_db)):
    nombre_director = nombre_director.lower().strip()

    try:
        # Buscar el director por nombre
        director = db.query(Directores).filter(
            func.lower(Directores.director_name) == nombre_director
        ).first()

        if not director:
            return {"mensaje": "No se encontró ningún director con ese nombre."}

        # Obtener las películas dirigidas por el director
        movies_info = db.query(Movies).filter(
            Movies.id_director == director.id_director
        ).all()

        # Construir la lista de películas con los detalles requeridos
        movies_info_list = []
        total_revenue = 0
        total_roi = 0

        for movie in movies_info:
            ganancia = (movie.revenue - movie.budget) if movie.revenue is not None and movie.budget is not None else None
            roi = (ganancia / movie.budget) if movie.budget is not None and ganancia is not None else None

            movies_info_list.append({
                "titulo": movie.title,
                "fecha_lanzamiento": movie.release_date,
                "retorno": movie.revenue,
                "costo": movie.budget,
                "ganancia": ganancia,
                "roi": roi
            })

            if movie.revenue is not None:
                total_revenue += movie.revenue
            if roi is not None:
                total_roi += roi

        return {
            "director": nombre_director.capitalize(),
            "cantidad_peliculas": len(movies_info_list),
            "exito_total": round(total_revenue, 2),
            "roi_total": round(total_roi, 2),
            "peliculas": movies_info_list
        }

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Error en la consulta: " + str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error inesperado: " + str(e))

     
 
       








try:
    vectorizer = load_vectorizer()
    tfidf_matrix = load_tfidf_matrix()
except Exception as e:
    print(f"Error al cargar los archivos: {e}")

# Definición de modelos Pydantic
class MovieQuery(BaseModel):
    title: str

class RecommendationResponse(BaseModel):
    title: str
    

def recommend_movies(title: str, tfidf_matrix, vectorizer, top_n: int = 5):
    new_texts = [title]
    new_tfidf_matrix = vectorizer.transform(new_texts)
    similarities = cosine_similarity(new_tfidf_matrix, tfidf_matrix)
    similar_indices = similarities[0].argsort()[-top_n:][::-1]
    return similar_indices

@app.post("/recommend/", response_model=Union[List[RecommendationResponse], dict], tags=["Recomendaciones"])
async def get_recommendations(query: MovieQuery, db: Session = Depends(get_db)):
    try:
        # Convertir el título a minúsculas para la búsqueda
        title_lower = query.title.lower()
        
        # Verificar si el título de la película está en el DataFrame (insensible a mayúsculas/minúsculas)
        movie_exists = db.query(Movies).filter(func.lower(Movies.title).like(f"%{title_lower}%")).first()
        if not movie_exists:
            return {"message": "No se encontró el film."}
        
        # Obtener las recomendaciones
        similar_indices = recommend_movies(query.title, tfidf_matrix, vectorizer)
        
        # Limitar las recomendaciones a 5
        recommended_movies = []
        for idx in similar_indices[:5]:  # Limitar a 5 resultados
            movie = db.query(Movies).filter(Movies.id_pelicula == idx).first()
            if movie:
                recommended_movies.append({
                    "title": movie.title
                })
        
        if not recommended_movies:
            return {"message": "No encontramos recomendaciones."}
        
        return recommended_movies

    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al obtener las recomendaciones: " + str(e))





# Iniciar el servidor Uvicorn si se ejecuta el script directamente
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)