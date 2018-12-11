import re
import os
import time
import traceback

import pandas as pd
from selenium import webdriver
from bs4 import BeautifulSoup
from bs4 import Tag

failed_set = set()


class SplitTool(object):
    def __init__(self):
        self._init_chrome()

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

    def _quit(self):
        self.driver.quit()

    def _change_selector_2_bs(self, bs, css_selector):
        # 下面的代码主要是修改css selector的，自动将nth-child转换成为nth-of-type，
        # 因为BeautifulSoup只支持后者，然而chrome复制下来的是nth-child
        while 'nth-child' in css_selector:
            bf = css_selector.split(':nth-child', 1)
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
            css_selector = (bf[0] + ':nth-of-type('
                            + str(type_index) + bf[1][bf[1].find(')'):])
        return css_selector

    def _page_url_rewrite(self, main_url, r, top_k_a_level):
        # 重写url
        url_list = []
        for l in r:
            if l[2] in top_k_a_level:
                url_list.append(l)
            if l[0].startswith('//'):
                l[0] = 'http:' + l[0]
            elif l[0].startswith('/'):
                l[0] = (main_url.split('//')[0] + '//'
                        + main_url.split('//')[1].split('/')[0] + l[0])
            elif not l[0].startswith('http'):
                # 有些网站会有index.php，asp等结尾，需要去掉
                if main_url.endswith('/'):
                    l[0] = main_url + l[0]
                else:
                    url_remove_list = ['.asp', '.jsp', '.php', '?', '=',
                                       '.html']
                    end_index = len(main_url)
                    for s in url_remove_list:
                        if s in main_url:
                            end_index = main_url.rindex('/')
                            break
                    l[0] = main_url[:end_index] + '/' + l[0]
        return url_list

    def _bfs_get_a(self, queue):
        # 通过广度优先搜索去寻找a标签
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
                        # url,page title,level index,global css selector
                        r.append([c['href'], url_name, len(l), None])
                    else:
                        t = list(l)
                        t.append(name)
                        queue.append((c, t))
        return r, a_level_list

    def _contain_remove(self, aim):
        # 判断上下级url是否有包含关系，删除被包含的url
        r_list = []
        for i in range(len(aim)):
            for j in range(len(aim)):
                if i != j:
                    if aim[j][0] in aim[i][0] and aim[j] not in r_list:
                        r_list.append(aim[j])
        for i in r_list:
            aim.remove(i)

    def _find_a(self, html, main_url, main_name, nav_selector, top_k=9):
        bs = BeautifulSoup(html, 'html.parser')
        queue = []
        nav_selector = self._change_selector_2_bs(bs, nav_selector)
        print('css:', nav_selector)
        bl = bs.select(nav_selector)
        if not bl:
            print(f'-----did not find aim element:{nav_selector}-----')
        else:
            queue.append((bs.select(nav_selector)[0], [main_name]))
        a_list, a_level_list = self._bfs_get_a(queue)
        top_k_a_level = a_level_list[:top_k]
        a_after_rewrite_list = self._page_url_rewrite(main_url, a_list,
                                                      top_k_a_level)
        self._contain_remove(a_after_rewrite_list)
        return a_after_rewrite_list

    def _get_value(self, s, default=0):
        # 获取 string 的整数值
        r = default
        try:
            r = int(s)
        except Exception as e:
            print(s, 'get int value error', e)
        return r

    # add default css selector in the same type of pages
    # create by rhluo 2018-12-10
    def open_url(self, url, title=None, global_css_selector=None):
        self.driver.get(url)
        top_k = 10
        position = 0
        is_complex_page = False
        default_css_selector = ''
        set_default_css_selector = False
        iframe_index = -1
        more_text = ''

        main_page_url = self.driver.current_url

        params = [[]]
        if not global_css_selector:
            print('请输入配置参数(c,tp,tk,title,css,ok,more)，默认直接回车:\r')
            params = input().split(' ')
        if params[0]:
            for p in params:
                if p.startswith('tp'):
                    # title position,配置title split所取得第几个字符串作为title
                    # 从1 开始
                    position = self._get_value(p[2:])
                elif p.startswith('tk'):
                    # top k配置,防止程序url 解析过深
                    top_k = self._get_value(p[2:])
                elif p.startswith('iframe'):
                    # 解析到iframe
                    iframe_index = self._get_value(p[6:])
                elif p.startswith('title'):
                    # 直接设置当前网页得title
                    title = p[5:]
                elif p.startswith('css'):
                    # 设置当前页面下所有子页面的 css selector
                    set_default_css_selector = True
                elif p.startswith('c'):
                    # 配置当前网站为复杂网站
                    is_complex_page = True
                elif p.startswith('more'):
                    # 从 更多 等关键字打开网站
                    more_text = p[4:]
                    is_complex_page = True
                elif p.startswith('ok'):
                    # 直接认为当前页面是所需页面
                    return (
                        [[main_page_url, title, 1, None]],
                        title, main_page_url, is_complex_page)

        if set_default_css_selector:
            while not default_css_selector:
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

        if iframe_index >= 0:
            self.driver.switch_to.frame(iframe_index)
        nav_selector = ''
        if DEBUG:
            nav_selector = NAV_DATA
        elif global_css_selector:
            nav_selector = global_css_selector
        else:
            # 防止多余的回车
            while not nav_selector:
                print('请输入需要拆分导航栏的css selector:\r')
                nav_selector = input()
        self.selector = nav_selector
        pt = title
        if more_text:
            pt = title + '-' + more_text
        html = self.driver.page_source
        url_data_list = self._find_a(html, url, pt, nav_selector, top_k)
        for d in url_data_list:
            if set_default_css_selector:
                d[3] = default_css_selector
        return (url_data_list, title, main_page_url, is_complex_page)

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
        # 主入口
        self.main_url = main_url
        data, title, main_page_url, is_complex_page = self.open_url(main_url)
        if is_complex_page:
            dl = []
            while data:
                d = data.pop()
                if u in d[0]:
                    try:
                        if NOT_OPEN_WORD_IN_REMOVE_LIST:
                            if d[1].split('-')[-1] in REMOVE_LIST:
                                print(f'title {d[1]} in remove list! Jump it!')
                                continue
                        print(f'begin to load {d[1]} url:{d[0]}')
                        dd, _, _, is_complex_page = self.open_url(d[0], d[1],
                                                                  d[3])

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
        self.write2file(data, title, main_page_url, u)
        print('{} complete! total size:{}'.format(title, len(data)))


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
                        header=None, encoding='gbk')
        else:
            df.to_csv('result_remove_rare_symbol.csv', encoding='gbk',
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
    '组织机构', '概况', '国务院', '下载', '帮助', '报名', '通知', '公告', '领导',
    '百科', '视频', '支部', '群众来信', '机构', '学习园地'
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
    print("开启抓取模式，请直接回车；开启合并模式，输入1：")
    mode = input()
    PROCESS = mode == '1'
    if PROCESS:
        combine_result_and_remove_data()
        remove_rare_symbol()
        # add_main_page()
    else:
        mt = SplitTool()
        last_url = ''
        u = None
        while True:
            try:
                url = ''
                if DEBUG:
                    url = URL
                    u = U
                else:
                    # 防止用户多输入回车
                    while not url:
                        print('请输入url，继续上一url则输入"?"'
                              '(不带www和http等字符，如果不需要程序追加www，'
                              '请在url前面加"N"，例如"Nbaidu.com"):\r')
                        url = input()
                    if url == '?':
                        url = last_url
                    else:
                        u = url.split('/')[0]
                        if u.startswith('N'):
                            u = u[1:]
                            url = 'http://' + url[1:]
                        else:
                            url = 'http://www.' + url
                mt.html_split(url, u)
                last_url = url
                if DEBUG:
                    print('end debug')
                    break
            except Exception as e:
                # traceback.print_exc()
                print('-' * 25, str(e), '-' * 25)
    # mt.driver.close()


if __name__ == '__main__':
    main()
