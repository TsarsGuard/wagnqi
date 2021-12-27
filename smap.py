#!/usr/bin/python
import configparser
import time
import requests  # get the requsts library from https://github.com/requests/requests
from bs4 import BeautifulSoup
import os
import logging
import datetime
import sys

BASE_DIR = os.path.abspath(os.curdir)
logger = logging.getLogger('nasm')
logger.setLevel(level=logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')

file_handler = logging.FileHandler(BASE_DIR + "/nasm.log")
file_handler.setLevel(level=logging.INFO)
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)


# overriding requests.Session.rebuild_auth to mantain headers when redirected

class SessionWithHeaderRedirection(requests.Session):
    AUTH_HOST = 'urs.earthdata.nasa.gov'

    def __init__(self, username, password):

        super().__init__()

        self.auth = (username, password)

    # Overrides from the library to keep headers when redirected to or from

    # the NASA auth host.

    def rebuild_auth(self, prepared_request, response):

        headers = prepared_request.headers

        url = prepared_request.url

        if 'Authorization' in headers:

            original_parsed = requests.utils.urlparse(response.request.url)

            redirect_parsed = requests.utils.urlparse(url)

            if (original_parsed.hostname != redirect_parsed.hostname) and \
 \
                    redirect_parsed.hostname != self.AUTH_HOST and \
 \
                    original_parsed.hostname != self.AUTH_HOST:
                del headers['Authorization']

        return


class downTools():

    def __init__(self):
        config = configparser.ConfigParser()
        config.read('properties.conf')
        self.nasa_url = config['settings']['nasa_url']
        self.download_path = config['settings']['download_path']
        self.day_time = ""
        self.file2 = ""
        self.count = 0
        username = config['settings']['username']
        password = config['settings']['password']
        self.session = SessionWithHeaderRedirection(username, password)
        print("username：初始化成功！")

    def getFileName(self, input_date=None):
        try:
            # 判断有无入参,如果有输入日期下载输入日期，如无下载当天
            if input_date is None:
                temp_date = datetime.datetime.now()  # 获取当前时间 年月日时分秒
                self.day_time = (temp_date + datetime.timedelta(days=-20)).strftime("%Y.%m.%d")  #
            else:
                self.day_time = input_date  # 格式为2021.01.01
            # 判断是是否已经下载
            self.download_path = self.download_path + self.day_time + "/"
            if os.path.exists(self.download_path):
                logger.info("已完成下载{0}".format(self.day_time))
                return
            today_url = self.nasa_url + '/' + self.day_time + "/"
            logger.info("开始下载" + today_url)
            response = self.session.get(today_url, stream=True)
            if response.status_code == 404:
                logger.info("{0}未更新".format(today_url))
                return
            soup = BeautifulSoup(response.content, "lxml")
            logger.info("下载{0}成功，开始解析".format(today_url))
            table = soup.table
            tr_list = table.find_all('tr')
            self.count = 0
            for child in tr_list:
                if child.attrs['class'][0] == 'odd':
                    logger.info("开始下载{0}".format(child.attrs['class'][0]))
                    self.downLoadSMAP(child.a.attrs["href"])
                elif child.attrs['class'][0] == 'even' and child.a.attrs["href"].find(".xml") != -1:
                    logger.info("开始下载{0}".format(child.attrs['class'][0]))
                    self.downLoadSMAP(child.a.attrs["href"])
        except Exception as e:
            if self.count < 5:
                self.count = self.count + 1
                logger.error(e)
                logger.info('第{0}次连接失败'.format(self.count))
                self.getFileName(input_date)
            else:
                logger.info('重试5次失败，请手动检查')

    def downLoadSMAP(self, filename):
        try:
            downloadname = self.download_path + filename
            # create session with the user credentials that will be used to authenticate access to the data
            # submit the request using the sessionS
            response = self.session.get(self.nasa_url + "/" + self.day_time + "/" + filename, stream=True)
            if response.status_code == 404:
                logger.info("{0}不存在".format(self.nasa_url + self.day_time + filename))
                return
            logger.info("连接{0},成功".format(filename))
            logger.info(response.status_code)
            # raise an exception in case of http errorsS
            response.raise_for_status()

            if not os.path.exists(self.download_path):
                os.mkdir(self.download_path)
            # save the file
            with open(downloadname, 'wb') as fd:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    fd.write(chunk)
            logger.info("保存{0}成功".format(downloadname))
            print("success!!!")
        except requests.exceptions.HTTPError as e:
            if self.count < 5:
                self.count = self.count + 1
                logger.error(e)
                logger.info('第{0}次下载文件失败'.format(self.count))
                self.getFileName(filename)
            else:
                logger.error('下载文件5次失败，请手动检查')


if __name__ == '__main__':
    d = downTools()
    if len(sys.argv) > 1:
        d.getFileName(sys.argv[1])
    else:
        d.getFileName()
