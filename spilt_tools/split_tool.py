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

from bs4 import BeautifulSoup
from bs4 import Tag
import traceback
import re

import pandas as pd

import time
import re
from mark_tool import config_util
import os

import time

failed_set = set()


class SplitTool(object):
    def __init__(self):
        self._read_config_info()
        self._init_chrome()
        self.config_load()

    def _read_config_info(self):
        pass

    def _init_chrome(self):
        # 初始化webDriver，配置其不显示图片
        chrome_options = webdriver.ChromeOptions()
        # prefs = {"profile.managed_default_content_settings.images": 2}
        prefs = {}
        chrome_options.add_experimental_option("prefs", prefs)
        # 使用edge，bug更少
        self.driver = webdriver.Chrome(chrome_options=chrome_options, executable_path='../driver/chromedriver.exe')
        # self.driver = webdriver.Edge(executable_path='../driver/chromedriver.exe')

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

    def get_tag_value(self, dict_name, tag_name):
        tag_dict = self.jcu.get(dict_name)
        selector = tag_dict['default']
        for key in tag_dict:
            full_p = '.*' + key + '.*'
            if re.match(full_p, tag_name) is not None:
                selector = tag_dict[key]
        return selector

    def find_a(self, html, main_url, main_name, nav_data):
        top_k = 9
        bs = BeautifulSoup(html, 'html.parser')
        queue = []
        if re.match('\d\w+', nav_data[0]):
            top_k = int(nav_data[0][0])
            nav_data[0] = nav_data[0][1:]
        if len(nav_data) == 1:
            while 'nth-child' in nav_data[0]:
                bf = nav_data[0].split(':nth-child', 1)
                f, t = bf[0].rsplit(' > ', 1)
                type_index = 0
                aim_index = int(bf[1][int(bf[1].find('(')) + 1: int(bf[1].find(')'))])
                index = 1
                for i, c in enumerate(bs.select(f)[0].children):
                    if isinstance(c, Tag):
                        if c.name == t:
                            type_index += 1
                        if aim_index == index:
                            print(c.name)
                            break
                        index += 1
                nav_data[0] = bf[0] + ':nth-of-type(' + str(type_index) + bf[1][bf[1].find(')'):]
            print('css:', nav_data[0])
            bl = bs.select(nav_data[0])
            if not bl:
                print(f'-----did not find aim element:{nav_data[0]}-----')
            else:
                queue.append((bs.select(nav_data[0])[0], [main_name]))
        else:
            roots = bs.find_all(attrs={nav_data[0]: nav_data[1]})
            if roots is None:
                print('-----did not find aim element-----')
            else:
                for root in roots:
                    queue.append((root, [main_name]))
        r = []
        a_level_list = []
        while queue:
            e, l = queue.pop(0)

            if isinstance(e, Tag):
                children = e.children
                name = ''
                if len(nav_data) == 3 and nav_data[2] in e.get_attribute_list(nav_data[0]):
                    print('class {} ignore'.format(nav_data[2]))
                    continue
                for c in children:
                    if not isinstance(c, Tag):
                        continue
                    if c.name == 'a':
                        if not c.has_attr('href'):
                            continue
                        name = c.getText()
                        pre_name = ''
                        for s in l:
                            if s:
                                pre_name += (s + '-')
                        if len(l) not in a_level_list:
                            a_level_list.append(len(l))
                        r.append([c['href'], pre_name + name, len(l)])
                    else:
                        t = list(l)
                        t.append(name)
                        queue.append((c, t))
        rr = []
        top_k_a_level = a_level_list[:top_k]
        for l in r:
            if l[2] in top_k_a_level:
                rr.append(l)
            if l[0].startswith('//'):
                l[0] = 'http:' + l[0]
            elif l[0].startswith('/'):
                l[0] = main_url.split('//')[0] + '//' + main_url.split('//')[1].split('/')[0] + l[0]
            elif not l[0].startswith('http'):
                l[0] = main_url + '/' + l[0]
        self.__contain_remove(rr)
        return rr

    def __contain_remove(self, aim):
        r_list = []
        for i in range(len(aim)):
            for j in range(len(aim)):
                if i != j:
                    if aim[j][0] in aim[i][0] and aim[j] not in r_list:
                        r_list.append(aim[j])
        for i in r_list:
            aim.remove(i)

    def open_url(self, url, position=0, title=None):
        self.driver.get(url)
        # self.driver.set_page_load_timeout(8)
        # self.driver.set_script_timeout(8)
        # self.driver.switch_to.frame('main')
        html = self.driver.page_source
        main_page_url = self.driver.current_url
        if not title:
            title = self.driver.title.split(',')[0]
            split_list = [',', ' ', '-', '_', '|', '——']
            for sc in split_list:
                ts = title.split(sc)
                if len(ts) > 0:
                    if position > 0:
                        title = ts[position - 1]
                    else:
                        title = ts[0]
                        for s in ts:
                            if len(s) > len(title):
                                title = s
        print('title is {}'.format(title))
        if DEBUG:
            nav_data = NAV_DATA
        else:
            print('请输入nav位置:\r')
            nav_data = input()
            if ' > ' not in nav_data:
                nav_data = nav_data.split(' ')
            else:
                nav_data = [nav_data]
                # nav_data = [nav_data.replace('nth-child', 'nth-of-type')]
        print(nav_data)
        if len(nav_data) == 1:
            self.aim_value = nav_data[0]
        else:
            self.aim_value = nav_data[1]

        return self.find_a(html, url, title, nav_data), title, main_page_url

    def write2file(self, data, title, main_page_url, u):
        result = []
        for d in data:
            r = [title, main_page_url, u.split('/')[0], 1, d[1], d[0], '', '', '', '', '', '', '']
            result.append(r)
        df = pd.DataFrame(result)
        r_value = [';', ':', '-', '#', '/', '\\', ' > ', '(', ')']
        for r in r_value:
            title = title.replace(r, '')
            self.aim_value = self.aim_value.replace(r, '')

        if not os.path.exists('split_result'):
            os.mkdir('split_result')
        df.to_csv('split_result/' + title + self.aim_value + '.csv', index=None, header=None)

    def html_split(self, main_url, u, position, complex):
        self.main_url = main_url
        data, title, main_page_url = self.open_url(main_url, position)
        if complex:
            dl = []
            for d in data:
                if u in d[0]:
                    try:
                        dd, _, _ = self.open_url(d[0], position, d[1])
                        print('{} complete! total size:{}'.format(d[1], len(dd)))
                        dl.extend(dd)
                    except Exception as e:
                        print(e)
            data = dl
        self.write2file(data, title, main_page_url, u)
        print('{} complete! total size:{}'.format(title, len(data)))

    def print_line(self, lines=1):
        for i in range(lines):
            print('-' * 50)


def combine_result_and_remove_data():
    # import os
    # fs = os.listdir('split_result')
    # df = pd.DataFrame()
    # for f in fs:
    #     print(f)
    #     df_t = pd.read_csv('split_result/' + f, engine='python', index_col=False, header=None, encoding='utf-8')
    #     df = pd.concat([df, df_t], axis=0)
    #     print(df.shape)
    # print(df.head(10))
    # df.to_csv('result_combine.csv', index=None, header=None)
    df = pd.read_csv('result_combine.csv', index_col=False, header=None)
    remove_list = ['公开', '文件', '政策法规', '公示', '首页', '关于', '简介', '联系', '互动', '组织机构', '概况', '国务院', '下载', '帮助', '报名']

    for r in remove_list:
        df = df[df.iloc[:, 4].apply(lambda x: str(r) not in x)]
    gl = []
    for i in range(len(df)):
        gl.append(df.iloc[i, 2] in df.iloc[i, 5])
    df = df[gl]

    print('after remove', df.shape)
    df.to_csv('result_combine_result_and_remove_data.csv', index=None, header=None)


def remove_rare_symbol():
    df = pd.read_csv('result_combine_result_and_remove_data.csv')
    r_list = ['\r', '\n', ' ', '?', '!', '！']
    for i in [0, 4]:
        for r in r_list:
            df.iloc[:, i] = df.iloc[:, i].apply(lambda x: str(x).replace(r, ''))
    df.to_csv('result_remove_rare_symbol.csv', index=None, header=None)


def add_main(df):
    data = df.iloc[0, :].values
    data[4] = data[0] + '-首页'
    data[5] = data[1]

    add_df = pd.DataFrame([data])
    return pd.concat([add_df, df])


def add_main_page():
    df = pd.read_csv('result_remove_rare_symbol.xls')
    # r_list = ['通知']
    # for r in r_list:
    #     df = df[df.iloc[:, 4].apply(lambda x: r not in x)]
    df = df.groupby(2).apply(add_main)
    df.to_csv('result.csv')


# for test
DEBUG = False
URL = 'http://www.sjzhb.gov.cn/'
U = 'sjzhb.gov.cn'
NAV_DATA = ['class', 'navbar_box']

PROCESS = True

if __name__ == '__main__':
    if PROCESS:
        combine_result_and_remove_data()
        remove_rare_symbol()
        # add_main_page()
    else:
        mt = SplitTool()
        while 1:
            try:
                # 如果为复杂网页，直接请求子网页
                complex = False
                # 指定标题里面的第几段为title
                position = 0
                if DEBUG:
                    url = URL
                    u = U
                else:
                    print('请输入url(不带www和http等字符):\r')
                    url = input()
                    if url.startswith('C'):
                        url = url[1:]
                        complex = True
                    if ' ' in url:
                        url, position = url.split(' ')
                    u = url.split('/')[0]
                    if u.startswith('1'):
                        u = u[1:]
                        url = 'http://' + url[1:]
                    else:
                        url = 'http://www.' + url
                mt.html_split(url, u, int(position), complex)
                if DEBUG:
                    print('end debug')
                    break
            except Exception as e:
                traceback.print_exc()
                print('-' * 50)

    # mt.driver.close()
