import csv
import time
import logging
import yaml
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChService
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException

with open('config/main_config.yml') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

logging.basicConfig(
    filename=config['log_file'],
    filemode="w",
    format='%(asctime)s :: %(levelname)s : %(name)s : %(message)s : line: %(lineno)d',
    level=logging.getLevelName(config['log_level'])
)

logging.info("Program execution started")

driver: WebDriver
with webdriver.Chrome(
    service=ChService('drivers/chromedriver_v109.exe'),
    options=webdriver.ChromeOptions()
) as driver:
    driver.implicitly_wait(2)
    driver.get(config['url_to_scrape'])
    logging.info(f"Scraped URL: {config['url_to_scrape']}")
    logging.info(f"Title: {driver.title}")

    # Press "Accept" button for eu cookie consent
    driver.find_element(By.CLASS_NAME, "cc-btn.cc-allow").click()
    logging.info("Pressed 'Accept' button for eu cookie consent")

    # NAVIGATION into depth
    # Press "All Books" button
    driver.find_element(By.CSS_SELECTOR, "div.col-auto.menu-item.visos-knygos.mob-view").click()
    logging.info("Pressed 'All Books' button")

    # Hover on "Dalykinė literatūra"
    automationTools = driver.find_element(By.LINK_TEXT, "Dalykinė literatūra")
    ActionChains(driver).move_to_element(automationTools).perform()
    logging.info("Hovered over 'Dalykinė literatūra'")

    # Press "Kompiuterija ir informacinės technologijos" button
    driver.find_element(By.LINK_TEXT, "Kompiuterija ir informacinės technologijos").click()
    logging.info("Pressed 'Kompiuterija ir informacinės technologijos' button")
    time.sleep(2)

    urls, page_numbers = [], []
    book_authors, book_titles, book_prices, book_items = [], [], [], []

    # Check if selector exists for author and price
    def check_element_by_selector(selector):
        try:
            driver.find_element(By.CSS_SELECTOR, selector)
        except NoSuchElementException:
            # logging.warning("Element with such selector is not found")
            logging.warning(f"No element found with selector '{selector}'")
            return False
        return True

    # NAVIGATION into  depth and breadth
    # Number of last_page in "Kompiuterija ir informacinės technologijos"
    all_pages = driver.find_elements(By.XPATH, "//div[2]/div/div[5]/div/ul//a")
    last_page_number = int((all_pages[-2]).text)

    # Navigation through pages to get the all_books urls
    for k in range(last_page_number):
        all_books = driver.find_elements(By.CSS_SELECTOR, "a.product-link")
        for book in all_books:
            urls.append(book.get_attribute("href"))

        # Go to text page
        next_page_button = driver.find_element(By.CLASS_NAME, "forward")
        next_page_button.click()

    # Visit saved pages urls and get titles, authors, prices of the objects (check if author and price exists)
    for url in urls:
        driver.get(url)
        # time.sleep(1)
        one_book_authors: list[str] = []

        title = driver.find_element(By.CSS_SELECTOR, "h1 > span:nth-child(1)")
        book_titles.append(title.text)

        if check_element_by_selector("div.d-inline-block") > 0:
            authors = driver.find_elements(By.CSS_SELECTOR, "div.d-inline-block")
            for author in authors:
                one_book_authors.append(author.text)
        else:
            one_book_authors.append("N/A")
        book_authors.append(one_book_authors)

        if check_element_by_selector("span.new-price.single-price") > 0:
            price = driver.find_element(By.CSS_SELECTOR, "span.new-price.single-price")
            book_prices.append(price.text)
        elif check_element_by_selector("span.price.single-price") > 0:
            price = driver.find_element(By.CSS_SELECTOR, "span.price.single-price")
            book_prices.append(price.text)
        elif check_element_by_selector("ul.prices.mb-4 > li > span") > 0:
            price = driver.find_element(By.CSS_SELECTOR, "ul.prices.mb-4 > li > span")
            book_prices.append(price.text)
        else:
            book_prices.append("N/A €")

    author_strings = [" ".join(author_list) for author_list in book_authors]

    with open("report/v1_books.csv", "w", encoding='UTF-8', newline="") as f:
        writer = csv.writer(f, delimiter=";")
        header = ["Title", "Author", "Price"]
        writer.writerow(header)
        for title, author, price in zip(book_titles, author_strings, book_prices):
            writer.writerow([title, author, price])

    driver.close()
logging.info("Program execution ended")
