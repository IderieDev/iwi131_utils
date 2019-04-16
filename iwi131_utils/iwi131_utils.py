from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import logging

logger = logging.getLogger('hackerrank_scraper.scraper')

# The element names of the leaderboard fields
HACKERRANK_LEADERBOARD_LIST_CLASS_NAME = 'leaderboard-list-view'


# The elements corresponding to individual fields in the leaderboard
HACKERRANK_LEADERBOARD_ROW_CLASS_NAME = 'row '


class Competitor:
    def __init__(self, position, username, completedCount):
        self.position = position
        self.username = username
        self.completedCount = completedCount

    def __str__(self):
        return '{0:<5} {1:<25} {2:<5}'.format(self.position, self.username,
                                              self.completedCount)

    def __repr__(self):
        return self.__str__()


class Scraper:
    def __init__(self, hackerrank_leaderboard_url):
        
        #self.driver = webdriver.PhantomJS('/opt/conda/bin/phantomjs')
        self.driver = webdriver.ChromeOptions('/opt/conda/bin/chromedriver')
        self.hackerrank_leaderboard_url = hackerrank_leaderboard_url
        self.loggedin = False

    def get_competitors_from_leaders_table(self, leadersTableElement):
        userListBoxes = leadersTableElement.find_elements_by_class_name(
            HACKERRANK_LEADERBOARD_LIST_CLASS_NAME
        )

        for listbox in userListBoxes:
            row = listbox.find_element_by_class_name(HACKERRANK_LEADERBOARD_ROW_CLASS_NAME)
            position, username, problems_completed, hour = row.text.split('\n')
     
            problems_completed = (
                0 if problems_completed == '-' else round(float(problems_completed))
            )

            competitor = Competitor(position, username, problems_completed)
            
            logger.debug('Loaded competitor {}'.format(competitor))
            yield competitor

    def get_competitors_from_leaderboard(self, leaderboardURL):
        logger.info('Loading leaderboard from url {}'.format(leaderboardURL))
        self.driver.implicitly_wait(30)
        pageSource = ""
        pageNumber = 1
        while "Sorry, we require a few more submissions" not in pageSource:
            logger.debug('Loading page {}'.format(pageNumber))
            self.driver.get('{}/{}'.format(leaderboardURL, pageNumber))
            pageSource = self.driver.page_source

            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, HACKERRANK_LEADERBOARD_LIST_CLASS_NAME)
                    )
                )
            except TimeoutException:
                logger.info('Leaderboard details not found -- Done loading')
                return

            logger.debug('Leaderboard details loaded -- loading competitors')
            leaderboardElement = self.driver.find_element_by_id("leaders")
            pageSource = self.driver.page_source
            for competitor in self.get_competitors_from_leaders_table(leaderboardElement):
                yield competitor

            logger.info('Page {} loaded.'.format(pageNumber))
            pageNumber += 1

    def _scrape(self, leaderboard_url):
        for competitor in self.get_competitors_from_leaderboard(leaderboard_url):
            yield competitor

    def scrape(self):
        for competitor in self._scrape(self.hackerrank_leaderboard_url):
            yield competitor
