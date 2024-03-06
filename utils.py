import asyncio

import pandas
from config import MAXIMUM_GWEI, SLEEP_TIME_GAS

from web3 import AsyncWeb3, AsyncHTTPProvider
from loguru import logger
from playwright.async_api._generated import Page

# # Disable WebRTC
# await context.add_init_script("""
#     if (window.RTCPeerConnection) {
#         const originalRTCPeerConnection = window.RTCPeerConnection;
#         window.RTCPeerConnection = function(config, ...args) {
#             if (config && config.iceServers) {
#                 config.iceServers = config.iceServers.filter(server => {
#                     if (server.urls) {
#                         server.urls = server.urls.filter(url => url.startsWith('turn:'));
#                     }
#                     return !!server.urls;
#                 });
#             }
#             return new originalRTCPeerConnection(config, ...args);
#         };
#     }
# """)




async def switch_to_page_by_title(context, title) -> Page:
    for _ in range(50):
        for page in context.pages:
            # print([await page.title()])
            if title == await page.title():
                await page.bring_to_front()  # Переключаемся на страницу
                # print(await page.title())
                return page
        await asyncio.sleep(0.5)
    return None  
        

def get_format_proxy(proxy):
    login_password, address_port = proxy.split('@')
    address, port = address_port.split(':')
    login, password = login_password.split(':')
    return address, port, login, password


def get_accounts():
    with open('Accounts.xlsx', 'rb') as file:
        try:
            wb = pandas.read_excel(file, sheet_name="Accounts")
        except Exception as ex:
            logger.error(ex)
            raise ex
        
        accounts_data = {}
        for index, row in wb.iterrows():
            private_key = row["Private Key"]
            proxy = row["Proxy"]
            accounts_data[int(index) + 1] = {
                "private_key": private_key,
                "proxy": proxy,
            }
                    
        accounts = []
        for k, v in accounts_data.items():
            accounts.append((
                k,
                v['private_key'], 
                v['proxy'] if isinstance(v['proxy'], str) else None,
            ))
        return accounts


async def gas_checker(account_number):
    w3 = AsyncWeb3(AsyncHTTPProvider('https://ethereum-rpc.publicnode.com'))
    while True:
        gas = round(AsyncWeb3.from_wei(await w3.eth.gas_price, 'gwei'), 3)
        if gas < MAXIMUM_GWEI:
            await asyncio.sleep(1)
            logger.success(f"{account_number} | {gas} Gwei | Gas price is good")
            await asyncio.sleep(1)
            return 
        else:
            await asyncio.sleep(1)
            logger.warning(
                f"{account_number} | {gas} Gwei | Gas is too high."
                f" Next check in {SLEEP_TIME_GAS} second")
            await asyncio.sleep(SLEEP_TIME_GAS)
            


# Подключение к сайту https://app.zerion.io
                