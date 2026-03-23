import os
from pathlib import Path
import subprocess
import sys


BASE_DIR = Path(__file__).resolve().parent


def _read_text(relative_path: str) -> str:
    return (BASE_DIR / relative_path).read_text(encoding="utf-8")


project_structure = {
    "src": {
        "__init__.py": _read_text("src/__init__.py"),
        "database.py": _read_text("src/database.py"),
        "app.py": _read_text("src/app.py"),
    },
    "main.py": _read_text("main.py"),
    "requirements.txt": _read_text("requirements.txt"),
}


def create_project():
    print("A criar estrutura do projeto...")

    for item, content in project_structure.items():
        if isinstance(content, dict):
            os.makedirs(item, exist_ok=True)
            print(f"Pasta pronta: {item}")
            for subfile, subcontent in content.items():
                file_path = Path(item) / subfile
                file_path.write_text(subcontent, encoding="utf-8")
                print(f"Ficheiro criado: {file_path}")
        else:
            Path(item).write_text(content, encoding="utf-8")
            print(f"Ficheiro criado: {item}")

    print("\nA instalar dependências...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        print(f"\nFalha ao instalar dependências: {exc}")
        print(f"Podes tentar manualmente com: {sys.executable} -m pip install -r requirements.txt")
        return

    print("\nProjeto criado com sucesso!")
    print(f"Dependências instaladas com: {sys.executable}")
    print(f"Executa agora: {sys.executable} main.py")


if __name__ == "__main__":
    create_project()
