import json
import os
import shutil
import time

import markdown2
import requests

import console
import ui

from parse.exhentaiparser import renew, renew_account, ExhentaiParser
from core.database import create_db
from conf.config import CONFIGPATH, COOKIE_FILE, CACHEPATH, IMAGEPATH
from core.utility import generate_tag_translator_json, update_tagtranslator_dict

class ReadmeView (ui.View):
    def __init__(self, md_text):
        self.name = 'README'
        html = markdown2.markdown(md_text)#, output_format='html5')
        web = ui.WebView(name='web')
        web.load_html(html)
        self.add_subview(web)
        
    def layout(self):
        self['web'].frame = (0, 0, self.width, self.height)


class WelcomeView (ui.View):
    def __init__(self):
        pass
        # self.background_color = 'red'
    
    def did_load(self):
        self['button_cancel'].action = self.close_view
        self['button_readme'].action = self.present_readme
        self['button_test_web'].action = self.test_web
        self['button_next'].action = self.get_account_password
        is_ipad = check_is_ipad()
        if not is_ipad:
            self['button1'].image = ui.Image.named('iob:close_24')
            self['button1'].tint_color = 'red'
            self['label_next'].text = '很遗憾，您的设备不是iPad'
            t = console.alert('本App只适配iPad，是否继续？', '', 'Yes')
    
    def get_account_password(self, sender):
        try:
            username, password = console.login_alert('请输入账号密码')
        except KeyboardInterrupt:
            self.close()
        if username and password:
            renew_account(username, password)
            renew()
            init_config()
            create_db()
            get_favcat()
            generate_tag_translator_json()
            update_tagtranslator_dict()
            import conf.global_variables as glv
            glv.init()
            self.present_listview()
            self.close()
        
    @ui.in_background
    def present_listview(self):
        from core.listview import listview
        time.sleep(0.5)
        listview()
    
    def present_readme(self, sender):
        v = ReadmeView(open('README.md', encoding='utf-8').read())
        v.present()
        
    def test_web(self, sender):
        url = 'https://e-hentai.org'
        try:
            r = requests.get(url)
        except:
            success = False
        else:
            if r.ok:
                success = True
            else:
                success = False
        if success:
            console.hud_alert('成功')
        else:
            console.hud_alert('失败', 'error')
            self['button2'].image = ui.Image.named('iob:close_24')
            self['button2'].tint_color = 'red'
            self['label_next'].text = '很遗憾，似乎您的网络还没设置好'
    
    def close_view(self, sender):
        self.close()
            
def check_is_ipad():
    a, b = ui.get_screen_size()
    if a < 768 or b < 768:
        return False
    else:
        return True
        
def init_config():
    if not os.path.exists(IMAGEPATH):
        os.mkdir(IMAGEPATH)
    if not os.path.exists(CACHEPATH):
        os.mkdir(CACHEPATH)
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

def welcome():
    v = ui.load_view('gui/welcome_view.pyui')
    v.present('sheet', hide_title_bar=True)
