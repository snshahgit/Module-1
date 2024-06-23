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
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import random
import traceback

async def login(driver, username, password):
    try:
        login_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "combinedLoginLinkWrapper"))
        )
        login_button.click()
        
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "guts"))
        )

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

    except (TimeoutException, NoSuchElementException, WebDriverException) as e:
        print(f"Error during login: {e}")
        raise e

async def get_all_rental_properties(driver, pin, house_type, safety, weather):
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "HomeViews"))
        )
        property_list = driver.find_elements(By.CLASS_NAME, "bp-Homecard__Content")
        data = await get_data(driver, property_list, pin, house_type, safety, weather)
        return data
    except (TimeoutException, WebDriverException) as e:
        print(f"Error while fetching rental properties: {e}")
        return []

async def get_data(driver, property_list, pin, house_type, safety, weather):
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
                if 'Built in' in parent.text and build is None:
                    build = parent.text
                if 'parking space' in parent.text and parking_space is None:
                    parking_space = parent.text
                if 'per sq ft' in parent.text and price_per_sqft is None:
                    price_per_sqft = parent.text
                if 'HOA fee' in parent.text and hoa_fee is None:
                    hoa_fee = parent.text
            try:
                tax_info = None
                parent_elements = WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "amenity-group"))
                )
                for parent in parent_elements:
                    if "Tax" in parent.text:
                        tax_info = parent.text
            except:
                print('Could not locate tax information!')
            image_elements = driver.find_elements(By.CSS_SELECTOR, "img.landscape")
            image_urls = [element.get_attribute('src') for element in image_elements]
            transitScore, sideWalkScore = None, None
            try:
                amenities = WebDriverWait(driver, 40).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "percentage"))
                )
                sideWalkScore = amenities[0].text
                transitScore = amenities[1].text
            except:
                print('No information on public transit and sidewalks!')

            schoolCount = None
            try:
                schools = WebDriverWait(driver, 40).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "ItemPickerPill__label--count"))
                )
                schoolCount = [school.text for school in schools][0]
            except:
                print("No school information")

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
                'imgUrls': image_urls,
                'transitScore':transitScore,
                'sideWalkScore':sideWalkScore, 
                'schoolCount':schoolCount,
                'safety':safety, 
                'weather':weather
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

async def get_crime(driver, pin, base_url):

    driver.get("https://crimegrade.org/")
    zipcode = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, "FormBodyInput"))
    )
    zipcode.send_keys(pin + Keys.RETURN)
    crime = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, "overallGradeLetter"))
    )
    crime = crime.text
    crime_range = ['A+','A','A-','B+','B','B-','C+','C','C-','D+','D','D-','E+','E','E-','F+','F','F-']
    safety = ((len(crime_range) - crime_range.index(crime))/len(crime_range))
    driver.get(base_url)
    return safety

async def get_weather(driver, pin, base_url):
    
    driver.get(f"https://riskfactor.com/zip/00000-mi/{pin}_fsid/flood")
    flood = WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".my-4 > div:nth-child(1) > p:nth-child(1) > span:nth-child(2)"))
    ).text
    # print(flood)

    driver.get(f"https://riskfactor.com/zip/00000-mi/{pin}_fsid/fire")
    fire = WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".pt-2 > div:nth-child(1) > p:nth-child(3) > span:nth-child(2)"))
    ).text
    # print(fire)

    driver.get(f"https://riskfactor.com/zip/00000-mi/{pin}_fsid/wind")
    wind = WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".pt-2 > div:nth-child(1) > p:nth-child(1) > span:nth-child(1)"))
    ).text
    # print(wind)

    driver.get(f"https://riskfactor.com/zip/00000-mi/{pin}_fsid/air")
    air = WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".pt-2 > div:nth-child(1) > p:nth-child(1) > span:nth-child(2)"))
    ).text
    # print(air)

    driver.get(f"https://riskfactor.com/zip/00000-mi/{pin}_fsid/heat")
    heat = WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".pt-2 > div:nth-child(1) > p:nth-child(1) > span:nth-child(2)"))
    ).text
    # print(heat)

    driver.get(base_url)
    
    weather = [flood, fire, wind, air, heat]

    return weather

async def scrape_properties(pin_codes):
    server_url = 'http://localhost:5000/add_properties'
    
    async with aiohttp.ClientSession() as session:
        for pin in pin_codes:
            try:
                chrome_options = Options()
                # chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--ignore-certificate-errors')
                chrome_options.add_argument('--ignore-ssl-errors')
                
                driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
                driver.set_page_load_timeout(60)
                url = 'https://www.redfin.com/'

                username = 'shahsau1@msu.edu'
                password = 'P@ssw0rd'
                driver.get(url)
                await login(driver, username, password)
                safety = await get_crime(driver, pin, base_url= url)
                weather = await get_weather(driver, pin, base_url= url)
                house_type = random.choice(['house', 'townhouse', 'condo'])
                driver.get(f"https://www.redfin.com/zipcode/{pin}")
                data = await get_all_rental_properties( driver, pin, house_type,safety,weather)
                if data:
                    asyncio.create_task(send_data(session, server_url, data, pin))
                await asyncio.sleep(random.uniform(5, 10))  # Random sleep to avoid getting blocked
            except (TimeoutException, WebDriverException) as e:
                print(f"Error occurred for pin code {pin}: {e}")
            except Exception as e:
                print(f"An unexpected error occurred for pin code {pin}: {e}")
                traceback.print_exc()
            finally:
                driver.quit()


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
