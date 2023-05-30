import sqlite3
import os
import json

class DatabaseAPI:
    database_name = 'Tesco_Prices.db'

    def create_database(self):
        try:
            if os.path.exists(self.database_name):
                return 0
            connection = sqlite3.connect(self.database_name)
            cursor = connection.cursor()
            cursor.execute('CREATE TABLE tblItems (tpnb INTEGER PRIMARY KEY, name TEXT, subscriber TEXT);')
            connection.commit()
            cursor.execute('CREATE TABLE tblPrices (tpnb INTEGER, date_changed DATETIME, price DOUBLE, promotion_message TEXT, '
                           'FOREIGN KEY (tpnb) REFERENCES tblItems (tpnb));')
            connection.commit()
            connection.close()
            return 0
        except Exception as e:
            print(f"Error creating the database: {e}")
            return -1

    def get_items(self):
        try:
            connection = sqlite3.connect(self.database_name)
            cursor = connection.cursor()
            cursor.execute('SELECT * FROM tblItems;')
            results = cursor.fetchall()
            connection.close()
            return results
        except Exception as e:
            print(f"Error getting item from database: {e}")
            return -1

    def add_item(self, name, tpnb, subscriber):
        try:
            connection = sqlite3.connect(self.database_name)
            cursor = connection.cursor()
            cursor.execute('INSERT INTO tblItems (tpnb, name, subscriber) VALUES (?, ?, ?);', (int(tpnb), str(name), str(subscriber)))
            connection.commit()
            connection.close()
            return 0
        except Exception as e:
            print(f"Error adding item to the database: {e}")
            return -1

    def check_price_difference(self, tpnb, price):
        try:
            connection = sqlite3.connect(self.database_name)
            cursor = connection.cursor()
            cursor.execute('SELECT price FROM tblPrices WHERE tpnb = ? ORDER BY date_changed DESC LIMIT 1;', (tpnb,))
            results = cursor.fetchone()
            if results is None or results[0] != price:
                return True
            else:
                return False
            connection.close()
        except Exception as e:
            print(f"Error checking the price difference: {e}")
            return -1

    def add_price(self, tpnb, price, promotion_message):
        try:
            if self.check_price_difference(tpnb, price):
                connection = sqlite3.connect(self.database_name)
                cursor = connection.cursor()
                cursor.execute('INSERT INTO tblPrices (tpnb, price, date_changed, promotion_message) VALUES (?, ?, CURRENT_TIMESTAMP, ?);',
                               (tpnb, price, promotion_message))
                connection.commit()
                connection.close()
                return 0
        except Exception as e:
            print(f"Error adding a new price: {e}")
            return -1

    def get_prices(self):
        try:
            connection = sqlite3.connect(self.database_name)
            cursor = connection.cursor()
            cursor.execute('SELECT * FROM tblPrices;')
            results = cursor.fetchall()
            connection.close()
            return results
        except Exception as e:
            print(f"Error getting prices from the database: {e}")
            return -1

    def get_prices_by_tpnb(self,tpnb):
        try:
            connection = sqlite3.connect(self.database_name)
            cursor = connection.cursor()
            cursor.execute('SELECT * FROM tblPrices WHERE tpnb = ? ORDER BY date_changed DESC;', (tpnb,))
            results = cursor.fetchall()
            connection.close()
            return results
        except Exception as e:
            print(f"Error getting prices of a given item: {e}")
            return -1

    def get_item_by_tpnb(self,tpnb):
        try:
            connection = sqlite3.connect(self.database_name)
            cursor = connection.cursor()
            cursor.execute('SELECT * FROM tblItems WHERE tpnb = ?;', (tpnb,))
            results = cursor.fetchall()
            connection.close()
            return results
        except Exception as e:
            print(f"Error getting item by tpnb '{tpnb}': {e}")
            return -1