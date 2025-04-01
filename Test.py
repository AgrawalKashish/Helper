from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import time

# Set up the WebDriver (ensure you have the correct driver for your browser)
driver = webdriver.Chrome()  # Or use webdriver.Firefox() if using Firefox

# Navigate to the webpage
url = "YOUR_URL_HERE"
driver.get(url)

# Wait for the page to load
time.sleep(3)

try:
    # Locate the dropdown menu
    dropdown_element = driver.find_element(By.CLASS_NAME, "jenkins-select_input")
    
    # Initialize Select class
    dropdown = Select(dropdown_element)
    
    # Iterate over all options
    for option in dropdown.options:
        value = option.get_attribute("value")
        print(f"Selecting: {value}")

        # Select the option
        dropdown.select_by_value(value)

        # Click the "Build" button
        build_button = driver.find_element(By.XPATH, "//button[text()='Build']")  # Adjust if needed
        build_button.click()

        print(f"Triggered build for: {value}")

        # Wait a bit before proceeding to the next option
        time.sleep(5)  

except Exception as e:
    print("Error:", e)

# Close the browser
driver.quit()
