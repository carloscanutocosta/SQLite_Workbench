import os
import subprocess
import sys
import shutil
import time

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

def ensure_certificate():
    """Gera um certificado auto-assinado se não existir, para garantir que a assinatura funciona."""
    if os.path.exists("certificate.pfx"):
        return

    print("⚠️  'certificate.pfx' não encontrado. A gerar certificado auto-assinado...")
    try:
        # Comando PowerShell para criar certificado e exportar PFX (Senha: 1234)
        cmd = [
            "powershell", "-Command",
            "$cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject 'CN=SQLite Workbench' -CertStoreLocation Cert:\\CurrentUser\\My; "
            "$password = ConvertTo-SecureString -String '1234' -Force -AsPlainText; "
            "Export-PfxCertificate -Cert $cert -FilePath 'certificate.pfx' -Password $password"
        ]
        subprocess.check_call(cmd)
        print("✅ Certificado gerado: certificate.pfx (Senha: 1234)")
    except Exception as e:
        print(f"❌ Erro ao gerar certificado: {e}")

def create_version_info(filename):
    """Cria o ficheiro de informações de versão para o executável."""
    content = """
# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
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
        StringStruct(u'FileVersion', u'1.0.0.0'),
        StringStruct(u'InternalName', u'SQLiteWorkbench'),
        StringStruct(u'LegalCopyright', u'Copyright (c) 2026 Carlos Canuto Costa'),
        StringStruct(u'OriginalFilename', u'SQLiteWorkbench.exe'),
        StringStruct(u'ProductName', u'SQLite Workbench'),
        StringStruct(u'ProductVersion', u'1.0.0.0')])
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
    icon_path = "Assets/Icons/icon.ico"
    version_file = "version_info.txt"
    
    # Criar ficheiro de versão
    has_version = create_version_info(version_file)
    
    # Obter comando de build
    cmd = get_build_command(main_script, exe_name, icon_path, version_file, has_version)
    
    print("🔨 A executar PyInstaller...")
    try:
        subprocess.check_call(cmd)
        print("✅ Compilação concluída com sucesso!")
        return True, exe_name
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro durante a build: {e}")
        return False, None

def get_build_command(main_script, exe_name, icon_path, version_file, has_version):
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
        
    # Adicionar pasta Assets como dados (windows usa ponto e vírgula)
    if os.path.exists("Assets"):
        # --add-data "origem;destino"
        cmd.extend(["--add-data", "Assets;Assets"])
    
    return cmd

def sign_executable(exe_path):
    """Assina o executável usando signtool.exe se o certificado existir."""
    cert_path = "certificate.pfx"
    cert_pass = "1234"  # A mesma senha definida no PowerShell
    
    if not os.path.exists(cert_path):
        print(f"⚠️  Aviso: '{cert_path}' não encontrado. O executável não será assinado.")
        return

    print("🔐 A iniciar assinatura digital...")

    signtool_path = None

    # 1. Verificar se está no PATH
    if shutil.which("signtool"):
        signtool_path = "signtool"
    else:
        # 2. Procurar em locais comuns (versões específicas conhecidas)
        common_paths = [
            r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\signtool.exe",
            r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.18362.0\x64\signtool.exe",
            r"C:\Program Files (x86)\Windows Kits\10\bin\x64\signtool.exe",
            r"C:\Program Files (x86)\Windows Kits\8.1\bin\x64\signtool.exe"
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                signtool_path = path
                break
        
        # 3. Se ainda não encontrou, tentar procurar na pasta raiz do Kit 10 (qualquer versão)
        if not signtool_path:
            sdk_root = r"C:\Program Files (x86)\Windows Kits\10\bin"
            if os.path.exists(sdk_root):
                for root, dirs, files in os.walk(sdk_root):
                    if "signtool.exe" in files:
                        signtool_path = os.path.join(root, "signtool.exe")
                        break

    if not signtool_path:
        print("⚠️  Aviso: 'signtool.exe' não encontrado (Windows SDK em falta?).")
        print("   O executável foi gerado com sucesso, mas NÃO foi assinado.")
        return

    # Comando de assinatura
    # /fd SHA256: Usa algoritmo seguro
    # /tr ... /td ...: Adiciona timestamp (importante para o certificado não expirar o exe)
    sign_cmd = [
        signtool_path, "sign",
        "/f", cert_path,
        "/p", cert_pass,
        "/fd", "SHA256",
        "/tr", "http://timestamp.digicert.com",
        "/td", "SHA256",
        exe_path
    ]

    try:
        subprocess.check_call(sign_cmd)
        print("✅ Executável assinado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao assinar: {e}")

def clean_up():
    """Limpa ficheiros temporários de build."""
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists(f"SQLiteWorkbench.spec"):
        os.remove(f"SQLiteWorkbench.spec")
    if os.path.exists("version_info.txt"):
        os.remove("version_info.txt")
    print("🧹 Limpeza de ficheiros temporários concluída.")

def test_executable(exe_name):
    """Testa se o executável compilado abre e mantém-se em execução."""
    exe_path = os.path.join("dist", f"{exe_name}.exe")
    
    if not os.path.exists(exe_path):
        print(f"❌ Executável não encontrado para teste: {exe_path}")
        return

    print(f"\n🚀 A executar teste de arranque: {exe_path}")
    
    try:
        # Inicia o executável sem bloquear o script
        process = subprocess.Popen(exe_path)
        
        print("⏳ A aguardar 5 segundos para verificar inicialização...")
        time.sleep(5)
        
        # Verifica se o processo ainda está ativo
        if process.poll() is None:
            print("✅ TESTE BEM-SUCEDIDO: A aplicação iniciou e permaneceu aberta.")
            print("🛑 A encerrar o processo de teste...")
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
        else:
            print(f"❌ TESTE FALHOU: A aplicação fechou imediatamente. Código de saída: {process.returncode}")
            
    except Exception as e:
        print(f"❌ Erro crítico ao executar teste: {e}")

if __name__ == "__main__":
    if not check_pyinstaller():
        install_pyinstaller()
    
    ensure_certificate()
    
    success, name = build_exe()
    
    if success and name:
        dist_path = os.path.join("dist", f"{name}.exe")
        if os.path.exists(dist_path):
            sign_executable(dist_path)
            print(f"\n🚀 Processo concluído! O executável está em:\n{os.path.abspath(dist_path)}")
            test_executable(name)

    clean_up()
