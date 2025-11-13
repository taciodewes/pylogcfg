"""
Pacote principal de configuração e gerenciamento de logging assíncrono.

Oferece inicialização centralizada de loggers com suporte a:
- Formatação JSON estruturada
- Manipulação assíncrona via QueueListener
- Rotação automática de arquivos de log

Uso:
    from pylogcfg import obter_logger

    logger = obter_logger("meuapp")
    logger.info("Aplicação iniciada")
"""

from importlib import import_module
from typing import Any

__all__ = ["obter_logger"]


def obter_logger(*args: Any, **kwargs: Any):
    """
    Inicializa e retorna um logger configurado.
    Implementa importação preguiçosa do módulo interno pylogcfg.
    """
    modulo = import_module(".pylogcfg", __package__)
    return modulo.obter_logger(*args, **kwargs)
