from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
import os
import re

# Create driver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# Get script folder to save CSV in the same path
script_folder = os.path.dirname(os.path.abspath(__file__))

try:
    # Navigate to the archive page
    url = "https://kmt.vander-lingen.nl/archive"
    driver.get(url)
    time.sleep(3)

    # Get all list items containing reaction data
    list_items = driver.find_elements(By.CSS_SELECTOR, "li")
    
    reaction_data_list = []
    for item in list_items:
        try:
            # Get the reaction data link
            reaction_link = item.find_element(By.LINK_TEXT, "reaction data")
            reaction_url = reaction_link.get_attribute('href')
            
            # Get the text of the li element and extract the name (before "reaction data")
            li_text = item.text
            # Remove "reaction data | DOI" part to get just the name
            reaction_name = li_text.split("reaction data")[0].strip()
            
            reaction_data_list.append({
                "name": reaction_name,
                "url": reaction_url
            })
        except:
            continue
    
    print(f"Found {len(reaction_data_list)} reaction data entries")

    for i, reaction_entry in enumerate(reaction_data_list, 1):
        reaction_name = reaction_entry["name"]
        reaction_url = reaction_entry["url"]
        
        # Sanitize filename (remove invalid characters)
        safe_filename = re.sub(r'[<>:"/\\|?*]', '_', reaction_name)
        csv_file = os.path.join(script_folder, f"{safe_filename}.csv")
        
        print(f"\n[{i}/{len(reaction_data_list)}] Processing: {reaction_name}")
        print(f"  URL: {reaction_url}")
        
        # Initialize CSV with header for this reaction
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Type", "SMILES"])
            writer.writeheader()
        
        driver.get(reaction_url)
        time.sleep(2)

        reaction_page_data = []  # To store data for this reaction data page

        while True:
            # Get the number of results
            try:
                results_button = driver.find_element(By.CSS_SELECTOR, "button.btn.btn-info")
                total_results = int(results_button.text.split()[-1])
            except:
                total_results = 0

            print(f"  Results: {total_results}")

            if total_results == 0:
                print("  No results found. Moving to next reaction data.")
                break

            # Find all Smiles buttons
            smiles_buttons = driver.find_elements(By.CSS_SELECTOR,
                'button.btn.btn-outline-success.btn-sm[data-toggle="modal"][data-reaction-smiles]')

            for j in range(min(total_results, len(smiles_buttons))):
                try:
                    smiles_buttons = driver.find_elements(By.CSS_SELECTOR,
                        'button.btn.btn-outline-success.btn-sm[data-toggle="modal"][data-reaction-smiles]')

                    # Click Smiles button
                    try:
                        print(f"    Clicking Smiles button {j+1}/{total_results}...")
                        smiles_buttons[j].click()
                        time.sleep(2)

                        # Scrape data inside modal
                        try:
                            modal_content = driver.find_element(By.CSS_SELECTOR, '.modal-body')
                            smile_data = modal_content.text.strip()

                            # Split into Reactant, Solvent/Reagent, Product
                            parts = smile_data.split('>')
                            reactant = parts[0].strip() if len(parts) > 0 else ''
                            solvent = parts[1].strip() if len(parts) > 1 else ''
                            product = parts[2].strip() if len(parts) > 2 else ''

                            # Store each component separately
                            if reactant:
                                reaction_page_data.append({
                                    "type": "Reactant",
                                    "smiles": reactant
                                })
                            if solvent:
                                reaction_page_data.append({
                                    "type": "Solvent/Reagent",
                                    "smiles": solvent
                                })
                            if product:
                                reaction_page_data.append({
                                    "type": "Product",
                                    "smiles": product
                                })

                            print(f"      Scraped SMILES:")
                            print(f"        Reactant: {reactant[:60]}...")
                            print(f"        Solvent/Reagent: {solvent[:60]}...")
                            print(f"        Product: {product[:60]}...")

                        except Exception as e:
                            print(f"      Error scraping modal: {e}")

                        # Close modal
                        try:
                            close_button = driver.find_element(By.CSS_SELECTOR, '.modal .close')
                            close_button.click()
                        except:
                            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)

                        time.sleep(1)

                    except Exception as e:
                        print(f"    Error clicking Smiles button {j+1}: {e}")

                except Exception as e:
                    print(f"    Error processing button {j+1}: {e}")

            # Click Next button to go to next page
            try:
                next_button = driver.find_element(By.LINK_TEXT, "Next")
                print("  Clicking Next button...")
                next_button.click()
                time.sleep(2)
            except:
                print("  No Next button found. Finished this reaction data page.")
                break

        # Save reaction page data to CSV
        with open(csv_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Type", "SMILES"])
            for item in reaction_page_data:
                writer.writerow({
                    "Type": item["type"],
                    "SMILES": item["smiles"]
                })

        print(f"  ✅ Saved {len(reaction_page_data)} reactions to: {safe_filename}.csv")

finally:
    driver.quit()
    print(f"\n✓ Completed scraping all reaction data. CSV files saved in: {script_folder}")