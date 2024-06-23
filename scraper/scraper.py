from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
import time
import random
import json
import traceback

def login(driver, username, password):


    # print('login')
    loginbutton = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "combinedLoginLinkWrapper"))
    )
    loginbutton.click()

    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "guts"))
    )

    email = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "email"))
    )
    email.send_keys(username)

    next = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "button.Button.submitButton.primary"))
    ).click()

    passkey = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "password"))
    )
    passkey.send_keys(password)

    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "button.Button.submitButton.v3.primary"))
    ).click()




def get_to_listings(driver):
    # print('listings')

    # Wait for the search bar to be present
    searchbar = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "search-box-input"))
    )
    searchbar.clear()
    searchbar.send_keys("Jersey City" + Keys.ENTER)
    # print('done typing')
    # Wait for the search button to be clickable and click it
    # print('Searched')


def get_all_rental_properties(driver, pin, house_type, safety, weather):
    # waiting till all placards are fetchable
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CLASS_NAME, "HomeViews"))
    )

    property_list = driver.find_elements(By.CLASS_NAME, "bp-Homecard__Content")
    # print(len(property_list))
    
    data = get_data(driver, property_list, pin, house_type, safety, weather)
    return data

def get_weather(driver, pin, base_url):
    
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

def get_crime(driver, pin, base_url):

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

# get data like address, price, beds, baths, sqft, parking space, images, price per square feet
def get_data(driver, property_list, pin, house_type, safety, weather):

    data = []
    original_window = driver.current_window_handle
    for property in property_list:

        property.click()
        # Wait for the new tab to open
        WebDriverWait(driver, 30).until(EC.number_of_windows_to_be(2))
        # Switch to the new tab
        new_window = [window for window in driver.window_handles if window != original_window][0]
        driver.switch_to.window(new_window)

        address = None
        try:
            # Perform actions on the new tab
            address = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "full-address"))
            ).text
            # print(address)
        except:
            print("No information on the address!")


        [price, beds, baths, sqft] = [val.text for val in WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "statsValue"))
        )]


        build, parking_space, price_per_sqft, hoa_fee = None, None, None, None
        try:
            parent_elements = driver.find_elements(By.CLASS_NAME, "keyDetails-row")

            for parent in parent_elements:
                if 'Built in' in parent.text and build is None:
                    build = parent.text
                    # print(f"Built in: {build}")

                if 'parking space' in parent.text and parking_space is None:
                    parking_space = parent.text
                    # print(f"Parking Space: {parking_space}")

                if 'per sq ft' in parent.text and price_per_sqft is None:
                    price_per_sqft = parent.text
                    # print(f"Price per Sq Ft: {price_per_sqft}")

                if 'HOA fee' in parent.text and hoa_fee is None:
                    hoa_fee = parent.text
                    # print(f"HOA fee: {hoa_fee}")
        except:
            print("No information on Build, Parking space, Price per square ft, and HOA fee!")


        tax_info = None
        try:

            parent_elements = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "amenity-group"))
            )

            for parent in parent_elements:
                if "Tax" in parent.text:
                    tax_info = parent.text

            # print(tax_info)
        except:
            print('Could not locate tax information!')

        image_urls = None
        try: 
            image_elements = WebDriverWait(driver, 60).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "img.landscape"))
            )
            # Extract URLs from image elements
            image_urls = [element.get_attribute('src') for element in image_elements]
        except:
            print("No images to show!")
        # print(image_urls)
        
        transitScore, sideWalkScore = None, None
        try:
            amenities = WebDriverWait(driver, 40).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "percentage"))
            )
            sideWalkScore = amenities[0].text
            transitScore = amenities[1].text
            # print(transitScore, sideWalkScore)
        except:
            print('No information on public transit and sidewalks!')

        schoolCount = None
        try:
            schools = WebDriverWait(driver, 40).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "ItemPickerPill__label--count"))
            )
            schoolCount = [school.text for school in schools][0]
            # print(schoolCount)
        except:
            print("No school information")

        data.append({'pin':pin, 'houseType':house_type, 'address':address, 'price':price, 'beds':beds, 'baths':baths, 'sqft':sqft, 'parking':parking_space, 'construction':build, 'pricePerSqft':price_per_sqft, 'homeOwnersAssociationFees':hoa_fee, 'taxInfo':tax_info, 'imgUrls':image_urls, 'transitScore':transitScore, 'sideWalkScore':sideWalkScore, 'schoolCount':schoolCount, 'safety':safety, 'weather':weather})

        driver.close()
        driver.switch_to.window(original_window)        
        break
    return data


def main():
    try:
        # sample url: base url/zipcode/{pin}/filter/property-type={house_type},min-beds={min_beds},min-price={min_price},max-price={max_price}
        # default value for pin
        pin = '07201'
        # House type: House, Townhouse, Condo
        house_type = random.choice(['house', 'townhouse', 'condo'])
        # Budget 50K to 10M (max-price)
        min_price= None # '50K'
        max_price = None # '2M'
        # Minimum beds
        min_beds= 1 # 2.5

        # Initialize the Chrome driver

        chrome_options = Options()
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(60)  # Adjust timeout as needed
        url = 'https://www.redfin.com/'

        username = 'shahsau1@msu.edu'
        password = 'P@ssw0rd'
        driver.get(url)
        login(driver, username, password)


        # Ensure the login process is complete
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "userMenu"))
        )

        safety = get_crime(driver, pin, base_url= url)
        # print(safety)
        weather = get_weather(driver, pin, base_url= url)
        print(safety, weather)
        url+= f"zipcode/{pin}/filter/property-type={house_type},min-beds={min_beds},min-price={min_price},max-price={max_price}"
        # print(url)
        # Navigate to URL using driver.navigate().to(url)
        driver.get(url)
        data = get_all_rental_properties(driver, pin, house_type, safety, weather)

        print(json.dumps(data))




        # Optional: Wait for the results page to load
        time.sleep(10)  # You might want to replace this with a more specific wait

    except TimeoutException:
        print("Loading took too much time!")

    finally:
        # Close the driver
        driver.quit()



if __name__=="__main__":
    main()
