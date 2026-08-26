# taller-escuela
Automatizar el registro de prestamos de herramientas a los alumnos de Taller. Llevar el control de stock de las herramientas.


## Requisitos

* Python 3.x
* pip (el gestor de paquetes de Python)

## Instalación

1.  **Clona el repositorio:**
    ```bash
    git clone [https://github.com/TuUsuario/NombreDelRepositorio.git](https://github.com/TuUsuario/NombreDelRepositorio.git)
    cd NombreDelRepositorio
    ```

2.  **Crea un entorno virtual (recomendado):**
    ```powershell
    python -m venv venv
    ```

3.  **Activa el entorno virtual en PowerShell:**
    ```powershell
    .\venv\Scripts\Activate.ps1
    ```
    *Nota: Es posible que necesites habilitar la ejecución de scripts en PowerShell si no lo has hecho antes. Puedes hacerlo ejecutando `Set-ExecutionPolicy RemoteSigned` como administrador y confirmando con `Y`.*

4.  **Instala las dependencias:**
    ```powershell
    pip install -r requirements.txt
    ```

## Configuración de la base de datos

Para configurar la conexión a la base de datos, el proyecto utiliza un archivo `.env` que **no está incluido en el repositorio** por razones de seguridad. Para poner en marcha el proyecto en tu entorno local, sigue estos pasos:

1. Copia el archivo de ejemplo `.env.example` y renómbralo a `.env` en la raíz del proyecto:

    ```powershell
    copy .env.example .env
    ```

2. Abre el archivo `.env` y completa con tus propios datos de conexión a la base de datos:

    ```env
    DB_HOST=localhost
    DB_USER=tu_usuario
    DB_PASSWORD=tu_contraseña
    DB_NAME=db_pañol
    ```

3. Guarda el archivo `.env`. Este archivo será usado por el proyecto para conectar a la base de datos.

4. Cada desarrollador debe hacer este paso en su máquina local para no compartir credenciales sensibles en el repositorio.

## Archivo `config.py.example`

El proyecto también incluye un archivo `config.py.example` que sirve como plantilla para la configuración de la conexión a la base de datos en Python.

- Este archivo contiene la estructura y el código necesario para leer las variables de entorno desde el archivo `.env`.
- **No contiene datos sensibles** y sí debe estar incluido en el repositorio para que todos los desarrolladores tengan la referencia.

### Qué debe hacer cada desarrollador:

1. Copiar `config.py.example` y renombrarlo a `config.py` en la raíz del proyecto:

    ```bash
    cp config.py.example config.py
    ```

2. No modificar `config.py` para poner datos sensibles directamente, sino mantener la lectura desde las variables de entorno definidas en `.env`.

3. Así, cada uno podrá tener su configuración local sin subir claves al repositorio.
