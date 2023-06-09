import sqlite3
import os
import json
from utils import logger

class DatabaseAPI:

    def __init__(self):
        self.database_name = os.path.join(os.path.dirname(__file__), 'database/Tesco_Prices.db')

    def create_database(self):
        try:
            if os.path.exists(self.database_name):
                return 0
            connection = sqlite3.connect(self.database_name)
            cursor = connection.cursor()
            cursor.execute('CREATE TABLE tblItems (tpnb INTEGER PRIMARY KEY, name TEXT);')
            connection.commit()
            cursor.execute('CREATE TABLE tblItemSubscriptions (subscriber TEXT, tpnb INTEGER, PRIMARY KEY(subscriber, tpnb), '
                           'FOREIGN KEY(tpnb) REFERENCES tblItems(tpnb), FOREIGN KEY(subscriber) REFERENCES tblSubscribers (subscriber));')
            connection.commit()
            cursor.execute('CREATE TABLE tblSubscribers (subscriber TEXT PRIMARY KEY, last_viewed DATETIME);')
            connection.commit()
            cursor.execute('CREATE TABLE tblPrices (tpnb INTEGER, date_changed DATETIME, price DOUBLE, promotion_message TEXT, clubcard_price DOUBLE, '
                           'FOREIGN KEY (tpnb) REFERENCES tblItems (tpnb));')
            connection.commit()
            connection.close()
            return 0
        except Exception as e:
            logger(f"Error creating the database: {e}")
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
            logger(f"Error getting item from database: {e}")
            return -1
        
    def perform_no_response_query(self, query):
        try:
            connection = sqlite3.connect(self.database_name)
            cursor = connection.cursor()
            cursor.execute(query)
            connection.commit()
            connection.close()
            return 0
        except Exception as e:
            logger(f"Error performing query: {e}. query string: '{query}'")
            return -1

    def add_item(self, name, tpnb, subscriber):
        try:
            self.perform_no_response_query(f'INSERT INTO tblSubscribers (subscriber) VALUES ({str(subscriber.id)});')
            self.perform_no_response_query(f"INSERT INTO tblItems (tpnb, name) VALUES ({int(tpnb)}, '{str(name)}');")
            self.perform_no_response_query(f'INSERT INTO tblItemSubscriptions (subscriber, tpnb) VALUES ({str(subscriber.id)}, {int(tpnb)});')
            return 0
        except Exception as e:
            logger(f"Error adding item to the database: {e}")
            return -1

    def check_item_differences(self, tpnb, price, clubcard_price, promotion_message):
        try:
            connection = sqlite3.connect(self.database_name)
            cursor = connection.cursor()
            cursor.execute('SELECT price, clubcard_price, promotion_message FROM tblPrices WHERE tpnb = ? ORDER BY date_changed DESC LIMIT 1;', (tpnb,))
            results = cursor.fetchone()
            connection.close()
            if results is None:
                return True
            elif float(results[0][0]) != price or str(results[0][2]) != promotion_message:
                return True 
            else:
                if results[0][1] is not None:
                    if float(results[0][1]) != clubcard_price:
                        return True
                return False
        except Exception as e:
            logger(f"Error checking the price difference: {e}")
            return -1

    def add_price(self, tpnb, price, promotion_message, clubcard_price):
        try:
            if self.check_item_differences(tpnb, price, clubcard_price, promotion_message):
                connection = sqlite3.connect(self.database_name)
                cursor = connection.cursor()
                cursor.execute('INSERT INTO tblPrices (tpnb, price, date_changed, promotion_message, clubcard_price) VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?);',
                               (tpnb, price, promotion_message, clubcard_price))
                connection.commit()
                connection.close()
                return 0
        except Exception as e:
            logger(f"Error adding a new price: {e}")
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
            logger(f"Error getting prices from the database: {e}")
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
            logger(f"Error getting prices of a given item: {e}")
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
            logger(f"Error getting item by tpnb '{tpnb}': {e}")
            return -1
        
    def get_subscribers(self):
        try:
            connection = sqlite3.connect(self.database_name)
            cursor = connection.cursor()
            cursor.execute('SELECT subscriber FROM tblSubscribers;')
            results = cursor.fetchall()
            connection.close()
            if results is None:
                return []
            else:
                new_results = []
                for x in results:
                    new_results.append(x[0])
                return new_results
        except Exception as e:
            logger(f"Error getting subscribers from the database: {e}")
            return -1

    def get_items_by_subscriber(self,subscriber):
        try:
            connection = sqlite3.connect(self.database_name)
            cursor = connection.cursor()
            cursor.execute(f"SELECT tpnb FROM tblItemSubscriptions WHERE subscriber={str(subscriber.id)};")
            results = cursor.fetchall()
            connection.close()
            if results is None:
                return []
            else:
                first_results = []
                for x in results:
                    first_results.append(x[0])
                return first_results
        except Exception as e:
            logger(f"Error getting subscribers from the database: {e}")
            return -1
        
    def update_subscribers_last_viewed(self, subscriber):
        try:
            self.perform_no_response_query(f"UPDATE tblSubscribers SET last_viewed=CURRENT_TIMESTAMP WHERE subscriber={str(subscriber.id)};")
            return 0
        except Exception as e:
            logger(f"Error updating last viewed for subscriber {subscriber.id}: {e}")
            return -1
        
    def get_unviewed_item_changes(self,subscriber):
        try:
            connection = sqlite3.connect(self.database_name)
            cursor = connection.cursor()
            cursor.execute(f"SELECT i.tpnb FROM tblItemSubscriptions i, tblSubscribers s, tblPrices p WHERE s.subscriber=i.subscriber AND p.tpnb=i.tpnb AND s.last_viewed < p.date_changed AND s.subscriber={subscriber.id};")
            results = cursor.fetchall()
            connection.close()
            if results is None:
                return []
            else:
                new_results = []
                for r in results:
                    new_results.append(r[0])
                return new_results
        except Exception as e:
            logger(f"Error getting unviewed items for {subscriber.id} from the database: {e}")
            return -1
    
    def remove_item_from_subscription(self, tpnb, subscriber):
        return_state = self.perform_no_response_query(f"DELETE FROM tblItemSubscriptions WHERE tpnb={tpnb} AND subscriber={str(subscriber.id)};")
        logger(f"{subscriber.id} removed item {tpnb} from their subscription list. Return state: {return_state}")
        if return_state == 0:
            try:
                connection = sqlite3.connect(self.database_name)
                cursor = connection.cursor()
                cursor.execute(f"SELECT * FROM tblItemSubscriptions WHERE tpnb={tpnb};")
                results = cursor.fetchall()
                connection.close()
                if results is not None:
                    if results == []:
                        self.perform_no_response_query(f"DELETE FROM tblItems WHERE tpnb={tpnb};")
                        logger(f"Removed item {tpnb} from the database as it is no longer subscribed to.")
            except Exception as e:
                logger(f"Error in remove_item_from_subscription: {e}")
        return return_state