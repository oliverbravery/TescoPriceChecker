import requests
import json
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