import re
import os
import time
import traceback

import pandas as pd
from selenium import webdriver
from bs4 import BeautifulSoup
from bs4 import Tag

from mark_tool import config_util

failed_set = set()


class SplitTool(object):
    def __init__(self):
        self._read_config_info()
        self._init_chrome()
        self._config_load()
        self.default_css_selector = ''
        self.set_default_css_selector = False

    def _read_config_info(self):
        pass

    def _init_chrome(self):
        # 使用edge，bug更少
        if USE_CHROME:
            # 初始化webDriver，配置其不显示图片
            chrome_options = webdriver.ChromeOptions()
            if REMOVE_PICTURE_IN_CHROME:
                prefs = {"profile.managed_default_content_settings.images": 2}
                chrome_options.add_experimental_option("prefs", prefs)
            self.driver = webdriver.Chrome(
                executable_path=PATH_CHROME_DRIVE,
                chrome_options=chrome_options)
        else:
            self.driver = webdriver.Edge(
                executable_path=PATH_EDGE_DRIVE)

    def _refreshPage(self):
        oldUrl = self.driver.current_url
        try:
            self.driver.refresh()
        except Exception as e:
            pass
        if oldUrl != self.driver.current_url:
            pass

    def _quit(self):
        self.driver.quit()

    def _config_load(self, config_file='config.json'):
        self.jcu = config_util.JsonConfigUtil(config_file)
        self.start_position = self.jcu.get('start_position')

    def _get_tag_value(self, dict_name, tag_name):
        tag_dict = self.jcu.get(dict_name)
        selector = tag_dict['default']
        for key in tag_dict:
            full_p = '.*' + key + '.*'
            if re.match(full_p, tag_name) is not None:
                selector = tag_dict[key]
        return selector

    def _find_a(self, html, main_url, main_name, nav_data, top_k=9):
        bs = BeautifulSoup(html, 'html.parser')
        queue = []
        # 下面的代码自动将nth-child转换成为nth-of-type，
        # 因为BeautifulSoup只支持后者，然而chrome复制下来的是nth-child
        while 'nth-child' in nav_data:
            bf = nav_data.split(':nth-child', 1)
            f, t = bf[0].rsplit(' > ', 1)
            type_index = 0
            aim_index = int(
                bf[1][int(bf[1].find('(')) + 1: int(bf[1].find(')'))])
            index = 1
            for i, c in enumerate(bs.select(f)[0].children):
                if isinstance(c, Tag):
                    if c.name == t:
                        type_index += 1
                    if aim_index == index:
                        break
                    index += 1
            nav_data = (bf[0] + ':nth-of-type('
                        + str(type_index) + bf[1][bf[1].find(')'):])
        print('css:', nav_data)
        bl = bs.select(nav_data)
        if not bl:
            print(f'-----did not find aim element:{nav_data}-----')
        else:
            queue.append((bs.select(nav_data)[0], [main_name]))
        r = []
        a_level_list = []
        while queue:
            e, l = queue.pop(0)
            if isinstance(e, Tag):
                children = e.children
                name = ''
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
                        url_name = (pre_name + name).replace(' ', '')
                        r.append([c['href'], url_name, len(l)])
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
                l[0] = (main_url.split('//')[0] + '//'
                        + main_url.split('//')[1].split('/')[0] + l[0])
            elif not l[0].startswith('http'):
                l[0] = main_url + '/' + l[0]
        self._contain_remove(rr)
        return rr

    def _contain_remove(self, aim):
        r_list = []
        for i in range(len(aim)):
            for j in range(len(aim)):
                if i != j:
                    if aim[j][0] in aim[i][0] and aim[j] not in r_list:
                        r_list.append(aim[j])
        for i in r_list:
            aim.remove(i)

    def _get_value(self, s, default=0):
        r = default
        try:
            r = int(s)
        except Exception as e:
            print(s, 'get int value error', e)
        return r

    #add default css selector in the same type of pages
    #create by rhluo 2018-12-10
    def open_url(self, url, title=None, global_css_selector=None):
        self.driver.get(url)
        top_k = 10
        position = 0
        is_complex_page = False
        default_css_selector = ''
        set_default_css_selector = False
        more_text = ''
        html = self.driver.page_source
        main_page_url = self.driver.current_url
        params = [[]]
        #todo
        if not global_css_selector:
            print('请输入配置参数(c,tp,tk,title,css):\r')
            params = input().split(' ')
        if params[0]:
            for p in params:
                #print(p)
                if p.startswith('tp'):
                    position = self._get_value(p[2:])
                elif p.startswith('tk'):
                    top_k = self._get_value(p[2:])
                elif p.startswith('title'):
                    title = p[5:]
                elif p.startswith('css'):
                    #print("css set success !!\r")
                    set_default_css_selector = True
                elif p.startswith('c'):
                    is_complex_page = True
                elif p.startswith('more'):
                    more_text = p[4:]
                    is_complex_page = True
                elif p.startswith('ok'):
                    return (
                        [[main_page_url, title, 1, None]],
                        title, main_page_url, is_complex_page)

        if set_default_css_selector:
            print('请输入默认的全局css selector:\r')
            default_css_selector = input()

        if not title:
            title = self.driver.title
            for sc in TITLE_SPLIT_LIST:
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
            nav_selector = NAV_DATA
        elif global_css_selector:
            nav_selector = global_css_selector
        else:
            print('请输入需要拆分导航栏的css selector:\r')
            nav_selector = input()
        self.selector = nav_selector
        pt = title

        if more_text:
            pt = title + '-' + more_text

        data = self._find_a(html, url, pt, nav_selector, top_k)
        for d in data:
            if set_default_css_selector:
                d.append(default_css_selector)
            else:
                d.append(None)
        return (data,title, main_page_url, is_complex_page)

    def write2file(self, data, title, main_page_url, u):
        if data is None or len(data) == 0:
            print(title, self.selector, 'no result')
            return
        result = []
        for d in data:
            r = [
                title, main_page_url, u.split('/')[0], 1,
                d[1], d[0], '', '', '', '', '', '', ''
            ]
            result.append(r)
        df = pd.DataFrame(result)
        for r in TITLE_RARE_SYMBOL:
            title = title.replace(r, '')
            self.selector = self.selector.replace(r, '')

        if not os.path.exists('split_result'):
            os.mkdir('split_result')
        df.to_csv('split_result/' + title + '_' + self.selector + '.csv',
                  index=None, header=None)

    def html_split(self, main_url, u):
        self.main_url = main_url
        data, title, main_page_url, is_complex_page = self.open_url(main_url)
        if is_complex_page:
            dl = []
            while data:
                d = data.pop()
                if u in d[0]:
                    try:
                        #print(d[3])
                        if NOT_OPEN_WORD_IN_REMOVE_LIST:
                            if d[1].split('-')[-1] in REMOVE_LIST:
                                print(f'title {d[1]} in remove list! Jump it!')
                                continue
                        print(f'begin to load {d[1]} url:{d[0]}')
                        dd, _, _, is_complex_page = self.open_url(d[0], d[1], d[3])

                        if is_complex_page:
                            data.extend(dd)
                            print(f'{d[1]} is complex page!'
                                  f'total size:{len(dd)}')
                        else:
                            print(f'{d[1]} complete! total size:{len(dd)}')
                            dl.extend(dd)
                    except Exception as e:
                        print(e)
            data = dl

        # if self.set_default_css_selector:
        #     self.set_default_css_selector = False
        #     self.default_css_selector = ''
        self.write2file(data, title, main_page_url, u)
        print('{} complete! total size:{}'.format(title, len(data)))

    def print_line(self, lines=1):
        for i in range(lines):
            print('-' * 50)


def combine_result_and_remove_data():
    try:
        fs = os.listdir('split_result')
    except FileNotFoundError:
        print('未找到要合并的文件，请先做拆分再合并')
        exit(-1)
    df = pd.DataFrame()
    for f in fs:
        if 'DS_Store' in f:
            continue
        print(f)
        try:
            df_t = pd.read_csv('split_result/' + f, engine='python',
                               index_col=False, header=None, encoding='utf-8')
        except Exception as e:
            print(e)
            df_t = None
        if df_t is not None:
            df = pd.concat([df, df_t], axis=0)
        print(df.shape)
    print(df.head(10))
    if len(df) == 0:
        return
    for r in REMOVE_LIST:
        df = df[df.iloc[:, 4].apply(lambda x: str(r) not in x)]
    gl = []
    for i in range(len(df)):
        gl.append(df.iloc[i, 2] in df.iloc[i, 5])
    df = df[gl]

    print('after remove', df.shape)
    df.insert(0, column='id', value=ID)
    df.to_csv('result_combine_result_and_remove_data.csv', index=None,
              header=None)


def remove_rare_symbol():
    if os.path.exists('result_combine_result_and_remove_data.csv'):
        df = pd.read_csv('result_combine_result_and_remove_data.csv',
                         index_col=False, header=None)
        for i in [1, 5]:
            for r in RARE_SYMBOL:
                df.iloc[:, i] = df.iloc[:, i].apply(
                    lambda x: str(x).replace(r, ''))
        if SAVE_IN_EXCEL:
            df.to_excel('result_remove_rare_symbol.xls', index=None,
                        header=None, encoding='utf-8')
        else:
            df.to_csv('result_remove_rare_symbol.csv', encoding='utf-8',
                      index=None, header=None)


def add_main(df):
    data = df.iloc[0, :].values
    data[4] = data[0] + '-首页'
    data[5] = data[1]

    add_df = pd.DataFrame([data])
    return pd.concat([add_df, df])


def add_main_page():
    df = pd.read_csv('result_remove_rare_symbol.xls')
    df = df.groupby(2).apply(add_main)
    df.to_csv('result.csv')


# for test
DEBUG = False
URL = 'http://www.sjzhb.gov.cn/'
U = 'sjzhb.gov.cn'
NAV_DATA = ['class', 'navbar_box']
PATH_CHROME_DRIVE = '../driver/chromedriver.exe'
PATH_EDGE_DRIVE = '../driver/MicrosoftWebDriver.exe'
# 移除关键字
NOT_OPEN_WORD_IN_REMOVE_LIST = True
REMOVE_LIST = [
    '公开', '文件', '政策法规', '公示', '首页', '关于', '简介', '联系', '互动',
    '组织机构', '概况', '国务院', '下载', '帮助', '报名', '通知', '公告', '领导', '机构',
    '百科', '视频', '图片', '支部', '群众来信', '学习园地'
]
# 内容罕见字符
RARE_SYMBOL = ['\r', '\n', ' ', '?', '!', '！', '-更多', '-more', '>']
# 标题罕见字符
TITLE_RARE_SYMBOL = [';', ':', '-', '#', '/', '\\', ' > ', '(', ')']
# 标题的分隔符
TITLE_SPLIT_LIST = [',', ' ', '-', '_', '|', '——']

PROCESS = False
ID = 277
USE_CHROME = True
REMOVE_PICTURE_IN_CHROME = False
SAVE_IN_EXCEL = False


def main():
    print("开启抓取模式，输入其他字符；开启合并模式，输入1：")
    mode = input()
    PROCESS = True if mode == '1' else False
    if PROCESS:
        combine_result_and_remove_data()
        remove_rare_symbol()
        # add_main_page()
    else:
        mt = SplitTool()
        lasturl = ''
        while True:
            try:
                if DEBUG:
                    url = URL
                    u = U
                else:
                    print('请输入url(不带www和http等字符，如果不需要程序追加www，'
                          '请在url前面加"N"，例如"Nbaidu.com"):\r')
                    print('是否继续上一url? 若是则输入?字符')
                    url = input()
                    if url == '?':
                        url = lasturl
                    else:
                        u = url.split('/')[0]
                        if u.startswith('N'):
                            u = u[1:]
                            url = 'http://' + url[1:]
                        else:
                            url = 'http://www.' + url
                mt.html_split(url, u)
                lasturl = url
                if DEBUG:
                    print('end debug')
                    break
            except Exception as e:
                traceback.print_exc()
                print('-' * 50)
    # mt.driver.close()


if __name__ == '__main__':
    main()
