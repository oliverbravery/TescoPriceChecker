# Tesco Price Checker
Tesco Item Price & Clubcard Deal Tracking via Discord
## Project Description
This project allows users to subscribe to certain items on the Tesco website via there links and then, when the price of the item or the clubcard deal for that item changes, the user will be notified via a discord webhook. The Tesco API is queried to get the items details, a discord bot is used to monitor and respond to user commands and discord webhooks are used to send general price updates to a given channel.
## Project Setup
### Prerequisites
- Python 3.9.x
- Pip
- Tesco API Key
- Discord Bot Token
- Discord Webhook URL
- Docker (if you want to run the project in a container)
#### Aquire a Tesco API Key
To get a tesco API key you need to inspect the headers attatched to any request made to the domain `api.tesco.com`. On mac, I would recommend using a proxy like [charles](https://www.charlesproxy.com/download/). Start on the tesco.com website then from there visit any product page (whilst proxying all traffic). Remember to enable SSL proxying for the api.tesco.com site. Once you find a POST request to the api.tesco.com domain you can inspect its headers and find the `x-apikey` value (this is the tesco api key). I copied the cURL request of the POST api request from charles to postman to inspect the headers more clearly.
>NOTE: if enabling SSL proxy on the API domain does not work you may need to inspect the ip address for the api and add it to the charles access control list.
### Installing dependencies
In order to set your environment up, first install all requirements:
```shell
pip install -r requirements.txt
```
### Environment Variables
To setup the environment variables, edit the `src/.env.template` file. You will need to enter your discord webhook url, tesco api key and discord bot token. Once you have done this, rename the file to `.env`.
### Running the project
You can either run the project in a container or locally. To run the project locally, run the following command from the src directory:
```shell
python main.py
```
To run the project in a container, run the following commands from the root directory:
```shell
docker build --tag tesco-price-bot .
```
This command creates an image of the project. Next all you have to do is run the docker image in a container.

