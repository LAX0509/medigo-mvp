MediGo MVP

Sistema de Gestión de Citas Médicas

Descripción

MediGo es un MVP desarrollado como proyecto académico para la asignatura de Arquitectura de Software.

El sistema permite gestionar el ciclo completo de citas médicas entre pacientes y especialistas, incluyendo registro de usuarios, autenticación, creación de citas, historial clínico básico y finalización de atención médica con registro de notas, fórmulas y órdenes.

La arquitectura actual está implementada como un monolito con backend en FastAPI y base de datos MySQL.

Funcionalidades Principales

Registro de usuarios como paciente o doctor

Inicio de sesión con autenticación básica

Listado de doctores

Creación de citas médicas

Consulta de historial de citas

Cancelación de citas

Finalización de cita con:

Nota médica

Prescripciones

Órdenes médicas

Arquitectura

El sistema está organizado en:

Frontend web tipo SPA

Backend REST desarrollado en FastAPI

Base de datos relacional MySQL

Estructura del proyecto:

APP_MEDICA
│
├── backend
│ ├── main.py
│ ├── database.py
│ ├── user_router.py
│ └── medical_router.py
│
├── db
│ └── init.sql
│
├── frontend
│ └── index.html
│
└── requirements.txt

Tecnologías Utilizadas

Python

FastAPI

MySQL

bcrypt

HTML

REST API

Configuración del Proyecto
1. Clonar el repositorio

git clone https://github.com/TU_USUARIO/medigo-mvp.git

cd medigo-mvp

2. Crear entorno virtual

python -m venv venv
venv\Scripts\activate

3. Instalar dependencias

pip install -r requirements.txt

4. Configurar variables de entorno

Crear un archivo .env en la raíz del proyecto con el siguiente formato:

DB_HOST=localhost
DB_PORT=3306
DB_USER=tu_usuario
DB_PASSWORD=tu_password
DB_NAME=app_medica

5. Inicializar base de datos

Ejecutar el archivo db/init.sql en MySQL.

6. Ejecutar la aplicación

uvicorn backend.main:app --reload

La aplicación estará disponible en:

http://localhost:8000

Documentación Swagger:

http://localhost:8000/api/docs

Estado del Proyecto

Actualmente el sistema se encuentra en fase MVP con arquitectura monolítica.

En el marco del proyecto académico se propone una re-arquitectura orientada a mejorar atributos de calidad como:

Mantenibilidad

Testabilidad

Seguridad

Autor

Juan Camilo Nieto Arboleda
Estudiante de Ingeniería de Sistemas