import os

_BACKEND_NAME = 'sdxl'


def set_backend(name: str | None):
    global _BACKEND_NAME
    normalized = (name or 'sdxl').strip().lower()
    if normalized in {'sdxl', 'flux'}:
        _BACKEND_NAME = normalized
    else:
        _BACKEND_NAME = 'sdxl'
    return _BACKEND_NAME


def get_backend_name() -> str:
    return _BACKEND_NAME


def get_backend_config() -> dict:
    return {
        'name': get_backend_name(),
        'is_flux': get_backend_name() == 'flux',
        'is_sdxl': get_backend_name() == 'sdxl',
    }


def get_backend_from_env() -> str:
    return set_backend(os.environ.get('IMAGINEX_BACKEND', 'sdxl'))


def resolve_backend(name: str | None = None) -> str:
    if name is not None:
        return set_backend(name)
    return get_backend_from_env()
