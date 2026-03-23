import os
import subprocess
import sys
import shutil

def check_pyinstaller():
    """Verifica se o PyInstaller está instalado."""
    try:
        subprocess.check_output([sys.executable, '-m', 'pip', 'show', 'pyinstaller'])
        return True
    except subprocess.CalledProcessError:
        return False

def install_pyinstaller():
    """Instala o PyInstaller via pip."""
    print("A instalar PyInstaller...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])

def create_version_info(filename):
    """Cria o ficheiro de informações de versão para o executável."""
    content = """
# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(0, 9, 0, 0),
    prodvers=(0, 9, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Carlos Canuto Costa'),
        StringStruct(u'FileDescription', u'SQLite Workbench - Ferramenta de gestão SQLite'),
        StringStruct(u'FileVersion', u'0.9.0.0'),
        StringStruct(u'InternalName', u'SQLiteWorkbench'),
        StringStruct(u'LegalCopyright', u'Copyright (c) 2026 Carlos Canuto Costa'),
        StringStruct(u'OriginalFilename', u'SQLiteWorkbench.exe'),
        StringStruct(u'ProductName', u'SQLite Workbench'),
        StringStruct(u'ProductVersion', u'0.9.0.0')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Erro ao criar ficheiro de versão: {e}")
        return False

def build_exe():
    """Compila o projeto usando PyInstaller."""
    print("A iniciar o processo de build...")
    
    # Nome do ficheiro principal
    main_script = "main.py"
    
    # Nome do executável final
    exe_name = "SQLiteWorkbench"
    
    # Caminhos adicionais (se necessário, ex: ícone)
    icon_path = "Assets/icon.ico"
    version_file = "version_info.txt"
    
    # Criar ficheiro de versão
    has_version = create_version_info(version_file)
    
    # Comando PyInstaller
    # --noconsole: não mostra a janela preta de comando
    # --onefile: cria um único ficheiro .exe
    # --name: define o nome do executável
    # --clean: limpa a cache antes de construir
    # --collect-all customtkinter: garante que todos os ficheiros do CTk sejam copiados
    
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconsole",
        "--onefile",
        "--clean",
        f"--name={exe_name}",
        "--collect-all", "customtkinter",
        "--collect-all", "pygments",
        "--exclude-module", "matplotlib",
        main_script
    ]
    
    if has_version:
        cmd.insert(3, f"--version-file={version_file}")
    
    # Adicionar ícone se existir
    if os.path.exists(icon_path):
        # Inserir após "PyInstaller" (índice 3 na lista atual)
        cmd.insert(3, f"--icon={icon_path}")

    try:
        subprocess.check_call(cmd)
        print("\n✅ Build concluída com sucesso!")
        print(f"O executável encontra-se na pasta: {os.path.abspath('dist')}")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erro durante a build: {e}")

def clean_up():
    """Limpa ficheiros temporários de build."""
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists(f"SQLiteWorkbench.spec"):
        os.remove(f"SQLiteWorkbench.spec")
    if os.path.exists("version_info.txt"):
        os.remove("version_info.txt")
    print("🧹 Limpeza de ficheiros temporários concluída.")

if __name__ == "__main__":
    if not check_pyinstaller():
        install_pyinstaller()
    
    build_exe()
    clean_up()
