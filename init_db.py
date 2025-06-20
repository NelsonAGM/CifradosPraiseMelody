# init_db.py
import os
from app import app, db # Asegúrate de que 'app' y 'db' se importen correctamente

# Cargar variables de entorno si es necesario para el contexto de la app
# En Render, las variables de entorno ya estarán disponibles.
# from dotenv import load_dotenv
# load_dotenv()

print("Intentando crear tablas de la base de datos...")
with app.app_context():
    db.create_all()
print("Tablas de la base de datos creadas exitosamente (o ya existían).")