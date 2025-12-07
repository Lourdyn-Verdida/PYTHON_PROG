from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import csv
import os

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Set CSV output path in the same directory as the script
CSV_OUTPUT_PATH = os.path.join(SCRIPT_DIR, "scraped_data.csv")

# Initialize the CSV file with headers
csv_headers = [
    'Entry_Number',
    'Base_Value', 'Base_Reaction_Role',
    'Solvent_Value', 'Solvent_Reaction_Role',
    'Amine_Value', 'Amine_Reaction_Role',
    'Aryl_Halide_Value', 'Aryl_Halide_Reaction_Role',
    'Metal_Value', 'Metal_Reaction_Role',
    'Ligand_Value', 'Ligand_Reaction_Role',
    'Product_Value', 'Product_Reaction_Role',
    'Yield_Type', 'Yield_Value'
]

# Create CSV file and write headers
with open(CSV_OUTPUT_PATH, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(csv_headers)

print(f"✓ CSV file created at: {CSV_OUTPUT_PATH}")

# Initialize WebDriver (Selenium 4.6+ has built-in driver management)
print("Initializing Chrome WebDriver...")
try:
    driver = webdriver.Chrome()
    print("✓ Chrome WebDriver initialized successfully")
except Exception as e:
    print(f"Error initializing Chrome: {e}")
    print("\nTroubleshooting steps:")
    print("1. Make sure Google Chrome is installed")
    print("2. Update Selenium: pip install --upgrade selenium")
    print("3. If still failing, install webdriver-manager: pip install webdriver-manager")
    exit(1)

def wait_ready(timeout=20):
    """Wait for page to fully load"""
    try:
        WebDriverWait(driver, timeout).until(lambda d: d.execute_script('return document.readyState') == 'complete')
        time.sleep(0.5)  # Small buffer after page load
    except Exception:
        time.sleep(1)

def wait_for_element(by, selector, timeout=20, condition="presence"):
    """Wait for element to be present/clickable before proceeding"""
    try:
        if condition == "clickable":
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, selector))
            )
        else:  # presence
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
        return element
    except Exception as e:
        print(f"⚠ Timeout waiting for element: {selector} ({e})")
        return None

def write_to_csv(entry_num, data_dict):
    """Write scraped data to CSV file"""
    row = [
        entry_num,
        data_dict.get('base_value', ''),
        data_dict.get('base_reaction_role', ''),
        data_dict.get('solvent_value', ''),
        data_dict.get('solvent_reaction_role', ''),
        data_dict.get('amine_value', ''),
        data_dict.get('amine_reaction_role', ''),
        data_dict.get('aryl_halide_value', ''),
        data_dict.get('aryl_halide_reaction_role', ''),
        data_dict.get('metal_value', ''),
        data_dict.get('metal_reaction_role', ''),
        data_dict.get('ligand_value', ''),
        data_dict.get('ligand_reaction_role', ''),
        data_dict.get('product_value', ''),
        data_dict.get('product_reaction_role', ''),
        data_dict.get('yield_type', ''),
        data_dict.get('yield_value', '')
    ]
    
    with open(CSV_OUTPUT_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(row)
    
    print(f"✓ Written entry #{entry_num} to CSV")

def scrape_entry(entry_number):
    """Scrape all data from one entry and return as dictionary"""
    data = {}
    
    # Scroll down to find the code button for Base tab
    print("\nScrolling to find code button...")
    try:
        for _ in range(10):
            driver.execute_script("window.scrollBy(0, 75);")
            time.sleep(0.3)
        
        code_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-v-144eb116].button"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", code_button)
        time.sleep(0.5)
        code_button.click()
        print("✓ Clicked code button (<>) for Base")
        time.sleep(2)
    except Exception as e:
        print(f"⚠ Failed to find/click code button: {e}")

    # Scrape Base data
    print("\nScraping Base data...")
    try:
        time.sleep(1)
        code_elements = driver.find_elements(By.CSS_SELECTOR, "pre, code")
        for element in code_elements:
            try:
                text = element.text
                if '"value":' in text and 'base_value' not in data:
                    value_match = re.search(r'"value":\s*"([^"]+)"', text)
                    if value_match:
                        data['base_value'] = value_match.group(1)
                        print(f"✓ Found Base value: {data['base_value']}")
                if 'reaction_role' in text and 'base_reaction_role' not in data:
                    role_match = re.search(r'reaction_role:\s*(\w+)', text)
                    if role_match:
                        data['base_reaction_role'] = role_match.group(1)
                        print(f"✓ Found Base reaction_role: {data['base_reaction_role']}")
                if 'base_value' in data and 'base_reaction_role' in data:
                    break
            except Exception:
                continue
    except Exception as e:
        print(f"⚠ Failed to scrape Base data: {e}")

    # Close code view
    try:
        close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-v-419ab5e1].close"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", close_button)
        time.sleep(0.3)
        close_button.click()
        time.sleep(1)
    except Exception as e:
        print(f"⚠ Failed to close code view: {e}")

    # Solvent tab
    try:
        solvent_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'tab') and contains(text(), 'Solvent')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", solvent_tab)
        time.sleep(0.5)
        solvent_tab.click()
        time.sleep(1)
        
        code_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-v-144eb116].button"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", code_button)
        time.sleep(0.5)
        code_button.click()
        time.sleep(2)
        
        code_elements = driver.find_elements(By.CSS_SELECTOR, "pre, code")
        for element in code_elements:
            try:
                text = element.text
                if '"value":' in text and 'solvent_value' not in data:
                    value_match = re.search(r'"value":\s*"([^"]+)"', text)
                    if value_match:
                        data['solvent_value'] = value_match.group(1)
                if 'reaction_role' in text and 'solvent_reaction_role' not in data:
                    role_match = re.search(r'reaction_role:\s*(\w+)', text)
                    if role_match:
                        data['solvent_reaction_role'] = role_match.group(1)
                if 'solvent_value' in data and 'solvent_reaction_role' in data:
                    break
            except Exception:
                continue
        
        close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-v-419ab5e1].close"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", close_button)
        time.sleep(0.3)
        close_button.click()
        time.sleep(1)
    except Exception as e:
        print(f"⚠ Solvent scraping error: {e}")

    # Amine tab
    try:
        amine_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'tab') and contains(text(), 'amine')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", amine_tab)
        time.sleep(0.5)
        amine_tab.click()
        time.sleep(1)
        
        code_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-v-144eb116].button"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", code_button)
        time.sleep(0.5)
        code_button.click()
        time.sleep(2)
        
        code_elements = driver.find_elements(By.CSS_SELECTOR, "pre, code")
        for element in code_elements:
            try:
                text = element.text
                if '"value":' in text and 'amine_value' not in data:
                    value_match = re.search(r'"value":\s*"([^"]+)"', text)
                    if value_match:
                        data['amine_value'] = value_match.group(1)
                if 'reaction_role' in text and 'amine_reaction_role' not in data:
                    role_match = re.search(r'reaction_role:\s*(\w+)', text)
                    if role_match:
                        data['amine_reaction_role'] = role_match.group(1)
                if 'amine_value' in data and 'amine_reaction_role' in data:
                    break
            except Exception:
                continue
        
        close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-v-419ab5e1].close"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", close_button)
        time.sleep(0.3)
        close_button.click()
        time.sleep(1)
    except Exception as e:
        print(f"⚠ Amine scraping error: {e}")

    # Aryl halide tab
    try:
        aryl_halide_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'tab') and contains(text(), 'aryl halide')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", aryl_halide_tab)
        time.sleep(0.5)
        aryl_halide_tab.click()
        time.sleep(1)
        
        code_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-v-144eb116].button"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", code_button)
        time.sleep(0.5)
        code_button.click()
        time.sleep(2)
        
        code_elements = driver.find_elements(By.CSS_SELECTOR, "pre, code")
        for element in code_elements:
            try:
                text = element.text
                if '"value":' in text and 'aryl_halide_value' not in data:
                    value_match = re.search(r'"value":\s*"([^"]+)"', text)
                    if value_match:
                        data['aryl_halide_value'] = value_match.group(1)
                if 'reaction_role' in text and 'aryl_halide_reaction_role' not in data:
                    role_match = re.search(r'reaction_role:\s*(\w+)', text)
                    if role_match:
                        data['aryl_halide_reaction_role'] = role_match.group(1)
                if 'aryl_halide_value' in data and 'aryl_halide_reaction_role' in data:
                    break
            except Exception:
                continue
        
        close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-v-419ab5e1].close"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", close_button)
        time.sleep(0.3)
        close_button.click()
        time.sleep(1)
    except Exception as e:
        print(f"⚠ Aryl halide scraping error: {e}")

    # Metal and ligand tab
    try:
        metal_ligand_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'tab') and contains(text(), 'metal and ligand')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", metal_ligand_tab)
        time.sleep(0.5)
        metal_ligand_tab.click()
        time.sleep(1)
        
        # Metal
        code_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-v-144eb116].button"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", code_button)
        time.sleep(0.5)
        code_button.click()
        time.sleep(2)
        
        code_elements = driver.find_elements(By.CSS_SELECTOR, "pre, code")
        for element in code_elements:
            try:
                text = element.text
                if '"value":' in text and 'metal_value' not in data:
                    value_match = re.search(r'"value":\s*"([^"]+)"', text)
                    if value_match:
                        data['metal_value'] = value_match.group(1)
                if 'reaction_role' in text and 'metal_reaction_role' not in data:
                    role_match = re.search(r'reaction_role:\s*(\w+)', text)
                    if role_match:
                        data['metal_reaction_role'] = role_match.group(1)
                if 'metal_value' in data and 'metal_reaction_role' in data:
                    break
            except Exception:
                continue
        
        close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-v-419ab5e1].close"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", close_button)
        time.sleep(0.3)
        close_button.click()
        time.sleep(1)
        
        # Ligand
        code_buttons = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[data-v-144eb116].button"))
        )
        if len(code_buttons) > 1:
            code_button = code_buttons[1]
        else:
            code_button = code_buttons[0]
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", code_button)
        time.sleep(0.5)
        code_button.click()
        time.sleep(2)
        
        code_elements = driver.find_elements(By.CSS_SELECTOR, "pre, code")
        for element in code_elements:
            try:
                text = element.text
                if '"value":' in text and 'ligand_value' not in data:
                    value_match = re.search(r'"value":\s*"([^"]+)"', text)
                    if value_match:
                        data['ligand_value'] = value_match.group(1)
                if 'reaction_role' in text and 'ligand_reaction_role' not in data:
                    role_match = re.search(r'reaction_role:\s*(\w+)', text)
                    if role_match:
                        data['ligand_reaction_role'] = role_match.group(1)
                if 'ligand_value' in data and 'ligand_reaction_role' in data:
                    break
            except Exception:
                continue
        
        close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-v-419ab5e1].close"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", close_button)
        time.sleep(0.3)
        close_button.click()
        time.sleep(1)
    except Exception as e:
        print(f"⚠ Metal/ligand scraping error: {e}")

    # Product
    try:
        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(1)
        
        code_button = WebDriverWait(driver, 12).until(
            EC.element_to_be_clickable((By.XPATH,
                "//div[contains(@class,'compound')][.//div[contains(@class,'role') and contains(.,'product')]]//div[contains(@class,'raw')]//div[contains(@class,'button')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", code_button)
        time.sleep(0.5)
        code_button.click()
        time.sleep(2)
        
        code_elements = driver.find_elements(By.CSS_SELECTOR, "pre, code")
        for element in code_elements:
            try:
                text = element.text
                if '"value":' in text and 'product_value' not in data:
                    m = re.search(r'"value":\s*"([^"]+)"', text)
                    if m:
                        data['product_value'] = m.group(1)
                if 'reaction_role' in text and 'product_reaction_role' not in data:
                    r = re.search(r'reaction_role:\s*(\w+)', text)
                    if r:
                        data['product_reaction_role'] = r.group(1)
                if 'product_value' in data and 'product_reaction_role' in data:
                    break
            except Exception:
                continue
        
        close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-v-419ab5e1].close"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", close_button)
        time.sleep(0.3)
        close_button.click()
        time.sleep(1)
    except Exception as e:
        print(f"⚠ Product scraping error: {e}")

    # Yield
    try:
        yield_button = WebDriverWait(driver, 12).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-v-5fabe866].button"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", yield_button)
        time.sleep(0.5)
        yield_button.click()
        time.sleep(2)
        
        code_elements = driver.find_elements(By.CSS_SELECTOR, "pre, code")
        for element in code_elements:
            try:
                text = element.text
                if '"type"' in text and 'yield_type' not in data:
                    m = re.search(r'"type":\s*"([^"]+)"', text)
                    if m:
                        data['yield_type'] = m.group(1)
                if '"value"' in text and 'yield_value' not in data:
                    v = re.search(r'"value":\s*([0-9.+\-eE]+)', text)
                    if v:
                        data['yield_value'] = v.group(1)
                if 'yield_type' in data and 'yield_value' in data:
                    break
            except Exception:
                continue
        
        close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-v-419ab5e1].close"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", close_button)
        time.sleep(0.3)
        close_button.click()
        time.sleep(1)
    except Exception as e:
        print(f"⚠ Yield scraping error: {e}")
    
    return data

def process_dataset(dataset_url, browse_handle):
    """Process a single dataset by scraping all its entries"""
    print(f"\n{'='*80}")
    print(f"Processing dataset: {dataset_url}")
    print(f"{'='*80}")
    
    # Open dataset in new tab
    driver.execute_script("window.open(arguments[0], '_blank');", dataset_url)
    time.sleep(2)
    
    # Switch to the new dataset tab
    driver.switch_to.window(driver.window_handles[-1])
    wait_ready(20)
    print("✓ Dataset page loaded")
    time.sleep(2)
    
    # Set pagination to 100
    print("\nSetting pagination to 100...")
    try:
        # Wait for pagination dropdown to be present
        for _ in range(15):
            driver.execute_script("window.scrollBy(0, 300);")
            time.sleep(0.3)
        
        pagination_select = wait_for_element(By.CSS_SELECTOR, "select#pagination", timeout=15, condition="presence")
        if pagination_select:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", pagination_select)
            time.sleep(0.5)
            
            Select(pagination_select).select_by_value('100')
            print("✓ Selected pagination: 100")
            wait_ready(10)  # Wait for page to reload after pagination change
            time.sleep(2)
        else:
            raise Exception("Pagination dropdown not found")
        
    except Exception as e:
        print(f"⚠ Failed to set pagination: {e}")
        try:
            driver.execute_script("document.querySelector('select#pagination').value = '100'; document.querySelector('select#pagination').dispatchEvent(new Event('change'));")
            print("✓ Set pagination to 100 (JS fallback)")
            wait_ready(10)
            time.sleep(2)
        except Exception as e2:
            print(f"⚠ Pagination fallback also failed: {e2}")
    
    # Scroll to top
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)
    
    # Get dataset handle
    dataset_handle = driver.current_window_handle
    
    # Wait for View Full Details buttons to load
    print("\nWaiting for entries to load...")
    time.sleep(2)
    
    # Find all View Full Details buttons
    vfd_buttons = driver.find_elements(By.CSS_SELECTOR, "button[data-v-652da20a='']")
    total_buttons = len(vfd_buttons)
    print(f"✓ Found {total_buttons} entries in this dataset")
    
    # Limit to 100 entries maximum
    max_entries = min(100, total_buttons)
    print(f"✓ Will process {max_entries} entries (limited to 100)")
    
    entry_count = 0
    for idx in range(max_entries):
        try:
            vfd_btn = vfd_buttons[idx]
            entry_count += 1
            print(f"\n{'='*60}")
            print(f"Processing Entry #{entry_count} (Button {idx+1}/{max_entries})")
            print(f"{'='*60}")
            
            # Wait for button to be ready
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", vfd_btn)
            time.sleep(0.5)
            
            # Get target URL
            parent_link = vfd_btn.find_element(By.XPATH, "ancestor::a[@href]")
            target_url = parent_link.get_attribute('href')
            
            # Open in new tab
            driver.execute_script("window.open(arguments[0], '_blank');", target_url)
            time.sleep(2)
            
            # Switch to new tab
            driver.switch_to.window(driver.window_handles[-1])
            wait_ready(20)
            print("✓ Entry details page loaded")
            time.sleep(2)
            
            # Scrape the entry
            entry_data = scrape_entry(entry_count)
            write_to_csv(entry_count, entry_data)
            
            # Close tab and return to dataset
            driver.close()
            driver.switch_to.window(dataset_handle)
            time.sleep(1)
            
        except Exception as e:
            print(f"⚠ Error processing entry {entry_count}: {e}")
            try:
                # Attempt to close and return to dataset tab
                if len(driver.window_handles) > 1:
                    driver.close()
                driver.switch_to.window(dataset_handle)
            except:
                pass
            continue
    
    print(f"\n✓ Finished processing dataset. Total entries: {entry_count}")
    
    # Close dataset tab and return to browse page
    print("\nClosing dataset tab and returning to browse page...")
    driver.close()
    driver.switch_to.window(browse_handle)
    time.sleep(1)
    print("✓ Returned to browse page")

# Main execution
print("\n" + "="*80)
print("Starting Web Scraping Process")
print("="*80)

# Navigate to home page first
driver.get("https://open-reaction-database.org/")
wait_ready()
print("✓ Navigated to home page")
time.sleep(2)

# Click Browse button in navbar
print("\nClicking Browse button in navbar...")
try:
    browse_btn = wait_for_element(By.CSS_SELECTOR, "a[href='/browse'].nav-link", timeout=20, condition="clickable")
    if browse_btn:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", browse_btn)
        time.sleep(0.5)
        browse_btn.click()
        print("✓ Clicked Browse button")
        wait_ready()
        time.sleep(3)
    else:
        raise Exception("Browse button not found")
except Exception as e:
    print(f"⚠ Failed to click Browse button: {e}")
    print("Attempting to navigate directly to browse page...")
    driver.get("https://open-reaction-database.org/browse")
    wait_ready()
    time.sleep(3)

# Step 1: Change entries per page to 100
print("\nSetting pagination to 100...")
try:
    dropdown = wait_for_element(By.CSS_SELECTOR, "select#pagination", timeout=15, condition="presence")
    if dropdown:
        driver.execute_script("arguments[0].scrollIntoView();", dropdown)
        time.sleep(1)

        # Try normal select
        Select(dropdown).select_by_value("100")
        print("✔ Changed entries to 100 (via Select)")
        wait_ready(10)  # Wait for page reload
        time.sleep(3)
    else:
        raise Exception("Pagination dropdown not found")
except Exception as e:
    print(f"⚠ Error with Select: {e}")
    # Fallback using JS
    try:
        driver.execute_script("""
            var s=document.querySelector('select#pagination');
            s.value='100';
            s.dispatchEvent(new Event('change',{bubbles:true}));
        """)
        print("✔ Changed entries to 100 (via JS fallback)")
        wait_ready(10)
        time.sleep(3)
    except Exception as e2:
        print(f"⚠ JS fallback failed: {e2}")

# Loop through pages and process all datasets
page = 1
total_datasets_processed = 0

# Save the browse page handle
browse_handle = driver.current_window_handle

while True:
    print(f"\n{'#'*80}")
    print(f"PROCESSING PAGE: {page}")
    print(f"{'#'*80}")
    
    # Wait for dataset links to load
    print("Waiting for dataset links to load...")
    time.sleep(2)
    
    # Get all dataset links on current page
    links = driver.find_elements(By.CSS_SELECTOR, 'a[href^="/dataset/ord_dataset-"]')
    dataset_urls = [link.get_attribute("href") for link in links]
    
    print(f"✓ Found {len(dataset_urls)} datasets on page {page}")
    
    # Process each dataset
    for idx, url in enumerate(dataset_urls):
        total_datasets_processed += 1
        print(f"\n[Dataset {idx+1}/{len(dataset_urls)} on Page {page}]")
        
        # Process dataset in new tab, pass browse_handle so we can return to it
        process_dataset(url, browse_handle)
        
        # We're already back on browse page, no need to navigate
        print("✓ Back on browse page, ready for next dataset")
        time.sleep(1)
    
    # Try to click NEXT to go to next page
    print(f"\n{'='*80}")
    print("Attempting to navigate to next page...")
    try:
        next_btn = wait_for_element(By.CSS_SELECTOR, "div.next.paginav span.word", timeout=10, condition="clickable")
        
        if not next_btn:
            print("❌ NEXT button not found -> All pages processed!")
            break
        
        # Check if next button is disabled
        if "disabled" in next_btn.get_attribute("class"):
            print("❌ NEXT button disabled -> All pages processed!")
            break
        
        driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
        time.sleep(0.5)
        next_btn.click()
        page += 1
        print(f"✔ NEXT clicked - Moving to page {page}")
        wait_ready(15)  # Wait for next page to load
        time.sleep(3)
    except Exception as e:
        print(f"No NEXT button or error -> All pages processed! ({e})")
        break
    
    # Try to click NEXT to go to next page
    print(f"\n{'='*80}")
    print("Attempting to navigate to next page...")
    try:
        next_btn = driver.find_element(By.CSS_SELECTOR, "div.next.paginav span.word")
        
        # Check if next button is disabled
        if "disabled" in next_btn.get_attribute("class"):
            print("❌ NEXT button disabled -> All pages processed!")
            break
        
        driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
        next_btn.click()
        page += 1
        print(f"✔ NEXT clicked - Moving to page {page}")
        time.sleep(4)
    except Exception as e:
        print(f"No NEXT button or error -> All pages processed! ({e})")
        break

# Final summary
print(f"\n{'='*80}")
print("SCRAPING COMPLETE!")
print(f"{'='*80}")
print(f"Total pages processed: {page}")
print(f"Total datasets processed: {total_datasets_processed}")
print(f"CSV saved to: {CSV_OUTPUT_PATH}")
print(f"{'='*80}")

driver.quit()