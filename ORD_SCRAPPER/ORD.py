from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import csv
import os

def scrape_ord_details(driver, ord_url, dataset_dir):
    wait = WebDriverWait(driver, 20)
    driver.get(ord_url)
    time.sleep(2)

    inputs_scraped_data = []
    products_scraped_data = []
    measurements_scraped_data = []

    def extract_identifiers_and_role(pre_elements):
        identifiers_value = None
        reaction_role_value = None
        for pre in pre_elements:
            pre_text = pre.text
            if pre_text.startswith('identifiers:'):
                match_val = re.search(r'"value":\s*"([^"]+)"', pre_text)
                if match_val:
                    identifiers_value = match_val.group(1)
            elif pre_text.startswith('reaction_role:'):
                match_role = re.match(r'reaction_role:\s*([^\s]+)', pre_text)
                if match_role:
                    reaction_role_value = match_role.group(1)
        return identifiers_value, reaction_role_value

    def extract_measurement_type_value(measurements_section):
        results = []
        try:
            value_cells = measurements_section.find_elements(By.CSS_SELECTOR, 'div.value')
            for i in range(0, len(value_cells), 5):
                if i + 2 < len(value_cells):
                    t = value_cells[i].text.strip()
                    v = value_cells[i + 2].text.strip()
                    if t:
                        results.append({"type": t, "value": v})
        except Exception as e:
            print(f"Error extracting (type, value) from measurements: {e}")
        return results

    try:
        # Inputs Section
        inputs_section = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div#inputs"))
        )
        driver.execute_script("arguments[0].scrollIntoView();", inputs_section)
        time.sleep(2)
        tabs = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#inputs .tabs .tab"))
        )
        print(f"Found {len(tabs)} tabs inside Inputs section\n")

        for tab in tabs:
            tab_name = tab.text.strip()
            print(f"Clicking tab → {tab_name}")
            driver.execute_script("arguments[0].click();", tab)
            time.sleep(2)

            input_buttons = inputs_section.find_elements(By.CSS_SELECTOR, "div.button")
            print(f"Found {len(input_buttons)} in tab {tab_name}.")
            for idx, btn in enumerate(input_buttons):
                try:
                    driver.execute_script("arguments[0].scrollIntoView();", btn)
                    try:
                        print(f"Clicking Inputs#{idx+1}")
                        driver.execute_script("arguments[0].click();", btn)
                    except Exception as click_error:
                        print(f"Cannot click Inputs raw button #{idx+1} in tab {tab_name}: {click_error}")
                        continue

                    time.sleep(1.5)
                    try:
                        data_section = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "div.data"))
                        )
                        pre_elements = data_section.find_elements(By.CSS_SELECTOR, "pre")
                        identifiers_value, reaction_role_value = extract_identifiers_and_role(pre_elements)
                        print(f"   Scraped identifiers value: {identifiers_value} | reaction_role: {reaction_role_value}")
                        inputs_scraped_data.append({
                            "tab": tab_name,
                            "raw_button_index": idx + 1,
                            "identifiers_value": identifiers_value,
                            "reaction_role": reaction_role_value
                        })
                    except Exception as dscrape:
                        print(f"Could not scrape data section for raw button #{idx+1} in tab {tab_name}: {dscrape}")
                    time.sleep(1.5)
                    try:
                        close_btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.close"))
                        )
                        driver.execute_script("arguments[0].click();", close_btn)
                        time.sleep(1)
                    except Exception as e:
                        print(f"Could not click Inputs close button #{idx+1}: {e}")
                except Exception as e:
                    print(f"Could not process Inputs raw button #{idx+1} in tab {tab_name}: {e}")

        print("\nFinished cycling through all input tabs.")

        # Outcomes Section
        outcomes_section = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div#outcomes"))
        )
        driver.execute_script("arguments[0].scrollIntoView();", outcomes_section)
        time.sleep(2)
        print("Stayed on Outcomes section for 2 seconds.\n")

        outcomes_views = outcomes_section.find_elements(By.CSS_SELECTOR, "div.outcomes-view")
        for outcome_idx, outcome_view in enumerate(outcomes_views):
            # PRODUCTS RAW BUTTONS
            try:
                products_compounds = outcome_view.find_elements(By.CSS_SELECTOR, ".compound-view")
                for prod_idx, compound_view in enumerate(products_compounds):
                    try:
                        prod_raw_btns = compound_view.find_elements(By.CSS_SELECTOR, ".raw .button")
                        for raw_btn_idx, prod_raw_btn in enumerate(prod_raw_btns):
                            driver.execute_script("arguments[0].scrollIntoView();", prod_raw_btn)
                            try:
                                driver.execute_script("arguments[0].click();", prod_raw_btn)
                            except Exception as click_error:
                                print(f"Cannot click Product raw button Outcome {outcome_idx+1} Product {prod_idx+1}: {click_error}")
                                continue

                            time.sleep(1.2)
                            try:
                                data_section = WebDriverWait(driver, 5).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.data"))
                                )
                                pre_elements = data_section.find_elements(By.CSS_SELECTOR, "pre")
                                identifiers_value, reaction_role_value = extract_identifiers_and_role(pre_elements)
                                print(f"   [Products] identifiers: {identifiers_value} | reaction_role: {reaction_role_value}")
                                products_scraped_data.append({
                                    "outcome_index": outcome_idx + 1,
                                    "product_index": prod_idx + 1,
                                    "identifiers_value": identifiers_value,
                                    "reaction_role": reaction_role_value
                                })
                            except Exception as dscrape:
                                print(f"Could not scrape product data for Outcome {outcome_idx+1} Product {prod_idx+1}: {dscrape}")
                            time.sleep(1)
                            try:
                                close_btn = WebDriverWait(driver, 5).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div.close"))
                                )
                                driver.execute_script("arguments[0].click();", close_btn)
                                time.sleep(0.3)
                            except Exception as e:
                                print(f"Could not close Products raw for Outcome {outcome_idx+1} Product {prod_idx+1}: {e}")
                    except Exception as e:
                        print(f"Error locating/clicking Product raw button: {e}")
            except Exception as e:
                print(f"Error with Products subsection: {e}")

            # MEASUREMENTS (table extraction)
            try:
                measurements_sections = outcome_view.find_elements(By.CSS_SELECTOR, ".measurements")
                for meas_idx, m_section in enumerate(measurements_sections):
                    pairs = extract_measurement_type_value(m_section)
                    print(f"Outcome# {outcome_idx+1}, Measurement block #{meas_idx+1}:")
                    for p in pairs:
                        print(f"   Type: {p['type']} | Value: {p['value']}")
                    print(f"Finished printing all pairs for Outcome# {outcome_idx+1} Block# {meas_idx+1}")
                    print(f"Total measurement pairs: {len(pairs)}\n")
                    measurements_scraped_data.append({
                        "outcome_index": outcome_idx + 1,
                        "measurement_index": meas_idx + 1,
                        "pairs": pairs
                    })
            except Exception as e:
                print(f"Error extracting (type, value) for Outcome {outcome_idx+1}: {e}")

    finally:
        pass

    # Extract ORD identifier from URL for the filename
    match = re.search(r'(ord-[\w\d]+)', ord_url)
    if match:
        csv_basename = f"{match.group(1)}.csv"
    else:
        csv_basename = "scraped_output.csv"

    # Save in SCRAPPED_DATA/DATASET_LINK/ord-xxxx.csv
    os.makedirs(dataset_dir, exist_ok=True)
    csv_path = os.path.join(dataset_dir, csv_basename)

    with open(csv_path, "w", newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        # Inputs header and data
        writer.writerow(["Section", "Tab", "Raw_Index", "Identifiers", "Reaction_Role"])
        for entry in inputs_scraped_data:
            writer.writerow([
                "Inputs",
                entry['tab'],
                entry['raw_button_index'],
                entry['identifiers_value'],
                entry['reaction_role']
            ])
        # Products header and data
        writer.writerow([])
        writer.writerow(["Section", "Outcome_Index", "Product_Index", "Identifiers", "Reaction_Role"])
        for entry in products_scraped_data:
            writer.writerow([
                "Products",
                entry['outcome_index'],
                entry['product_index'],
                entry['identifiers_value'],
                entry['reaction_role']
            ])
        # Measurements header and data
        writer.writerow([])
        writer.writerow(["Section", "Outcome_Index", "Measurement_Block_Index", "Type", "Value"])
        for entry in measurements_scraped_data:
            for p in entry["pairs"]:
                writer.writerow([
                    "Measurements",
                    entry['outcome_index'],
                    entry['measurement_index'],
                    p['type'],
                    p['value']
                ])
    print(f"\nCSV saved as: {csv_path}")

    print("\nScraped data from Inputs tabs:")
    for entry in inputs_scraped_data:
        print(f"Tab: {entry['tab']} | Raw#: {entry['raw_button_index']} | identifiers: {entry['identifiers_value']} | reaction_role: {entry['reaction_role']}")

    print("\nScraped data from Outcomes → Products raw:")
    for entry in products_scraped_data:
        print(f"Outcome# {entry['outcome_index']} Product# {entry['product_index']} | identifiers: {entry['identifiers_value']} | reaction_role: {entry['reaction_role']}")

    print("\nScraped data from Outcomes → Measurements:")
    for entry in measurements_scraped_data:
        print(f"Outcome# {entry['outcome_index']} Block# {entry['measurement_index']}:")
        for p in entry["pairs"]:
            print(f"   Type: {p['type']} | Value: {p['value']}")
        print(f"Finished printing all pairs for Outcome# {entry['outcome_index']} Block# {entry['measurement_index']}")
        print(f"Total measurement pairs: {len(entry['pairs'])}\n")

def click_all_view_full_details_on_dataset(driver, dataset_dir):
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)
    a_links = driver.find_elements(By.CSS_SELECTOR, 'div.col.full > a[href^="/id/ord-"]')
    print(f"Found {len(a_links)} full details links in this dataset page.")

    original_window = driver.current_window_handle

    for idx, a_el in enumerate(a_links):
        details_url = a_el.get_attribute('href')
        if not details_url:
            continue
        driver.execute_script('window.open(arguments[0], "_blank");', details_url)
        driver.switch_to.window(driver.window_handles[-1])
        print(f"Opened full details link in new tab: {details_url}")

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div#inputs, div#outcomes, h1, h2"))
            )
            print(f"Full details page loaded for button #{idx+1}")
        except TimeoutException:
            print(f"Timeout: full details page did not load for button #{idx+1}")

        scrape_ord_details(driver, details_url, dataset_dir)
        time.sleep(3)

        driver.close()
        driver.switch_to.window(original_window)
        print(f"Returned to dataset page after clicking full details #{idx+1} of {len(a_links)}.")

    print("Done clicking all View Full Details buttons in current dataset link!\n")

def set_dataset_pagination_to_100(driver):
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.select select#pagination"))
        )
        driver.execute_script("arguments[0].scrollIntoView();", dropdown)
        time.sleep(1)
        try:
            Select(dropdown).select_by_value("100")
            print("Changed dataset entries to 100 (via Select)")
        except:
            driver.execute_script("""
                var s=document.querySelector('div.select select#pagination');
                s.value='100';
                s.dispatchEvent(new Event('change',{bubbles:true}));
            """)
            print("Changed dataset entries to 100 (via JS fallback)")
        time.sleep(2)
    except Exception as e:
        print(f"Could not set dataset pagination dropdown: {e}")

def wait_for_dataset_to_load(driver):
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div#overview, .card-header, h1, h2"))
        )
        print("Dataset page loaded!")
        return True
    except Exception as e:
        print(f"Timeout waiting for dataset page to load: {e}")
        return False

def process_current_page(driver, scrapped_data_dir):
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)
    links = driver.find_elements(By.CSS_SELECTOR, 'a[href^="/dataset/ord_dataset-"]')
    dataset_urls = [link.get_attribute("href") for link in links]
    original_window = driver.current_window_handle

    for i, url in enumerate(dataset_urls):
        print(f"\n========= Working on dataset link {i+1}/{len(dataset_urls)}: {url} =========")
        driver.execute_script("window.open(arguments[0], '_blank');", url)
        driver.switch_to.window(driver.window_handles[-1])
        print(f"Opened dataset link in new tab: {url}")
        loaded = wait_for_dataset_to_load(driver)
        if loaded:
            set_dataset_pagination_to_100(driver)
            driver.execute_script("window.scrollTo(0, 0);")
            # Prepare path for this DATASET_LINK folder
            dataset_match = re.search(r'(ord_dataset-[\w\d]+)', url)
            if dataset_match:
                dataset_dir = os.path.join(scrapped_data_dir, dataset_match.group(1))
            else:
                dataset_dir = os.path.join(scrapped_data_dir, f"DATASET_{i+1}")
            os.makedirs(dataset_dir, exist_ok=True)
            click_all_view_full_details_on_dataset(driver, dataset_dir)
            print(f"Now moving to the next dataset link (if any)...\n")
            time.sleep(10)
        else:
            print("Could not verify dataset loaded (timeout or structure change).")
        driver.close()
        driver.switch_to.window(original_window)
        time.sleep(2)

if __name__ == "__main__":
    MAX_NEXT_PAGES = 5
    scrapped_data_dir = os.path.abspath("SCRAPPED_DATA")
    os.makedirs(scrapped_data_dir, exist_ok=True)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.maximize_window()
    driver.get("https://open-reaction-database.org/")
    print("Opened homepage and maximized window!")
    time.sleep(2)

    try:
        browse_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "nav a[href='/browse']"))
        )
        driver.execute_script("arguments[0].scrollIntoView();", browse_link)
        time.sleep(0.5)
        browse_link.click()
        print("Clicked Browse in navbar!")
    except TimeoutException:
        print("Could not find the Browse link in navbar!")
        driver.quit()
        exit(1)

    time.sleep(3)

    def set_browse_pagination_to_100(driver):
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            dropdown = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.select select#pagination"))
            )
            driver.execute_script("arguments[0].scrollIntoView();", dropdown)
            time.sleep(1)
            try:
                Select(dropdown).select_by_value("100")
                print("Changed browse entries to 100 (via Select)")
            except:
                driver.execute_script("""
                    var s=document.querySelector('div.select select#pagination');
                    s.value='100';
                    s.dispatchEvent(new Event('change',{bubbles:true}));
                """)
                print("Changed browse entries to 100 (via JS fallback)")
            time.sleep(3)
        except Exception as e:
            print(f"Could not set browse pagination dropdown: {e}")

    page = 1
    last_page = 1
    while page <= MAX_NEXT_PAGES:
        print(f"\nProcessing Page: {page}")
        set_browse_pagination_to_100(driver)
        process_current_page(driver, scrapped_data_dir)
        try:
            last_page_elem = driver.find_element(By.CSS_SELECTOR, ".paginav .button.word.selected")
            last_page = int(last_page_elem.text.strip())
            next_btn = driver.find_element(By.CSS_SELECTOR, "div.next.paginav span.word")
            if "disabled" in next_btn.get_attribute("class"):
                print("NEXT disabled -> Finished!")
                break
            driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
            next_btn.click()
            time.sleep(4)
            current_page_elem = driver.find_element(By.CSS_SELECTOR, ".paginav .button.word.selected")
            current_page = int(current_page_elem.text.strip())
            if current_page == 1 and page != 1:
                print("Went back to page 1 unexpectedly -> Exiting loop!")
                break
            page += 1
            print(f"NEXT clicked (page {page})")
        except Exception as e:
            print("No NEXT button or error -> Finished!", e)
            break


    driver.quit()
