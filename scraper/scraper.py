import asyncio
import aiohttp
from aiohttp import ClientSession
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import random
import traceback

async def login(driver, username, password):
    try:
        login_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "combinedLoginLinkWrapper"))
        )
        login_button.click()

        email = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "email"))
        )
        email.send_keys(username)

        next_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "button.Button.submitButton.primary"))
        )
        next_button.click()

        password_field = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "password"))
        )
        password_field.send_keys(password)

        submit_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "button.Button.submitButton.v3.primary"))
        )
        submit_button.click()

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "userMenu"))
        )
    except (TimeoutException, NoSuchElementException, WebDriverException) as e:
        print(f"Error during login: {e}")
        raise e

async def get_all_rental_properties(driver, pin, house_type):
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "HomeViews"))
        )
        property_list = driver.find_elements(By.CLASS_NAME, "bp-Homecard__Content")
        data = await get_data(driver, property_list, pin, house_type)
        return data
    except (TimeoutException, WebDriverException) as e:
        print(f"Error while fetching rental properties: {e}")
        return []

async def get_data(driver, property_list, pin, house_type):
    data = []
    original_window = driver.current_window_handle

    for property in property_list:
        try:
            property.click()
            WebDriverWait(driver, 20).until(EC.number_of_windows_to_be(2))
            new_window = [window for window in driver.window_handles if window != original_window][0]
            driver.switch_to.window(new_window)

            address = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "full-address"))
            ).text

            price, beds, baths, sqft = [val.text for val in WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "statsValue"))
            )]

            build, parking_space, price_per_sqft, hoa_fee = None, None, None, None
            parent_elements = driver.find_elements(By.CLASS_NAME, "keyDetails-row")

            for parent in parent_elements:
                if 'Built in' in parent.text and not build:
                    build = parent.text
                if 'parking space' in parent.text and not parking_space:
                    parking_space = parent.text
                if 'per sq ft' in parent.text and not price_per_sqft:
                    price_per_sqft = parent.text
                if 'HOA fee' in parent.text and not hoa_fee:
                    hoa_fee = parent.text

            tax_info = None
            parent_elements = driver.find_elements(By.CLASS_NAME, "amenity-group")
            for parent in parent_elements:
                if "Tax" in parent.text:
                    tax_info = parent.text

            image_elements = driver.find_elements(By.CSS_SELECTOR, "img.landscape")
            image_urls = [element.get_attribute('src') for element in image_elements]

            data.append({
                'pin': pin,
                'houseType': house_type,
                'address': address,
                'price': price,
                'beds': beds,
                'baths': baths,
                'sqft': sqft,
                'parking': parking_space,
                'construction': build,
                'pricePerSqft': price_per_sqft,
                'homeOwnersAssociationFees': hoa_fee,
                'taxInfo': tax_info,
                'imgUrls': image_urls
            })

            driver.close()
            driver.switch_to.window(original_window)
        except (TimeoutException, NoSuchElementException, WebDriverException) as e:
            print(f"Error while fetching property data: {e}")
            driver.close()
            driver.switch_to.window(original_window)

    return data

async def send_data(session, server_url, data, pin):
    try:
        async with session.post(server_url, json=data) as response:
            if response.status == 200:
                print(f"Successfully inserted data for pin code {pin}")
            else:
                print(f"Failed to insert data for pin code {pin}: {await response.text()}")
    except Exception as e:
        print(f"An error occurred while sending data for pin code {pin} to the server: {e}")
        traceback.print_exc()

async def scrape_properties(pin_codes):
    server_url = 'http://localhost:5000/add_properties'

    async with aiohttp.ClientSession() as session:
        for pin in pin_codes:
            chrome_options = Options()
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--ignore-ssl-errors')
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            driver.set_page_load_timeout(60)
            url = 'https://www.redfin.com/'

            username = 'shahsau1@msu.edu'
            password = 'P@ssw0rd'
            driver.get(url)
            
            await retry(login, 3, driver, username, password)

            try:
                house_type = random.choice(['house', 'townhouse', 'condo'])
                driver.get(f"https://www.redfin.com/zipcode/{pin}")
                data = await retry(get_all_rental_properties, 3, driver, pin, house_type)
                if data:
                    print(data)
                    asyncio.create_task(send_data(session, server_url, data, pin))
                await asyncio.sleep(random.uniform(5, 10))  # Random sleep to avoid getting blocked
            except (TimeoutException, WebDriverException) as e:
                print(f"Error occurred for pin code {pin}: {e}")
            except Exception as e:
                print(f"An unexpected error occurred for pin code {pin}: {e}")
                traceback.print_exc()
            finally:
                driver.quit()

async def retry(func, max_attempts=3, *args, **kwargs):
    attempts = 0
    while attempts < max_attempts:
        try:
            result = await func(*args, **kwargs)
            return result
        except (TimeoutException, WebDriverException) as e:
            print(f"Error occurred: {e}. Retrying {attempts + 1}/{max_attempts}...")
            attempts += 1
            await asyncio.sleep(5)  # Adding delay between retries
    print(f"Failed after {max_attempts} attempts.")
    return None

async def main():
    file_path = 'zipcodes.txt'
    try:
        with open(file_path, 'r') as file:
            pin_codes = [line.strip() for line in file.readlines()]
            await scrape_properties(pin_codes)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")

if __name__ == "__main__":
    asyncio.run(main())
