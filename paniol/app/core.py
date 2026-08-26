from ..data.db_manager import DatabaseManager

# Creamos una única instancia del gestor que será usada por toda la aplicación.
# Esto se conoce como un patrón Singleton (simplificado).
db_manager = DatabaseManager()