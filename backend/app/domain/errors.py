"""Errores de dominio. La capa HTTP los traduce a códigos de respuesta."""


class DomainError(Exception):
    """Base de los errores de negocio."""


class InvalidActivityError(DomainError):
    """Los datos de una actividad no permiten calcular EVM."""
