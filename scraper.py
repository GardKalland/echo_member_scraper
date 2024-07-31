from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Set which echo HS year to scrape
echo_year = ""  

urls = {
    "hovedstyre": f"https://echo.uib.no/for-studenter/gruppe/{echo_year}" if echo_year else "https://echo.uib.no/for-studenter/grupper/hovedstyre",
    "interessegrupper": "https://echo.uib.no/for-studenter/grupper/interessegrupper",
    "undergrupper": "https://echo.uib.no/for-studenter/grupper/undergrupper",
    "programmerbar": "https://echo.uib.no/for-studenter/gruppe/programmerbar"
}
chrome_options = Options()
chrome_options.add_argument("--headless")  
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

data_dict = {}

def scrape_group_members(group_url):
    try:
        driver.get(group_url)
        time.sleep(2)  
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        

        members_section = soup.find('h2', id='medlemmer')
        if members_section:
            logger.info(f"Scraping group from {group_url}")

            members_divs = members_section.find_next_sibling('div').find_all('div')
            if members_divs:
                logger.info(f"Found {len(members_divs)} members in group")

                for member_div in members_divs:

                    name_tag = member_div.find('p', class_='text-lg font-medium')
                    if name_tag:
                        name = name_tag.get_text(strip=True)
                        
                        title_tag = member_div.find('p', class_='text-sm')
                        if title_tag:
                            title = title_tag.get_text(strip=True)  

                        if name:  
                            group_name = group_url.split('/')[-1]
                            if name in data_dict:
                                data_dict[name]['groups'].append(group_name)
                                data_dict[name]['count'] = len(data_dict[name]['groups'])
                            else:
                                data_dict[name] = {'groups': [group_name], 'count': 1}
                            logger.info(f"Added member: {name} to group: {group_name}")
            else:
                logger.warning("No member divs found under the 'medlemmer' section.")
        else:
            logger.warning("No 'medlemmer' section found in the group page.")
    except Exception as e:
        logger.error(f"Error loading {group_url}: {e}")

def get_group_urls(main_url):
    try:
        driver.get(main_url)
        time.sleep(2)  
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        
        group_links = soup.find_all('a', href=True)
        group_urls = []
        
        for link in group_links:
            href = link['href']
            if '/for-studenter/gruppe/' in href:
                group_urls.append(f"https://echo.uib.no{href}")
        
        return group_urls
    except Exception as e:
        logger.error(f"Error loading {main_url}: {e}")
        return []


if echo_year == "":
    
    for group in ["hovedstyre","interessegrupper", "undergrupper"]:
        logger.info(f"Scraping main page: {urls[group]}")
        group_urls = get_group_urls(urls[group])
        logger.info(f"Found {len(group_urls)} group URLs in {urls[group]}")
    
        for group_url in group_urls:
            scrape_group_members(group_url)
    
    logger.info(f"Scraping main page: {urls['programmerbar']}")
    scrape_group_members(urls['programmerbar'])

    
else:

    for group in ["hovedstyre", "programmerbar"]:
        logger.info(f"Scraping main page: {urls[group]}")
        scrape_group_members(urls[group])


    for group in ["interessegrupper", "undergrupper"]:
        logger.info(f"Scraping main page: {urls[group]}")
        group_urls = get_group_urls(urls[group])
        logger.info(f"Found {len(group_urls)} group URLs in {urls[group]}")
    
        for group_url in group_urls:
            scrape_group_members(group_url)

driver.quit()

logger.info("Collected data:")
for name, details in data_dict.items():
    logger.info(f"{name}: {details}")

with open('members_2024_2025.json', 'w') as json_file:
    json.dump(data_dict, json_file, indent=4)
    logger.info("Data saved to medlemmer_verv.json")
