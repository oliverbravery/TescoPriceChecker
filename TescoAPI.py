import requests
import json
import os
from dotenv import load_dotenv
import requests
import json
from bs4 import BeautifulSoup

load_dotenv()
tesco_api_key = os.getenv("tesco_api_key")
new_item_retry_count=os.getenv("new_item_retry_count")

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
        except Exception as e:
            print(f"Error getting item details from the Tesco API: {e}")
            return -1
        
    def get_item_clubcard_details(item_details):
        promotions_infomation = item_details["data"]["product"]["promotions"]
        for promotion in promotions_infomation:
            attributes = promotion["attributes"]
            for attribute in attributes:
                if attribute == "CLUBCARD_PRICING":
                    promotion_deal_text = promotion["offerText"]
                    promotion_start_date = promotion["startDate"]
                    promotion_end_date = promotion["endDate"]
                    promotional_price = None
                    # if statment to check if promotion_deal_text starts with two numbers followed by p or one number followed by p
                    if (promotion_deal_text[0].isdigit() and promotion_deal_text[1] == "p") or (promotion_deal_text[0].isdigit() and  promotion_deal_text[1].isdigit() and promotion_deal_text[2] == "p"):
                        pennie_price = promotion_deal_text.split("p")[0]
                        # convert the pennie amount to pounds
                        promotional_price = float(pennie_price) / 100
                    elif promotion_deal_text[0] == "£":
                        #is pounds
                        pound_price = promotion_deal_text.split(" ")[0]
                        pound_price.replace("£", "")
                        promotional_price = float(pound_price)
                    return {"promotion_deal_text": promotion_deal_text, "promotion_start_date": promotion_start_date, "promotion_end_date": promotion_end_date, "promotional_price": promotional_price}
        return {"promotion_deal_text": None, "promotion_start_date": None, "promotion_end_date": None, "promotional_price": None}

    def find_tpnb_from_product_page(url):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36', "Upgrade-Insecure-Requests": "1","DNT": "1","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language": "en-US,en;q=0.5","Accept-Encoding": "gzip, deflate"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")
        tag = soup.find_all("meta", {"http-equiv": "refresh"})[0]
        attribute = tag.attrs
        end_url = attribute["content"].split("=")[-1][0:-1]
        new_url=url+"?bm-verify="+end_url
        for x in range(int(new_item_retry_count)):
            print(f"Attempt: {x}")
            response = requests.get(new_url, headers=headers)
            soup = BeautifulSoup(response.content, "html.parser")
            tag = soup.find_all("body")[0]
            attribute = tag.attrs
            try:
                json_data = json.loads(attribute["data-redux-state"])
                tpnb = json_data["productDetails"]["product"]["baseProductId"]
                return tpnb
            except:
                pass