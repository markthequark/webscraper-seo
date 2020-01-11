# gecko driver avilable from https://github.com/mozilla/geckodriver/releases/tag/v0.26.0

import time
from sys import platform
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def main() -> int:
    # webpages to scrape
    webpages = (
        ("novi.digital", "https://novi.digital/"),
        ("passion.digital", "https://passion.digital/"),
        ("londonseo.io", "https://www.londonseo.io/"),
        ("seo.co.uk", "https://www.seo.co.uk/"),
        ("seoagency-uk.co.uk", "https://www.seoagency-uk.co.uk/"),
        ("dubseo.co.uk", "https://www.dubseo.co.uk/"),
        ("seoworks.co.uk", "https://www.seoworks.co.uk/"),
        ("clickdo.co.uk", "https://www.clickdo.co.uk/"),
        ("seoguru.co.uk", "https://www.seoguru.co.uk/"),
        ("rankno1.co.uk", "https://www.rankno1.co.uk/"),
    )
    
    # determine which OS we're running on to select the correct driver
    path = "geckodriver/"
    if "linux" in platform:
        # linux
        path += "geckodriver_linux"
    elif "darwin" in platform:
        # OS X
        path += "geckodriver_mac"
    elif "win" in platform:
        # Windows...
        path += "geckodriver.exe"

    domains = [domain for domain, address in webpages]
    
    # launch webdriver to scrape data and open file to log data to
    with open("data.csv", "w+") as fp, webdriver.Firefox(executable_path=path) as driver:
        # get list of average search rankings for each domain
        ranks = mean_search_ranks(driver, domains)
        for domain, address in webpages:
            # the words scrapped from each webpage will be stored in it's own file
            filename = domain.split(".")[0] + ".txt"
            word_count = scrape(driver, address, filename)
            # the readability score is determined using the words scrapped
            score = read_score(driver, filename)
            # get the average search ranking for this webpage
            rank = ranks[domain]
            
            fp.write(domain + "," + word_count + "," + score + "," + rank + "\n")
    
    return 0 # ok


def mean_search_ranks(driver, domains: list) -> dict:
    """
    get the mean search rankings for each domain given
    returns a dictionary of the form {domain : mean search ranking}
    """
    # queries to search for
    queries = (
        "seo agency uk",
        "seo agency london",
        "seo company uk",
        "seo company london",
        "seo services uk",
        "seo services london",
    )

    ranks = []
    for query in queries:
        # perform a google search for this query
        driver.get("https://www.google.co.uk")
        search_box = driver.find_element_by_css_selector(".gLFyf")
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        # get the search rankings of all domains for this query, and add it to the list of rankings
        ranks.append(_get_ranks(driver, domains))
    
    # restructure the data to the form {domain : mean search ranking}
    return dict(zip(domains, (str(sum(rank[d] for rank in ranks)/len(ranks)) for d in domains)))
    
    
def _get_ranks(driver, domains: list) -> dict:
    rank = 1
    ranks = {}
    while len(ranks) < len(domains) and rank < 50:
        # wait for search rankings to load
        WebDriverWait(driver, 60).until(
          EC.presence_of_element_located((By.XPATH, r'//*[@id="pnnext"]'))
        )
        # get a list of all website cites
        cites = driver.find_elements_by_css_selector("cite")
        
        # if one of our domains is cited, log the search ranking position
        for cite in cites:
            for domain in domains:
                if domain in cite.text and domain not in ranks:
                    ranks[domain] = rank
            rank += 1
        
        # go to the next page of search rankings
        next_page = driver.find_element_by_css_selector("#pnnext")
        next_page.click()
    
    # return the search rankings dictionary with unfound domains ranked as the last ranking searched
    return {domain:ranks[domain] if domain in ranks else rank for domain in domains}


def read_score(driver, filename: str) -> str:
    """
    returns the readability score for the text stored in the file passed
    """
    time.sleep(1)
    # go to the readability score online tool
    driver.get("https://app.readable.com/text/")
    
    text_form = driver.find_element_by_css_selector("#text_to_score")
    
    # add the words scrapped to the text form
    with open(filename, "r") as fp:
        for line in fp:
            text_form.send_keys(line)
    
    # wait for the online tool to calculate the readability score
    WebDriverWait(driver, 20).until(
      EC.presence_of_element_located((By.XPATH, r'//*[@id="fave-flesch_reading_ease"]'))
    )
    
    # return the readability score
    return driver.find_element_by_css_selector("#fave-flesch_reading_ease").text


def scrape(driver, url: str, filename: str) -> str:
    """
    scrapes all text on given url and writes it to a file named after the url
    returns the word count on the page
    """
    driver.get(url)

    # all header and p DOMs
    doms = driver.find_elements_by_css_selector("h1, h2, h3, h4, h5, h6, p")

    # create a file to log scrapped words
    with open(filename, 'w+') as fp:
        for dom in doms:
            fp.write(dom.text + "\n\n")
    
    # return the sum of word counts in all DOMs
    return str(sum(len(dom.text.split()) for dom in doms))
  
  
if __name__ == "__main__":
    exit(main())
