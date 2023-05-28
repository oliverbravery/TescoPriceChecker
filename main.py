import requests
import json
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
tesco_api_key = os.getenv("tesco_api_key")

class TescoAPI:

    '''
    Returns JSON response or -1 if something goes wrong
    '''
    def get_item_details(tpnb):
        url = "https://api.tesco.com/shoppingexperience"
        payload = json.dumps({
            "query": "query GetProductDetails(\n  $tpnb: ID!\n) {\n  product(tpnb: $tpnb) {\n    tpnb,id\n  gtin\n  adId\n  baseProductId\n  title\n  brandName\n  shortDescription\n  defaultImageUrl\n  superDepartmentId\n  superDepartmentName\n  departmentId\n  departmentName\n  aisleId\n  aisleName\n  shelfId\n  shelfName\n  displayType\n  productType\n  averageWeight\n  bulkBuyLimit\n  maxQuantityAllowed: bulkBuyLimit\n  groupBulkBuyLimit\n  bulkBuyLimitMessage\n  bulkBuyLimitGroupId\n  timeRestrictedDelivery\n  restrictedDelivery\n  isForSale\n  isInFavourites\n  isNew\n  isRestrictedOrderAmendment\n  status\n  maxWeight\n  minWeight\n  increment\n  details {\n    components {\n      ...Competitors\n      ...AdditionalInfo\n    }\n  }\n  catchWeightList{\n    price\n    weight\n  }\n  price {\n    price: actual\n    unitPrice\n    unitOfMeasure\n  }\n  promotions {\n    promotionId: id\n    promotionType\n    startDate\n    endDate\n    offerText: description\n    price {\n      beforeDiscount\n      afterDiscount\n    }\n    attributes\n  }\n  restrictions(\n    startDateTime:$startDateTime\n    endDateTime:$endDateTime\n    basketItems:$basketItems\n  ) }\n}",
            "variables": {
                "tpnb": f"{tpnb}"
            }
        })
        headers = {
            'x-apikey': tesco_api_key,
            'Content-Type': 'application/json',
            'Origin': 'https://www.tesco.com'
        }
        try:
            response = requests.request("POST", url, headers=headers, data=payload)
            return response.json()
        except Exception:
            print(f"Error getting item details from the Tesco API: {Exception}")
            return -1

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

if __name__ == '__main__':
    pass
