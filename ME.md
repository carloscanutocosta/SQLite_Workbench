# SQLite Workbench

Uma ferramenta moderna com interface gráfica (GUI) para visualizar e gerir bases de dados SQLite. Desenvolvida em Python com `customtkinter`.

## Funcionalidades

*   **Explorador de Base de Dados**: Visualize tabelas, esquema e estatísticas.
*   **Visualização de Dados**: Paginação, ordenação e pesquisa em tempo real.
*   **Editor SQL**: Execução de queries personalizadas com realce de sintaxe e histórico.
*   **Gestão de Registos**: Inserir, editar e apagar registos diretamente na grelha.
*   **Importação/Exportação**: Importe ficheiros CSV para novas tabelas e exporte resultados para CSV.
*   **Ferramentas**: Compactação de base de dados (VACUUM) e gestão de tabelas.
*   **Interface**: Tema escuro/claro moderno.

## Instalação

Certifique-se de que tem o Python 3.x instalado.

### Opção 1: Configuração Automática

Se estiver a iniciar o projeto do zero, pode usar o script de instalação incluído:

```bash
python install.py
```

### Opção 2: Instalação Manual

Instale as dependências listadas no ficheiro `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Como Usar

Para iniciar a aplicação, execute o ficheiro principal na raiz do projeto:

```bash
python main.py
```

## Criar Executável (.exe)

O projeto inclui um script de build automatizado que utiliza o `PyInstaller` para gerar um executável único (standalone).

Execute o seguinte comando:

```bash
python build.py
```

O executável final (`SQLiteWorkbench.exe`) será criado na pasta `dist/`.