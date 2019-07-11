import json

from conf.config import COOKIE_FILE
from parse.exhentaiparser import ExhentaiParser

def init():
    """在主模块初始化"""
    global PARSER
    PARSER = ExhentaiParser(
        cookies_dict=json.loads(open(COOKIE_FILE).read())
            )

