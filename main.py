import asyncio
import random
import traceback

from playwright.async_api import async_playwright
from random import uniform
from loguru import logger
from config import *

from utils import gas_checker, get_accounts, get_format_proxy, switch_to_page_by_title

NEW_PASSWORD = "Password_12345"

async def run(id, private_key, proxy, semaphore):
    # 3 попытки зайти в кошелек
    for _ in range(3):
        try:
            async with semaphore:
                # await gas_checker(id)
                logger.info(f"{id} | START")

                # Initialize the browser and context
                async with async_playwright() as playwright:
                    if proxy is not None and USE_PROXY is True:
                        address, port, login, password = get_format_proxy(proxy)
                        context = await playwright.chromium.launch_persistent_context(
                            '',
                            headless=False,
                            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                            proxy={
                            "server": f"http://{address}:{port}",
                            "username": login,
                            "password": password
                            },
                            args=[
                                '--disable-blink-features=AutomationControlled',
                                f"--disable-extensions-except={EXTENSION_PATH}",
                                f"--load-extension={EXTENSION_PATH}"
                            ]
                        )
                    else:
                        context = await playwright.chromium.launch_persistent_context(
                            '',
                            headless=False,
                            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',

                            args=[
                                '--disable-blink-features=AutomationControlled',
                                f"--disable-extensions-except={EXTENSION_PATH}",
                                f"--load-extension={EXTENSION_PATH}"
                            ]
                        )
                    
                    page = await context.new_page()
                    await page.goto('chrome-extension://ekfliooibpfihceonpdkifajgmgbnpml/popup.8e8f209b.html?templateType=tab&context=onboarding#/onboarding/import/private-key')
                    # await asyncio.sleep(uniform(0.5, 0.9))
                    await page.close()
                    page = await switch_to_page_by_title(context, '')
                    await page.close()
                    
                    page = await switch_to_page_by_title(context, 'Zerion')
                    await page.goto('chrome-extension://ekfliooibpfihceonpdkifajgmgbnpml/popup.8e8f209b.html?templateType=tab&context=onboarding#/onboarding/import/private-key')

                    await page.fill('input[name="key"]', private_key)
                    await page.press('input[name="key"]', 'Enter')
                    await asyncio.sleep(uniform(0.3, 0.7))

                    # Ввод пароля
                    await page.fill('input[name="password"]', NEW_PASSWORD) 
                    await page.press('input[name="password"]', 'Enter')
                    await asyncio.sleep(uniform(0.3, 0.7))

                    # Подтверждение пароля
                    await page.fill('input[name="confirmPassword"]', NEW_PASSWORD)
                    await page.press('input[name="confirmPassword"]', 'Enter')
                    await asyncio.sleep(uniform(4, 6))

                    # await page.goto('chrome-extension://ekfliooibpfihceonpdkifajgmgbnpml/popup.8e8f209b.html')
                    
                    await page.goto("https://app.zerion.io")
                    await asyncio.sleep(uniform(1, 2))
                    # Обработка возможного всплывающего окна
                    try:
                        accept_button = await page.wait_for_selector('div:text("Accept")', timeout=3000)
                        await accept_button.click()
                    except:
                        pass  # Пропускаем, если кнопка не появилась

                    # await page.wait_for_selector('div:text("Zerion")')
                    await page.click(f'xpath=/html/body/div[1]/div[4]/div/div[3]/div/div/div/div[2]/div[2]/div/div[1]/button[1]')
                    await asyncio.sleep(uniform(0.5, 1))
                    zerion_popup_window = await switch_to_page_by_title(context, 'Zerion · Connect Wallet')
                    await zerion_popup_window.click('button:text("Connect")', timeout=10000)
                    await asyncio.sleep(uniform(5, 7))
                                    
                    if MODE == "SELF_SEND":
                        await self_send(id, context, page)
                    elif MODE == "SWAP":
                        await swap(id, context, page)
                    else:
                        print("Неверный режим")
                        return
                    
                    await asyncio.sleep(10)
                    break
                
        except Exception as ex:
            logger.error(f"{id} Retry... | {traceback.format_exc()}, {ex} ")
            await asyncio.sleep(10)
        finally:
            try:
                await context.close()
            except:
                pass

async def self_send(id, context, page):
    rand_self_count = random.randint(SEND_COUNT[0], SEND_COUNT[1])
    logger.info(f"{id} | START {rand_self_count} self send..")
    for i in range(1, rand_self_count+1):
        try:
            await page.goto('https://app.zerion.io/send')
            p = await page.wait_for_selector('#send-to', timeout=10000)
            await p.fill("0")
            await p.press('Backspace')
            await p.press('ArrowDown')
            await p.press('Enter')

            rand_sum_tx = random.uniform(float(SEND_SELF_AMOUNT[0]), float(SEND_SELF_AMOUNT[1]))
            p = await page.wait_for_selector('#send-value', timeout=10000)
            await p.fill("{0:.10f}".format(rand_sum_tx))

            p = await page.wait_for_selector('#chain', timeout=5000)
            await p.click()
            await asyncio.sleep(0.5)

            try:
                p = await page.wait_for_selector(f'xpath=//form//div[text()="{SEND_CHAIN}"]', timeout=2000)
                await p.click()
            except Exception:
                p = await page.wait_for_selector(f'text={SEND_CHAIN}', timeout=1000)
                await p.click()
            
            await asyncio.sleep(random.uniform(0.5, 1))
            p = await page.wait_for_selector(f'xpath=//button[@aria-autocomplete="list"]', timeout=10000)
            await p.click()
            await asyncio.sleep(random.uniform(0.5, 1))
            await page.click(f'xpath=//span[text()="{SEND_ASSET}"]', timeout=10000)
            await asyncio.sleep(2)
            
            await page.click('xpath=//form/button', timeout=10000)

            zerion_popup_window = await switch_to_page_by_title(context, 'Zerion · Send Transaction')
            await zerion_popup_window.click('text="Confirm"', timeout=10000)

            for t in range(15):
                await asyncio.sleep(1)
                if len(context.pages) < 2:
                    logger.success(f"{id} | Self send {i} | {SWAP_CHAIN} {SEND_ASSET} {rand_sum_tx}")
                    break
                if t > 12:
                    logger.error(f"{id} | Transaction execution error")
                    break
            await asyncio.sleep(random.randrange(NEXT_TX_MIN_WAIT_TIME, NEXT_TX_MAX_WAIT_TIME))
        except Exception as ex:
            logger.error(traceback.format_exc(), ex)

async def swap(id, context, page):
    rand_self_count = random.randint(SWAP_COUNT[0], SWAP_COUNT[1])
    logger.info(f"{id} | START {rand_self_count} swaps..")
    for i in range(1, rand_self_count+1):
        try:
            await page.goto('https://app.zerion.io/swap')
            p = await page.wait_for_selector('xpath=//div/div[5]/div[1]/div/div/div[1]/div[1]/div/button[1]/div/div', timeout=5000)
            await p.click()
            await asyncio.sleep(0.5)

            await page.click(f'xpath=//div/div[5]/div[1]/div/div/div[1]/div[1]/div/div/div/button/div/div/div[text()="{SWAP_CHAIN}"]', timeout=5000)
            
            await asyncio.sleep(random.uniform(0.5, 1))
            await page.click('xpath=//div[1]/div[4]/div/div[3]/div/div/div[5]/div[1]/div/div/div[1]/div[2]/label[1]/fieldset/div/div[2]/div[1]/button', timeout=10000)

            await asyncio.sleep(random.uniform(0.5, 1))
            from_asset = random.choice(FROM_ASSET_LIST)
            await page.click(f'xpath=//span[text()="{from_asset}"]', timeout=10000)

            await asyncio.sleep(random.uniform(0.5, 1))
            await page.click('xpath=//div[1]/div[4]/div/div[3]/div/div/div[5]/div[1]/div/div/div[1]/div[2]/label[2]/fieldset/div/div[2]/div[1]/button', timeout=10000)

            await asyncio.sleep(random.uniform(0.5, 1))
            p = await page.wait_for_selector('xpath=//div[1]/div[2]/input', timeout=10000)
            to_asset = random.choice(TO_ASSET_LIST)
            await p.fill(to_asset)

            await asyncio.sleep(random.uniform(1, 2))
            elements = await page.query_selector_all('xpath=//div')
            
            for el in elements:
                text_el = await el.text_content()
                if text_el.strip() == to_asset:
                    # print("Элемент найден:", el)
                    await el.click()
                    break

            await asyncio.sleep(random.uniform(1, 1.5))
            rand_sum_tx = random.uniform(float(SWAP_SELF_AMOUNT[0]), float(SWAP_SELF_AMOUNT[1]))
            p = await page.wait_for_selector('#sell-value', timeout=10000)
            await p.fill(f"{rand_sum_tx:.10f}") 
            #/html/body/div[1]/div[4]/div/div[3]/div/div/div[5]/div[1]/div/div/div[3]/button
            await page.click('xpath=//div/div/div[3]/button', timeout=10000)

            zerion_popup_window = await switch_to_page_by_title(context, 'Zerion · Send Transaction')
            await zerion_popup_window.click('text="Confirm"', timeout=10000)

            for t in range(15):
                await asyncio.sleep(1)
                if len(context.pages) < 2:
                    logger.success(f"{id} | Swap {i} | {SWAP_CHAIN} {rand_sum_tx} {from_asset} -> {to_asset}")
                    break
                if t > 12:
                    logger.error(f"{id} | Transaction execution error")
                    break
            await asyncio.sleep(random.randrange(NEXT_TX_MIN_WAIT_TIME, NEXT_TX_MAX_WAIT_TIME))
        except Exception as ex:
            logger.error(traceback.format_exc(), ex)


async def main(accounts):
    semaphore = asyncio.Semaphore(THREADS_NUM)
    tasks = [run(id, private_key, proxy, semaphore) for id, private_key, proxy in accounts]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    accounts = get_accounts()
    logger.info(f"Loaded {len(accounts)} accounts")
    asyncio.run(main(accounts))
    