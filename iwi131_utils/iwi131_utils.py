from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import xlrd

import pandas as pd 

import logging

from difflib import SequenceMatcher

logging.basicConfig(level=getattr(logging, 'INFO'))
logger = logging.getLogger('iwi131_utils')

# The element names of the leaderboard fields
HACKERRANK_LEADERBOARD_LIST_CLASS_NAME = 'leaderboard-list-view'


# The elements corresponding to individual fields in the leaderboard
HACKERRANK_LEADERBOARD_ROW_CLASS_NAME = 'row '


class Sansano_Hackerrank:
    def __init__(self, position, username, nota):
        self.position = position
        self.username = username
        self.nota = nota

    def __str__(self):
        return '{0:<5} {1:<25} {2:<5}'.format(self.position, self.username,
                                              self.nota)

    def __repr__(self):
        return self.__str__()


class Scraper:
    def __init__(self, hackerrank_leaderboard_url):
        
        self.driver = webdriver.PhantomJS('/Users/dylan/anaconda3/bin/phantomjs')
        #self.driver = webdriver.Chrome(executable_path='/opt/conda/bin/chromedriver')
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

            competitor = Sansano_Hackerrank(position, username, problems_completed)
            
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

    def scrape(self):
        for competitor in self.get_competitors_from_leaderboard(self.hackerrank_leaderboard_url):
            yield competitor

            
def estudiantes_x_paralelo_siga(dest_filename):
    xl_workbook = xlrd.open_workbook(dest_filename)
    sheet_names = xl_workbook.sheet_names()
    xl_sheet = xl_workbook.sheet_by_name(sheet_names[0])
    num_cols = xl_sheet.ncols
    matrix = [[xl_sheet.cell(row_idx, 1).value,xl_sheet.cell(row_idx, 10).value.split('@')[0].replace(".", "_")] for row_idx in range(9, xl_sheet.nrows)]
    return pd.DataFrame(matrix, columns = ['rol', 'username']) 

def identificador_nn(df_paralelo, df_alumnos_nn,ratio=0.85):
    identificados=[]
    residuos=[]
    for _, user_nn in df_paralelo.iterrows():
        for _, user_all in df_alumnos_nn.iterrows():
            if SequenceMatcher(None, str(user_nn['rol']), str(user_all['rol'])).ratio() >ratio:
                identificados.append([user_nn['username'],user_all['nota'],user_nn['rol']])
                residuos.append(user_all['username'])

    return (pd.DataFrame(identificados, columns = ['username', 'nota','rol']),residuos)