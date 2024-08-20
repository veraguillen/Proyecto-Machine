from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey,Table
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Tabla intermedia para la relación muchos a muchos entre actores y películas
# Definición de la tabla intermedia
actor_movie_association = Table(
    'actor_movie', Base.metadata,
    Column('id_actor', Integer, ForeignKey('actors.id_actor')),
    Column('id_pelicula', Integer, ForeignKey('movies.id_pelicula'))
)




class Movies(Base):
    __tablename__ = 'movies'
    id_pelicula = Column(Integer, primary_key=True)
    title = Column(String(255))
    release_date = Column(String(50))  # Ajustar el tipo según el formato de la fecha
    vote_average = Column(Float)
    vote_count = Column(Integer)
    revenue = Column(Float)
    budget = Column(Float)
    roi=Column(Float)
    overview=Column(String(50))
   
    # Foreign key para la relación con Directors
    id_director = Column(Integer, ForeignKey("directors.id_director"))
    # Relación con Actors
    actors = relationship("Actores", secondary=actor_movie_association, back_populates="movies")
    # Relación con el modelo Directors
    directors = relationship("Directores", back_populates="movies")
    
   



class Genres(Base):
    __tablename__ = 'genres'
    id_genero = Column(Integer, primary_key=True)
    nombre_genero = Column(String(255))




class Directores(Base):
    __tablename__ = 'directors'
    id_director = Column(Integer, primary_key=True)
    id_pelicula=Column(Integer)
    director_name = Column(String(255))
     # Relación con Movies
    movies = relationship("Movies", back_populates="directors")
    # Relación con Movies

    # Relación con Movies (relación uno a muchos)
    movies = relationship("Movies", back_populates="directors")





class Actores(Base):
    __tablename__ = 'actors'
    id_actor = Column(Integer, primary_key=True)
    id_pelicula=Column(String(255))
    nombre_actor = Column(String(255))
    genero= Column(String(255))
    
    # Relación con Movies (se define después de la clase Movies)
     # Relación con Movies
    movies = relationship("Movies", secondary=actor_movie_association, back_populates="actors")
    







# Configura la URL de conexión
DATABASE_URL = 'mysql+pymysql://root:root1234@mysql_container:3306/machine'
# Crea el motor de base de datos
engine = create_engine(DATABASE_URL, echo=True)

# Crea una sesión local para interactuar con la base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Inicializa la base de datos
def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
