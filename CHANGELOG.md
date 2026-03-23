# Changelog

Todas as alterações notáveis a este projeto serão documentadas neste ficheiro.

## [1.0.0.0] - Versão Inicial

### Adicionado
- **Interface Gráfica**:
  - GUI moderna desenvolvida com `customtkinter`.
  - Suporte a Temas (Dark, Light, Sistema).
  - Suporte Multi-idioma (Português e Inglês).
- **Gestão de Base de Dados**:
  - Visualização de tabelas, esquemas e estatísticas de dados.
  - Funcionalidade `VACUUM` para compactação.
  - Criação, renomeação e eliminação de tabelas.
- **Manipulação de Dados**:
  - Visualização de dados com paginação e ordenação.
  - Pesquisa em tempo real na tabela ativa.
  - Inserção, edição e eliminação de registos.
- **Editor SQL**:
  - Realce de sintaxe SQL (via `pygments`).
  - Histórico de execuções e sistema de favoritos.
  - Visualização de resultados em grelha.
- **Importação e Exportação**:
  - Importação de CSV para criar novas tabelas.
  - Exportação de dados visíveis para CSV e JSON.
- **Build e Distribuição**:
  - Script `build.py` automatizado para gerar `.exe` standalone.
  - Inclusão de ícone personalizado e metadados de versão (Version Info).

### Alterado
- **Identidade**: Aplicação renomeada de "SQLite Viewer Pro" para "**SQLite Workbench**".
- **Estrutura**: Refatorização para suporte modular e compilação otimizada com PyInstaller.