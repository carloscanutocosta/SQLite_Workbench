import csv
import sqlite3
import logging
from typing import List, Tuple, Any, Optional, Union
try:
    import pandas as pd
except ImportError:
    pd = None

# Configuração do logging
logging.basicConfig(
    filename='db_operations.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class DatabaseManager:
    """Gere a conexão e as operações com a base de dados SQLite."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            logging.info(f"Conexão estabelecida: {self.db_path}")
        except sqlite3.Error as e:
            logging.error(f"Erro ao conectar à BD: {e}")
            raise Exception(f"Erro ao conectar à BD: {e}")

    def disconnect(self):
        if self.conn:
            self.conn.close()
            logging.info("Conexão fechada.")

    def get_tables(self) -> List[str]:
        if not self.conn:
            self.connect()
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Erro ao listar tabelas: {e}")
            raise Exception(f"Erro ao listar tabelas: {e}")

    def _build_where_clause(self, table_name: str, filter_config: dict = None) -> Tuple[str, List[Any]]:
        """Constrói a cláusula WHERE e os parâmetros com base na configuração do filtro."""
        if not filter_config or not filter_config.get("value"):
            return "", []

        column = filter_config.get("column", "Todos")
        operator = filter_config.get("operator", "LIKE")
        value = filter_config.get("value", "")
        
        # Whitelist de operadores para segurança SQL
        valid_operators = ["=", "!=", ">", "<", ">=", "<=", "LIKE"]
        if operator not in valid_operators:
            operator = "LIKE"

        params = []
        conditions = []

        if column == "Todos":
            # Comportamento antigo: pesquisa em todas as colunas com LIKE
            cols = self.get_columns(table_name)
            wildcard_filter = f"%{value}%"
            for col in cols:
                conditions.append(f'"{col}" LIKE ?')
                params.append(wildcard_filter)
            where_clause = f" WHERE {' OR '.join(conditions)}"
        else:
            # Filtro em coluna específica
            safe_col = f'"{column.replace("\"", "\"\"")}"'
            
            # Ajuste para LIKE: adicionar % automaticamente para conveniência
            if operator == "LIKE":
                final_value = f"%{value}%"
            else:
                final_value = value
                
            where_clause = f" WHERE {safe_col} {operator} ?"
            params.append(final_value)
            
        return where_clause, params

    def get_table_row_count(self, table_name: str, filter_config: dict = None) -> int:
        """Obtém o número total de linhas numa tabela, opcionalmente filtradas."""
        if not self.conn:
            self.connect()
        try:
            cursor = self.conn.cursor()
            safe_table_name = f'"{table_name.replace("\"", "\"\"")}"'
            
            where_clause, params = self._build_where_clause(table_name, filter_config)

            query = f"SELECT COUNT(*) FROM {safe_table_name}{where_clause}"
            cursor.execute(query, tuple(params))
            count = cursor.fetchone()[0]
            return count
        except sqlite3.Error as e:
            logging.error(f"Erro ao contar linhas da tabela {table_name}: {e}")
            raise Exception(f"Erro ao contar linhas da tabela {table_name}: {e}")

    def get_table_data(self, table_name: str, limit: int, offset: int, filter_config: dict = None, sort_column: str = None, sort_order: str = "ASC") -> Tuple[List[str], List[Tuple[Any]]]:
        """Obtém uma 'página' de dados, opcionalmente filtrada."""
        if not self.conn:
            self.connect()
        try:
            cursor = self.conn.cursor()
            safe_table_name = f'"{table_name.replace("\"", "\"\"")}"'
            
            where_clause, params = self._build_where_clause(table_name, filter_config)
            order_clause = ""

            if sort_column:
                safe_sort_col = f'"{sort_column.replace("\"", "\"\"")}"'
                safe_order = "DESC" if sort_order and sort_order.upper() == "DESC" else "ASC"
                order_clause = f" ORDER BY {safe_sort_col} {safe_order}"

            # Fetch rowid for editing/deleting capabilities
            query = f"SELECT rowid, * FROM {safe_table_name}{where_clause}{order_clause} LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, tuple(params))

            if cursor.description:
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                return columns, rows
            return [], []
        except sqlite3.Error as e:
            logging.error(f"Erro ao ler dados da tabela {table_name}: {e}")
            raise Exception(f"Erro ao ler dados da tabela {table_name}: {e}")

    def get_columns(self, table_name: str) -> List[str]:
        """Obtém os nomes das colunas de uma tabela."""
        if not self.conn:
            self.connect()
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"PRAGMA table_info('{table_name}')")
            return [row[1] for row in cursor.fetchall()]
        except sqlite3.Error:
            return []

    def get_column_types(self, table_name: str) -> dict:
        """Obtém um dicionário mapeando colunas aos seus tipos de dados."""
        if not self.conn:
            self.connect()
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"PRAGMA table_info('{table_name}')")
            # row[1] é nome, row[2] é tipo
            return {row[1]: row[2] for row in cursor.fetchall()}
        except sqlite3.Error:
            return {}

    def _validate_data(self, table_name: str, data: dict):
        """Valida os dados de entrada comparando com os tipos das colunas."""
        col_types = self.get_column_types(table_name)
        
        for col, val in data.items():
            if val is None or val == "":
                continue
            
            dtype = col_types.get(col, "TEXT").upper()
            
            if "INT" in dtype:
                try:
                    int(val)
                except ValueError:
                    raise ValueError(f"A coluna '{col}' ({dtype}) espera um valor inteiro, mas recebeu '{val}'.")
            elif any(x in dtype for x in ["REAL", "FLOAT", "DOUBLE", "DECIMAL", "NUMERIC"]):
                try:
                    float(val)
                except ValueError:
                    raise ValueError(f"A coluna '{col}' ({dtype}) espera um valor numérico, mas recebeu '{val}'.")

    def get_table_schema(self, table_name: str) -> str:
        if not self.conn:
            self.connect()
        try:
            cursor = self.conn.cursor()
            query = "SELECT sql FROM sqlite_master WHERE type='table' AND name=?;"
            cursor.execute(query, (table_name,))
            result = cursor.fetchone()
            if result and result[0]:
                return result[0]
            return "-- Esquema não disponível."
        except sqlite3.Error as e:
            return f"-- Erro ao obter esquema: {e}"

    def import_csv_to_table(self, csv_path: str, table_name: str, delimiter: str = ';', progress_callback=None):
        """
        Importa dados de um ficheiro CSV para uma nova tabela.
        Assume que a primeira linha do CSV é o cabeçalho.
        """
        if not self.conn:
            self.connect()

        # Basic sanitization for table name
        safe_table_name = f'"{table_name.replace("\"", "\"\"")}"'

        try:
            # Primeiro passo: contar linhas para a barra de progresso
            total_lines = 0
            if progress_callback:
                with open(csv_path, 'r', encoding='utf-8-sig') as f:
                    total_lines = sum(1 for _ in f) - 1 # Subtrair cabeçalho

            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f, delimiter=delimiter)
                try:
                    header = next(reader)
                except StopIteration:
                    raise Exception("O ficheiro CSV está vazio.")
                
                # Sanitize column names for SQL
                sanitized_header = [f'"{col.strip().replace("\"", "\"\"")}"' for col in header]

                cursor = self.conn.cursor()

                # Create table - All columns will be TEXT for simplicity
                create_table_sql = f'CREATE TABLE {safe_table_name} ({", ".join(f"{col} TEXT" for col in sanitized_header)})'
                cursor.execute(create_table_sql)

                # Insert data
                placeholders = ", ".join(["?"] * len(header))
                insert_sql = f'INSERT INTO {safe_table_name} ({", ".join(sanitized_header)}) VALUES ({placeholders})'
                
                # Inserir em lotes para permitir atualização da UI
                batch = []
                batch_size = 1000
                processed_lines = 0

                for row in reader:
                    batch.append(row)
                    if len(batch) >= batch_size:
                        cursor.executemany(insert_sql, batch)
                        processed_lines += len(batch)
                        if progress_callback: progress_callback(processed_lines, total_lines)
                        batch = []
                
                if batch:
                    cursor.executemany(insert_sql, batch)
                    processed_lines += len(batch)
                    if progress_callback: progress_callback(processed_lines, total_lines)

                self.conn.commit()
                logging.info(f"CSV importado para tabela '{table_name}': {processed_lines} linhas.")
        except Exception as e:
            if self.conn: self.conn.rollback()
            logging.error(f"Erro ao importar CSV para '{table_name}': {e}")
            raise Exception(f"Erro ao importar CSV: {e}")

    def create_table(self, table_name: str, columns: List[dict], foreign_keys: List[dict] = None):
        """Cria uma nova tabela vazia."""
        if not self.conn:
            self.connect()
        
        if not table_name.strip():
            raise ValueError("O nome da tabela não pode ser vazio.")
        if not columns:
            raise ValueError("A tabela deve ter pelo menos uma coluna.")

        try:
            cursor = self.conn.cursor()
            
            safe_table_name = f'"{table_name.replace("\"", "\"\"")}"'
            
            column_definitions = []
            for col in columns:
                name = col.get('name')
                dtype = col.get('type')
                if not name or not dtype:
                    raise ValueError("Cada coluna deve ter um nome e um tipo.")
                
                safe_col_name = f'"{name.replace("\"", "\"\"")}"'
                definition = f"{safe_col_name} {dtype}"
                
                if col.get('pk'):
                    definition += " PRIMARY KEY"
                if col.get('ai'):
                    definition += " AUTOINCREMENT"
                if col.get('nn'):
                    definition += " NOT NULL"
                
                column_definitions.append(definition)
                
            if foreign_keys:
                for fk in foreign_keys:
                    local_col = fk.get('from')
                    ref_table = fk.get('table')
                    ref_col = fk.get('to')
                    
                    if local_col and ref_table and ref_col:
                        fk_def = f'FOREIGN KEY ("{local_col}") REFERENCES "{ref_table}" ("{ref_col}")'
                        column_definitions.append(fk_def)

            query = f"CREATE TABLE {safe_table_name} ({', '.join(column_definitions)})"
            
            cursor.execute(query)
            self.conn.commit()
            logging.info(f"Tabela criada: {table_name}")
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.error(f"Erro ao criar tabela '{table_name}': {e}")
            raise Exception(f"Erro ao criar tabela: {e}")

    def rename_table(self, old_name: str, new_name: str):
        """Renomeia uma tabela."""
        if not self.conn:
            self.connect()
        try:
            # Sanitize names
            safe_old_name = f'"{old_name.replace("\"", "\"\"")}"'
            safe_new_name = f'"{new_name.replace("\"", "\"\"")}"'
            
            cursor = self.conn.cursor()
            query = f"ALTER TABLE {safe_old_name} RENAME TO {safe_new_name}"
            cursor.execute(query)
            self.conn.commit()
            logging.info(f"Tabela renomeada: de '{old_name}' para '{new_name}'")
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.error(f"Erro ao renomear tabela '{old_name}': {e}")
            raise Exception(f"Erro ao renomear tabela: {e}")

    def delete_table(self, table_name: str):
        """Apaga uma tabela."""
        if not self.conn:
            self.connect()
        try:
            safe_table_name = f'"{table_name.replace("\"", "\"\"")}"'
            cursor = self.conn.cursor()
            query = f"DROP TABLE {safe_table_name}"
            cursor.execute(query)
            self.conn.commit()
            logging.info(f"Tabela apagada: {table_name}")
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.error(f"Erro ao apagar tabela '{table_name}': {e}")
            raise Exception(f"Erro ao apagar tabela: {e}")

    def get_foreign_keys(self, table_name: str) -> List[dict]:
        """Obtém a lista de chaves estrangeiras para uma tabela."""
        if not self.conn:
            self.connect()
        try:
            # PRAGMA statement is safe as table_name comes from get_tables()
            cursor = self.conn.cursor()
            cursor.execute(f"PRAGMA foreign_key_list('{table_name}');")
            keys = []
            for row in cursor.fetchall():
                keys.append({
                    'from': row[3],  # column in current table
                    'table': row[2], # referenced table
                    'to': row[4],    # column in referenced table
                })
            return keys
        except sqlite3.Error:
            # Fails silently if PRAGMA is not supported or table not found
            return []

    def delete_record(self, table_name: str, rowid: int):
        """Apaga um registo de uma tabela pelo seu rowid."""
        if not self.conn:
            self.connect()
        try:
            cursor = self.conn.cursor()
            query = f'DELETE FROM "{table_name}" WHERE rowid = ?'
            
            # Garantir que rowid é int
            try:
                rid = int(rowid)
            except ValueError:
                raise Exception(f"RowID inválido: {rowid}")

            cursor.execute(query, (rid,))
            self.conn.commit()
            if cursor.rowcount == 0:
                logging.warning(f"Tentativa de apagar registo inexistente (rowid: {rowid}) na tabela '{table_name}'")
                raise Exception("Nenhum registo foi apagado. O rowid pode ser inválido.")
            logging.info(f"Registo apagado na tabela '{table_name}' (rowid: {rowid})")
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.error(f"Erro ao apagar registo na tabela '{table_name}' (rowid: {rowid}): {e}")
            raise Exception(f"Erro ao apagar registo: {e}")

    def update_record(self, table_name: str, rowid: int, data: dict):
        """Atualiza um registo de uma tabela pelo seu rowid."""
        if not self.conn:
            self.connect()
        
        if not data:
            raise ValueError("Nenhum dado fornecido para atualização.")

        self._validate_data(table_name, data)

        try:
            # Garantir que rowid é int
            try:
                rid = int(rowid)
            except ValueError:
                raise Exception(f"RowID inválido: {rowid}")

            cursor = self.conn.cursor()
            
            safe_table_name = f'"{table_name.replace("\"", "\"\"")}"'
            
            set_parts = []
            values = []
            for col, val in data.items():
                safe_col = f'"{col.replace("\"", "\"\"")}"'
                set_parts.append(f"{safe_col} = ?")
                values.append(val)
            
            set_clause = ", ".join(set_parts)
            values.append(rid)
            
            query = f'UPDATE {safe_table_name} SET {set_clause} WHERE rowid = ?'
            
            cursor.execute(query, tuple(values))
            self.conn.commit()
            if cursor.rowcount == 0:
                logging.warning(f"Tentativa de atualizar registo inexistente (rowid: {rowid}) na tabela '{table_name}'")
                raise Exception("Nenhum registo foi atualizado. O rowid pode ser inválido.")
            logging.info(f"Registo atualizado na tabela '{table_name}' (rowid: {rowid}). Dados: {data}")
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.error(f"Erro ao atualizar registo na tabela '{table_name}' (rowid: {rowid}): {e}")
            raise Exception(f"Erro ao atualizar registo: {e}")

    def insert_record(self, table_name: str, data: dict):
        """Insere um novo registo na tabela."""
        if not self.conn:
            self.connect()
        
        if not data:
            raise ValueError("Nenhum dado fornecido para inserção.")

        self._validate_data(table_name, data)

        try:
            cursor = self.conn.cursor()
            safe_table_name = f'"{table_name.replace("\"", "\"\"")}"'
            
            columns = []
            values = []
            placeholders = []
            
            for col, val in data.items():
                columns.append(f'"{col.replace("\"", "\"\"")}"')
                values.append(val)
                placeholders.append("?")
            
            query = f'INSERT INTO {safe_table_name} ({", ".join(columns)}) VALUES ({", ".join(placeholders)})'
            
            cursor.execute(query, tuple(values))
            self.conn.commit()
            logging.info(f"Novo registo inserido na tabela '{table_name}'. Dados: {data}")
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.error(f"Erro ao inserir registo na tabela '{table_name}': {e}")
            raise Exception(f"Erro ao inserir registo: {e}")

    def get_pandas_statistics(self, table_name: str) -> str:
        """Gera um relatório estatístico completo usando Pandas (se instalado)."""
        if pd is None:
            return "A biblioteca Pandas não está instalada. Instale com 'pip install pandas'."
            
        if not self.conn:
            self.connect()
            
        try:
            # Carregar tabela inteira para DataFrame
            query = f'SELECT * FROM "{table_name}"'
            df = pd.read_sql_query(query, self.conn)
            
            if df.empty:
                return "A tabela está vazia."

            # 'include=all' força a análise de colunas numéricas E de texto
            stats = df.describe(include='all')
            
            # Retorna como string formatada (pode ser exibida num CTkTextbox)
            return stats.to_string()
        except Exception as e:
            logging.error(f"Erro na análise Pandas: {e}")
            return f"Erro ao gerar estatísticas: {e}"

    def get_column_statistics(self, table_name: str, column_name: str) -> dict:
        """Gera estatísticas para uma coluna específica usando SQL."""
        if not self.conn:
            self.connect()
        try:
            cursor = self.conn.cursor()
            safe_table = f'"{table_name.replace("\"", "\"\"")}"'
            safe_col = f'"{column_name.replace("\"", "\"\"")}"'

            stats = {}

            # 1. Agregação Geral: Total, Nulos, Únicos, Min, Max, Média
            # AVG é calculado condicionalmente apenas para números para evitar erros ou zeros em texto
            query_aggs = f"""
                SELECT
                    COUNT(*) as total_rows,
                    COUNT({safe_col}) as non_null_count,
                    COUNT(*) - COUNT({safe_col}) as null_count,
                    COUNT(DISTINCT {safe_col}) as unique_count,
                    MIN({safe_col}) as min_value,
                    MAX({safe_col}) as max_value,
                    AVG(CASE WHEN typeof({safe_col}) IN ('integer', 'real') THEN {safe_col} ELSE NULL END) as avg_value
                FROM {safe_table}
            """
            cursor.execute(query_aggs)
            row = cursor.fetchone()

            if row:
                stats = {
                    "total_rows": row[0],
                    "non_null_count": row[1],
                    "null_count": row[2],
                    "unique_count": row[3],
                    "min_value": row[4],
                    "max_value": row[5],
                    "avg_value": row[6]
                }

            # 2. Top 10 Valores mais frequentes (Moda)
            query_top = f"""
                SELECT {safe_col}, COUNT(*) as frequency
                FROM {safe_table}
                WHERE {safe_col} IS NOT NULL
                GROUP BY {safe_col}
                ORDER BY frequency DESC
                LIMIT 10
            """
            cursor.execute(query_top)
            stats["top_values"] = cursor.fetchall()

            return stats

        except sqlite3.Error as e:
            logging.error(f"Erro ao obter estatísticas da coluna '{column_name}': {e}")
            return {}

    def vacuum(self):
        """Executa o comando VACUUM para reconstruir e compactar a base de dados."""
        if not self.conn:
            self.connect()

        original_isolation_level = self.conn.isolation_level
        try:
            # VACUUM cannot run inside a transaction. Set autocommit mode.
            self.conn.isolation_level = None
            self.conn.execute("VACUUM;")
            logging.info("VACUUM executado com sucesso.")
        except sqlite3.Error as e:
            logging.error(f"Erro ao executar VACUUM: {e}")
            raise Exception(f"Erro ao compactar a base de dados: {e}")
        finally:
            # Restore the original isolation level
            if self.conn:
                self.conn.isolation_level = original_isolation_level

    def execute_custom_query(self, query: str) -> Union[Tuple[List[str], List[Tuple[Any]]], str]:
        if not self.conn:
            self.connect()
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            logging.info(f"Query SQL personalizada executada: {query}")
            
            if cursor.description:
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                return columns, rows
            
            self.conn.commit()
            return f"Query executada com sucesso. Linhas afetadas: {cursor.rowcount}"
            
        except sqlite3.Error as e:
            logging.error(f"Erro na query SQL personalizada: {e} | Query: {query}")
            raise Exception(f"Erro SQL: {e}")
