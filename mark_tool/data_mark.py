from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.ui import Select

import time
import re
from mark_tool import config_util

import time

import traceback

failed_set = set()


class MarkTool(object):
    def __init__(self):
        self._read_config_info()
        # self._init_wx_chat()
        self._init_web_driver()
        self.config_load()

    def _read_config_info(self):
        pass

    def _init_web_driver(self):
        # 初始化webDriver，配置其不显示图片
        chrome_options = webdriver.ChromeOptions()
        prefs = {"profile.managed_default_content_settings.images": 2}
        chrome_options.add_experimental_option("prefs", prefs)
        # 使用edge，bug更少
        # self.driver = webdriver.Chrome(chrome_options=chrome_options, executable_path='chromedriver.exe')
        self.driver = webdriver.Edge(executable_path='MicrosoftWebDriver.exe')

    def login_page(self):
        try:
            driver = self.driver
            driver.get('http://typz.int-yt.com/')
            usernameInput = driver.find_element_by_id('login_id')
            usernameInput.clear()
            usernameInput.send_keys(self.jcu.get('username'))
            passwordInput = driver.find_element_by_id('password')
            passwordInput.clear()
            passwordInput.send_keys(self.jcu.get('password'))

            buttonOfLogin = driver.find_element_by_id('submit')
            buttonOfLogin.click()
        except Exception as e:
            print('页面出现未知错误，请重试!错误信息：%s' % str(e))

    def refreshPage(self):
        oldUrl = self.driver.current_url
        try:
            self.driver.refresh()
        except Exception as e:
            pass
        if oldUrl != self.driver.current_url:
            pass

    def quit(self):
        self.driver.quit()

    def config_load(self, config_file='config.json'):
        self.jcu = config_util.JsonConfigUtil(config_file)
        self.start_position = self.jcu.get('start_position')

    def get_passage_selector(self, tag_name):
        return self.get_tag_value("passage_title_dict", tag_name)

    def get_page_list_selector(self, tag_name):
        return self.get_tag_value("page_list_dict", tag_name)

    def get_config_string(self, tag_name):
        return self.get_tag_value("config_string_dict", tag_name)

    def get_should_js_on(self, tag_name):
        return self.get_tag_value("should_js_on_dict", tag_name)

    def get_tag_value(self, dict_name, tag_name):
        tag_dict = self.jcu.get(dict_name)
        selector = None
        for key in tag_dict:
            full_p = '.*' + key + '.*'
            if re.match(full_p, tag_name) is not None:
                selector = tag_dict[key]
        return selector

    def mark(self):
        driver = self.driver
        # id = 'task_lists'
        not_finish = True
        p = self.start_position
        while not_finish:
            time.sleep(5)
            driver.get('http://typz.int-yt.com/configIndex.html')
            WebDriverWait(driver, 8).until(EC.frame_to_be_available_and_switch_to_it((By.ID, 'task_lists')))
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'tr[datagrid-row-index="0"]')))

            task_name = driver.find_element_by_id('task_name')
            task_name.clear()
            # task_name.send_keys('中国新闻网-广西-房地产')

            status_tag = driver.find_element_by_xpath('//*[@id="tb"]/div/span[11]/span/span/span')
            status_tag.click()
            # 寻找进行中
            driver.find_element_by_xpath('/html/body/div[6]/div/div[2]').click()
            time.sleep(1)
            driver.find_element_by_link_text('搜索').click()
            time.sleep(5)

            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'tr[datagrid-row-index="0"]')))
            tags = driver.find_elements_by_css_selector('td[field="flag"]')
            tags_id = driver.find_elements_by_css_selector('td[field="boardId"]')
            tags_name = driver.find_elements_by_css_selector('td[field="name"]')

            if len(tags) < p + 1:
                not_finish = False
                continue

            tag = tags[p]
            id = tags_id[p].text
            name = tags_name[p].text
            try:
                p += 1

                passage_selector = self.get_passage_selector(name)
                page_list_selector = self.get_page_list_selector(name)

                js_on = self.get_should_js_on(name)

                actions = ActionChains(driver)
                actions.double_click(tag)
                actions.perform()

                driver.switch_to.default_content()

                WebDriverWait(driver, 8).until(
                    EC.frame_to_be_available_and_switch_to_it((By.ID, 'task_detail')))

                # 检查js是否需要加载
                if js_on == 1:
                    print('id:%s    name:%s--->js reload' % (id, name))
                    js_select = Select(driver.find_element_by_css_selector('#js_enable'))
                    time.sleep(1)
                    js_select.select_by_value('1')
                    time.sleep(1)
                    driver.execute_script('reCatch();')
                    time.sleep(3)
                time.sleep(10)

                # taskDetail_main进入列表页
                WebDriverWait(driver, 8).until(
                    EC.frame_to_be_available_and_switch_to_it((By.ID, 'taskDetail_main')))

                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, passage_selector)))

                driver.implicitly_wait(20)

                print('===>', passage_selector)
                passage_list = driver.find_element_by_css_selector(passage_selector)
                tag_list = passage_list.find_elements_by_tag_name('a')

                if len(tag_list) == 0:
                    raise Exception('没有找到列表数据')

                url = tag_list[0].get_attribute('href')

                print('id:%s->link size:%d    name:%s' % (id, len(tag_list), name))
                # mod_num = len(tag_list) // 5
                mod_index = 0
                for tag in tag_list:
                    # if mod_index % mod_num == 0:
                    if mod_index < 6:
                        tag.click()
                        time.sleep(0.8)
                    mod_index += 1
                driver.switch_to.parent_frame()
                driver.find_element_by_id('doc_url_regexp_button').click()
                time.sleep(0.5)

                # 后续要使用所以先拿出来
                page_check = False
                if self.get_page_list_selector(name):
                    # taskDetail_main进入列表页
                    WebDriverWait(driver, 8).until(
                        EC.frame_to_be_available_and_switch_to_it((By.ID, 'taskDetail_main')))
                    # 找到翻页list位置

                    page_a_list = driver.find_element_by_css_selector(page_list_selector).find_elements_by_tag_name('a')
                    print('page_id:%s->%d' % (id, len(page_a_list)))
                    if len(page_a_list) > 0:
                        page_check = True
                        for tag_a in page_a_list:
                            tag_a.click()
                            time.sleep(0.2)

                    driver.switch_to.parent_frame()
                    if page_check:
                        driver.find_element_by_id('page_down_regexp_button').click()
                        time.sleep(0.5)

                time.sleep(1)

                # 勾选
                if page_check:
                    check_page = driver.find_element_by_id('page_down_valid')
                    if not check_page.is_selected():
                        check_page.click()
                        time.sleep(1)
                check_doc = driver.find_element_by_id('doc_url_valid')
                if not check_doc.is_selected():
                    check_doc.click()
                    time.sleep(1)

                driver.find_element_by_id('verifyButton').click()

                time.sleep(1)

                WebDriverWait(driver, 8).until(
                    EC.text_to_be_present_in_element((By.ID, 'verifyButton'), '下一步'))

                driver.find_element_by_id('verifyButton').click()

                driver.switch_to.default_content()

                WebDriverWait(driver, 8).until(
                    EC.frame_to_be_available_and_switch_to_it((By.ID, 'task_constor')))

                # 准备填写内容
                WebDriverWait(driver, 8).until(
                    EC.frame_to_be_available_and_switch_to_it((By.ID, 'constor_main')))

                WebDriverWait(driver, 8).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, passage_selector)))
                # url = driver.find_element_by_css_selector(passage_selector).get_attribute('href')

                # 返回上一层
                driver.switch_to.parent_frame()

                driver.find_element_by_id('jumpUrl').send_keys(url)
                driver.find_element_by_id('jumpButton').click()

                WebDriverWait(driver, 8).until(
                    EC.frame_to_be_available_and_switch_to_it((By.ID, 'constor_main')))

                driver.switch_to.parent_frame()

                for s in self.get_config_string(name):
                    driver.find_element_by_id('configContent').send_keys('\r\n' + s)
                time.sleep(3)
                driver.execute_script('extractContent();')
                time.sleep(3)
                driver.execute_script('parent.validAndComplete();')
                time.sleep(3)
                driver.switch_to.default_content()
                time.sleep(5)
                print('complete id:%s    name:%s' % (id, name))

            except Exception:
                print('====>traceback begin<===')
                print(traceback.format_exc())
                print('====>traceback end<===')
                failed_set.add(id)
                print('-------->id:%s   name:%s' % (id, name))

    def print_line(self, lines=1):
        for i in range(lines):
            print('-' * 50)


if __name__ == '__main__':
    mt = MarkTool()
    mt.login_page()
    mt.mark()
