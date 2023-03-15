from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import yaml

import time

with open('Resources/c4arena.yaml') as f:
    c4arena = yaml.safe_load(f)

driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

driver.get(c4arena[':c4arena_url'])
driver.maximize_window()

time.sleep(2)

frame = driver.find_element(By.XPATH, c4arena[':game_iframe'])
driver.switch_to.frame(frame)

play_ai_button = driver.find_element(By.XPATH, c4arena[':play_ai_button'])
play_ai_button.click()

time.sleep(1)

easy_button = driver.find_element(By.XPATH, c4arena[':difficulty_easy_button'])
easy_button.click()

time.sleep(2)
driver.get_screenshot_as_file('Resources/game_screenshot.png')

time.sleep(4)