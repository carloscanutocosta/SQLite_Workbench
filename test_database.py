import unittest
import os
import sys

# Adicionar o diretório raiz ao path para conseguir importar 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import DatabaseManager

class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        """Configuração executada antes de cada teste."""
        self.db_path = "test_db.sqlite"
        self.db = DatabaseManager(self.db_path)
        self.db.connect()

    def tearDown(self):
        """Limpeza executada após cada teste."""
        self.db.disconnect()
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except PermissionError:
                pass

    def test_create_table_and_get_tables(self):
        """Testa a criação de tabelas e a listagem das mesmas."""
        columns = [
            {"name": "id", "type": "INTEGER", "pk": True},
            {"name": "nome", "type": "TEXT", "nn": True}
        ]
        self.db.create_table("usuarios", columns)
        
        tables = self.db.get_tables()
        self.assertIn("usuarios", tables)

    def test_insert_and_read_data(self):
        """Testa a inserção de registos e a leitura de dados."""
        columns = [{"name": "produto", "type": "TEXT"}]
        self.db.create_table("stock", columns)
        
        self.db.insert_record("stock", {"produto": "Portátil"})
        self.db.insert_record("stock", {"produto": "Rato"})
        
        # Verificar contagem
        count = self.db.get_table_row_count("stock")
        self.assertEqual(count, 2)
        
        # Verificar dados (lembrando que get_table_data retorna (cols, rows) e rows inclui rowid no index 0)
        cols, rows = self.db.get_table_data("stock", limit=10, offset=0)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][1], "Portátil") # row[0] é rowid, row[1] é a primeira coluna de dados

    def test_update_record(self):
        """Testa a atualização de um registo existente."""
        self.db.create_table("config", [{"name": "chave", "type": "TEXT"}, {"name": "valor", "type": "TEXT"}])
        self.db.insert_record("config", {"chave": "tema", "valor": "light"})
        
        # Obter rowid
        _, rows = self.db.get_table_data("config", 10, 0)
        rowid = rows[0][0]
        
        # Atualizar
        self.db.update_record("config", rowid, {"valor": "dark"})
        
        # Verificar atualização
        _, rows = self.db.get_table_data("config", 10, 0)
        self.assertEqual(rows[0][2], "dark") # index 2 é a coluna 'valor'

    def test_delete_record(self):
        """Testa a eliminação de um registo."""
        self.db.create_table("logs", [{"name": "msg", "type": "TEXT"}])
        self.db.insert_record("logs", {"msg": "Erro 1"})
        
        _, rows = self.db.get_table_data("logs", 10, 0)
        rowid = rows[0][0]
        
        self.db.delete_record("logs", rowid)
        
        count = self.db.get_table_row_count("logs")
        self.assertEqual(count, 0)

    def test_custom_query(self):
        """Testa a execução de SQL personalizado."""
        result = self.db.execute_custom_query("CREATE TABLE teste_sql (id INTEGER)")
        self.assertIn("sucesso", str(result))
        
        self.db.execute_custom_query("INSERT INTO teste_sql VALUES (100)")
        cols, rows = self.db.execute_custom_query("SELECT * FROM teste_sql")
        self.assertEqual(rows[0][0], 100)

if __name__ == '__main__':
    unittest.main()