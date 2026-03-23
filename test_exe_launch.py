import os
import subprocess
import time
import sys

def test_launch():
    """Testa se o executável compilado abre e mantém-se em execução."""
    exe_path = os.path.join(os.getcwd(), "dist", "SQLiteWorkbench.exe")
    
    if not os.path.exists(exe_path):
        print(f"❌ Executável não encontrado: {exe_path}")
        print("Por favor, execute 'python build.py' antes de testar.")
        sys.exit(1)

    print(f"🚀 A testar arranque de: {exe_path}")
    
    try:
        # Inicia o executável sem bloquear o script de teste
        process = subprocess.Popen(exe_path)
        
        print("⏳ A aguardar 5 segundos para verificar inicialização...")
        time.sleep(5)
        
        # Verifica se o processo ainda está ativo (poll() retorna None se estiver ativo)
        if process.poll() is None:
            print("✅ SUCESSO: A aplicação iniciou e permaneceu aberta.")
            print("🛑 A encerrar o processo de teste...")
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
            sys.exit(0)
        else:
            print(f"❌ FALHA: A aplicação fechou imediatamente. Código de saída: {process.returncode}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Erro crítico ao executar teste: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_launch()