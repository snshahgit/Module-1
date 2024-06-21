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
    

def get_all_rental_properties(driver, pin, house_type):
    # waiting till all placards are fetchable
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CLASS_NAME, "HomeViews"))
    )
    
    property_list = driver.find_elements(By.CLASS_NAME, "bp-Homecard__Content")
    # print(len(property_list))
    data = get_data(driver, property_list, pin, house_type)
    return data

# get data like address, price, beds, baths, sqft, parking space, images, price per square feet
def get_data(driver, property_list, pin, house_type):

    data = []
    original_window = driver.current_window_handle
    for property in property_list:
        
        property.click()
        # Wait for the new tab to open
        WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
        # Switch to the new tab
        new_window = [window for window in driver.window_handles if window != original_window][0]
        driver.switch_to.window(new_window)
        
        # Perform actions on the new tab
        address = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "full-address"))
        ).text
        # print(address)

        [price, beds, baths, sqft] = [val.text for val in WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "statsValue"))
        )]

        
        build, parking_space, price_per_sqft, hoa_fee = None, None, None, None

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

        
        # electricity_bill_info = None
        # try:

        #     vals = [val.text for val in WebDriverWait(driver, 60).until(
        #         EC.presence_of_all_elements_located((By.CSS_SELECTOR, "p.ListItem__description.font-body-small-compact.color-text-secondary"))
        #     )]
        #     print(vals)
            # for parent in parent_elements:
            #     if '$' in parent.text.lower():
            #         electricity_bill_info = parent.text

            # print(electricity_bill_info)
        # except Exception as e:
        #     # print(e)
        #     traceback.print_exc()
        #     print('Could not locate electricity bill information!')

        
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

        
        image_elements = WebDriverWait(driver, 60).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "img.landscape"))
        )
        # Extract URLs from image elements
        image_urls = [element.get_attribute('src') for element in image_elements]
        
        # print(image_urls)

        data.append({'pin':pin, 'houseType':house_type, 'address':address, 'price':price, 'beds':beds, 'baths':baths, 'sqft':sqft, 'parking':parking_space, 'construction':build, 'pricePerSqft':price_per_sqft, 'homeOwnersAssociationFees':hoa_fee, 'taxInfo':tax_info, 'imgUrls':image_urls})

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
        min_price='50K'
        max_price = '550K'
        # Minimum beds
        min_beds=1
        
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

        url+= f"zipcode/{pin}/filter/property-type={house_type},min-beds={min_beds},min-price={min_price},max-price={max_price}"
        # print(url)
        # Navigate to URL using driver.navigate().to(url)
        driver.get(url)
        data = get_all_rental_properties(driver, pin, house_type)
        
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
    