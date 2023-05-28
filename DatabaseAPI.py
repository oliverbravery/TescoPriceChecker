import sqlite3
import os

class DatabaseAPI:
    database_name = 'Tesco_Prices.db'
    def create_database(self):
        try:
            if os.path.exists(self.database_name):
                return 0
            connection = sqlite3.connect(self.database_name)
            connection.execute('CREATE TABLE tblItems (tpnb INTEGER PRIMARY KEY, name TEXT);')
            connection.execute(
                'CREATE TABLE tblPrices (tpnb INTEGER, date_changed DATETIME, price DOUBLE, FOREIGN KEY (tpnb) REFERENCES tblItems (tpnb));')
            connection.commit()
            connection.close()
            return 0
        except Exception:
            print(f"Error creating the database: {Exception}")
            return -1

    def get_items(self):
        try:
            connection = sqlite3.connect(self.database_name)
            cursor = connection.cursor()
            cursor.execute('SELECT * FROM tblItems;')
            results = cursor.fetchall()
            json_data = json.dumps(results, indent=2)
            connection.close()
            return json_data
        except Exception:
            print(f"Error getting item from database: {Exception}")
            return -1

    def add_item(self, name, tpnb):
        try:
            connection = sqlite3.connect(self.database_name)
            cursor = connection.cursor()
            cursor.execute('INSERT INTO tblItems (name, tpnb) VALUES (?, ?);', (name, tpnb))
            connection.commit()
            connection.close()
            return 0
        except Exception:
            return -1

    def check_price_difference(self, tpnb, price):
        try:
            connection = sqlite3.connect(self.database_name)
            cursor = connection.cursor()
            cursor.execute('SELECT price FROM tblPrices WHERE tpnb = ? ORDER BY date_changed DESC LIMIT 1;', (tpnb,))
            results = cursor.fetchone()
            if results is not None and results[0] != price:
                return True
            else:
                return False
            connection.close()
        except Exception:
            print(f"Error checking the price difference: {Exception}")
            return -1

    def add_price(self, tpnb, price):
        try:
            if self.check_price_difference(tpnb, price):
                connection = sqlite3.connect(self.database_name)
                cursor = connection.cursor()
                cursor.execute('INSERT INTO tblPrices (tpnb, price, date_changed) VALUES (?, ?, CURRENT_TIMESTAMP);',
                               (tpnb, price))
                connection.commit()
                connection.close()
                return 0
        except Exception:
            print(f"Error adding a new price: {Exception}")
            return -1

    def get_prices(self):
        try:
            connection = sqlite3.connect(self.database_name)
            cursor = connection.cursor()
            cursor.execute('SELECT * FROM tblPrices;')
            results = cursor.fetchall()
            json_data = json.dumps(results, indent=2)
            connection.close()
            return json_data
        except Exception:
            print(f"Error getting prices from the database: {Exception}")
            return -1

    def get_prices_by_tpnb(self,tpnb):
        try:
            connection = sqlite3.connect(self.database_name)
            cursor = connection.cursor()
            cursor.execute('SELECT * FROM tblPrices WHERE tpnb = ? ORDER BY date_changed DESC;', (tpnb,))
            results = cursor.fetchall()
            json_data = json.dumps(results, indent=2)
            connection.close()
            return json_data
        except Exception:
            print(f"Error getting prices of a given item: {Exception}")
            return -1