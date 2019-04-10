# -*- coding: utf-8 -*-
# __author__ = "zok"  362416272@qq.com
# Date: 2019-04-09  Python: 3.7


import re
import pymysql

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
from config import *

# test

conn = pymysql.Connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            db=MYSQL_DB_NAME,
        )

browser = webdriver.Firefox(executable_path='./geckodriver')
wait = WebDriverWait(browser, 10)

browser.set_window_size(1400, 900)


def search():
    print('正在搜索')
    try:
        browser.get('https://www.taobao.com')
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#q'))
        )
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_TSearchForm > div.search-button > button')))
        input.send_keys(KEYWORD)
        submit.click()
        total = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.total')))
        get_products()
        return total.text
    except TimeoutException:
        return search()


def next_page(page_number):
    print('正在翻页', page_number)
    try:
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > input'))
        )
        submit = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit')))
        input.clear()
        input.send_keys(page_number)
        submit.click()
        wait.until(EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > ul > li.item.active > span'), str(page_number)))
        get_products()
    except TimeoutException:
        next_page(page_number)


def get_products():
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item')))
    html = browser.page_source
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            'image': 'https:' + item.find('.pic .img').attr('data-src'),  # 商品图片
            'price': item.find('.price').text(),  # 商品价格
            'goods_href': 'https:' + item.find('.J_ClickStat').attr('href'),  # 商品链接
            'deal': item.find('.deal-cnt').text()[:-3],  # 付款人数
            'title': item.find('.title').text(),  # 标题
            'shop': item.find('.shop').text(),  # 店铺名
            'location': item.find('.location').text(),  # 店铺地址
            'shop_id': item.find('.J_ShopInfo').attr('data-userid'),  # 店铺ID
            'shop_href': 'https:' + item.find('.J_ShopInfo').attr('href'),  # 店铺href
        }
        print(product)
        save_to_mysql(product)


def save_to_mysql(result):
    sql = """INSERT INTO goods(title,price,deal,goods_href,shop,location,shop_id,shop_href) VALUES ("{title}","{price}","{deal}","{goods_href}","{shop}","{location}","{shop_id}","{shop_href}") """.format(
        title=result['title'],
        price=result['price'],
        deal=result['deal'],
        goods_href=result['goods_href'],
        shop=result['shop'],
        location=result['location'],
        shop_id=result['shop_id'],
        shop_href=result['shop_href'],
    )

    cursor = conn.cursor()
    # 提交事务
    try:
        cursor.execute(sql)
        conn.commit()
    except Exception as e:
        print(e)
        print('异常回滚')
        conn.rollback()


def main():
    try:
        total = search()
        total = int(re.compile('(\d+)').search(total).group(1))
        for i in range(2, total + 1):
            next_page(i)
    except Exception:
        print('出错啦')
    finally:
        browser.close()


if __name__ == '__main__':
    main()
