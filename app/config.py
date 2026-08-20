import os
import tempfile

def get_base_dir() -> str:
    """
    Returns writable directory base path.
    On Vercel / serverless environment where current working dir is read-only,
    uses system temporary directory (/tmp).
    """
    test_dir = os.path.join(os.getcwd(), ".write_test")
    try:
        os.makedirs(test_dir, exist_ok=True)
        os.rmdir(test_dir)
        return os.getcwd()
    except (OSError, PermissionError):
        return tempfile.gettempdir()

def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path
