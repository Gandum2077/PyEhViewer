import json
import os
import shutil

import console
import dialogs
import ui

from parse.exhentaiparser import renew, renew_account, ExhentaiParser
from core.database import create_db
from conf.config import CONFIGPATH, COOKIE_FILE

def is_suitable_device():
    a, b = ui.get_screen_size()
    if a == 1024 and b == 768 or b == 1024 and a == 768:
        return True
        
def init_config():
    if os.path.exists(CONFIGPATH):
        os.remove(CONFIGPATH)
    shutil.copy(CONFIGPATH + '.example', CONFIGPATH)
    
def get_favcat():
    parser = ExhentaiParser(
        cookies_dict=json.loads(open(COOKIE_FILE).read())
            )
    url = 'https://exhentai.org/favorites.php'
    t = parser.get_list_infos(url)
    with open(CONFIGPATH, encoding='utf-8') as f:
        config = json.loads(f.read())
    config['favcat_nums_titles'] = t['favcat_nums_titles']
    config['favorites_order_method'] = t['favorites_order_method']
    text = json.dumps(config, indent=2, sort_keys=True)
    with open(CONFIGPATH, 'w', encoding='utf-8') as f:
        f.write(text)
ipadpro_iphone_warning = "未针对此设备调整UI"

choices_list = [
    'exhentai是啥？',
    '我有刚注册的e-hentai账号但还不能进入exhentai',
    '我有exhentai账号但没有Multi-Page Viewer的Hath Perk',
    '我有exhentai账号而且有Multi-Page Viewer的Hath Perk'
    ]
    
manual = [
    "绅士的隐蔽乐园，请于表站e-hentai.org注册账号，刚注册账号不能访问exhentai.org，需要等待2星期左右",
    "刚注册账号不能访问exhentai.org，需要等待2星期左右",
    "请去https://e-hentai.org/hathperks.php点亮Multi-Page Viewer的Hath Perk，需要300Hath币或捐款100美元"
    ]

def welcome():
    if not is_suitable_device():
        console.hud_alert(ipadpro_iphone_warning, 'error')
    t = dialogs.list_dialog(
        title="最符合你状况的描述是：",
        items=choices_list,
        multiple=False)
    if t == choices_list[0]:
        console.alert(manual[0])
    elif t == choices_list[1]:
        console.alert(manual[1])
    elif t == choices_list[2]:
        console.alert(manual[2])
    elif t == choices_list[3]:
        username, password = console.login_alert('请输入账号密码')
        if username and password:
            renew_account(username, password)
            renew()
            init_config()
            create_db()
            get_favcat()
            
            
