import json
import math
import os
import re
import shutil
import urllib.parse
from pathlib import Path

import clipboard
import console
import dialogs
import ui

from conf.config import CACHEPATH, IMAGEPATH, CONFIGPATH, ACCOUNT_FILE
import conf.global_variables as glv
from core.advancedsearch import AdvancedSearchView
from core.database import create_db, insert_info, delete_by_gid, search_by_url
from core.galleryview import galleryview
from core.rating_stars_view import render_rating_stars_view
from core.storage_search_phrases_view import render_storage_search_phrases_view
from core.utility import get_coordinate, get_color, translate_taglist, render_taglist_to_text, get_color_from_favcat, verify_url, detect_url_category, get_search_url, add_querydict_to_url
import parse.exhentaiparser

# 读取config.json的变量
with open(CONFIGPATH, encoding='utf-8') as f:
    t = json.loads(f.read())
    DEFAULT_URL = t.get('default_url')
    SEARCH_PHRASES = t.get('search_phrases')
    STORAGE_SEARCH_PHRASES = t.get('storage_search_phrases')
    DISPLAY_DOWNLOADS_ON_START = t.get('display_downloads_on_start')
    FAVCAT_NUMS_TITLES = t.get('favcat_nums_titles')
    FAVORITES_ORDER_METHOD = t.get('favorites_order_method')
    DOWNLOADS_ORDER_METHOD = t.get('downloads_order_method')

def save_config():
    with open(CONFIGPATH, encoding='utf-8') as f:
        config = json.loads(f.read())
    config['default_url'] = DEFAULT_URL
    config['search_phrases'] = SEARCH_PHRASES
    config['storage_search_phrases'] = STORAGE_SEARCH_PHRASES
    config['display_downloads_on_start'] = DISPLAY_DOWNLOADS_ON_START
    config['favcat_nums_titles'] = FAVCAT_NUMS_TITLES
    config['favorites_order_method'] = FAVORITES_ORDER_METHOD
    config['downloads_order_method'] = DOWNLOADS_ORDER_METHOD
    text = json.dumps(config, indent=2, sort_keys=True)
    with open(CONFIGPATH, 'w', encoding='utf-8') as f:
        f.write(text)

class ListView(ui.View):
    """负责产生list页面
    """
    def __init__(self):
        self.update_interval = 1
        # 伪全局变量，还有self.url
        self.search_phrase = ''
        
    def did_load(self):
        self['button_close_view'].action = self.close_view
        self['textfield_search'].delegate = TextFieldPopupDelegate()
        self['button_search'].action = self.search_button
        self['button_storage'].action = self.present_storage_search_phrases_view
        self['button_jump_to_page'].action = self.jump_to_page_button
        self['button_previous'].action = self.previous_page_button
        self['button_next'].action = self.next_page_button
        self['button_refresh'].action = self.refresh_button
        self['button_sidebar'].action = self.present_sidebar
        self['button_open_url'].action = self.open_url
    
    def layout(self):
        if self['scrollview']:
            self['scrollview'].frame=((self.width - 695 - 57 - 16)/2 + 16, 63, 695, 961)
        
    def update(self):
        if self.on_screen:
            pass
    
    def will_close(self):
        """功能:
            - 将全局变量写回config.json
        """
        save_config()

    def xdid_load(self, url):
        if url:
            self.url = url
        elif DISPLAY_DOWNLOADS_ON_START:
            self.url = 'downloads://?page=0'
        else:
            self.url = DEFAULT_URL
        asv = AdvancedSearchView(SEARCH_PHRASES, FAVCAT_NUMS_TITLES)
        asv.name = 'asv'
        asv.x = 62
        asv.y = 63
        asv.hidden = True
        asv.set_action(self.update_textfield_by_tableview)
        self.add_subview(asv)
        self.refresh()

    def init(self):
        """恢复初始
        """
        self['asv'].hidden = True
        if self['sidebar']:
            self.remove_subview(self['sidebar'])
        if self['storage_search_phrases_view']:
            self.remove_subview(self['storage_search_phrases_view'])
        self['textfield_search'].end_editing()

    def refresh(self):
        """此函数的使用时机是在self.url更新之后
        负责在刷新页面时所需要的各种更新，包括：
        self['button_sidebar'].image
        self['textfield_search'].text
        self['scrollview']
        """
        self.init()
        if self['scrollview']:
            self.remove_subview(self['scrollview'])
        t = urllib.parse.parse_qs(urllib.parse.urlparse(self.url).query).get('f_search')
        if t:
            self['textfield_search'].text = t[0]
        else:
            self['textfield_search'].text = ''
        self.search_phrase = self['textfield_search'].text
        url_category = detect_url_category(self.url)
        self._update_icon_sidebar_button(url_category)
        t = get_items(self.url, url_category)
        # 在此时机插入保存favcat_nums_titles和favorites_order_method
        if t['favcat_nums_titles']:
            global FAVCAT_NUMS_TITLES
            FAVCAT_NUMS_TITLES = t['favcat_nums_titles']
            global FAVORITES_ORDER_METHOD
            FAVORITES_ORDER_METHOD = t['favorites_order_method']
            save_config()
        self['label_current_page'].text = str(t['current_page_str'])
        self['label_total_pages'].text = str(t['total_pages_str'])
        scrollview = self._render_scrollview(t['items'], t['search_result'], url_category)
        scrollview.delegate = ScrollViewDelegate()
        self.add_subview(scrollview)

    def _update_icon_sidebar_button(self, url_category):
        if url_category == 'default':
            self['button_sidebar'].image = ui.Image.named('iob:navicon_32')
        if url_category == 'watched':
            self['button_sidebar'].image = ui.Image.named('iob:ios7_bell_32')
        if url_category == 'popular':
            self['button_sidebar'].image = ui.Image.named('iob:arrow_graph_up_right_32')
        if url_category == 'favorites':
            self['button_sidebar'].image = ui.Image.named('iob:bookmark_32')
        if url_category == 'downloads':
            self['button_sidebar'].image = ui.Image.named('iob:archive_32')
                    
    def _render_scrollview(self, items, search_result, url_category):
        scrollview = ui.ScrollView(
            frame=((self.width - 695 - 57 - 16)/2 + 16, 63, 695, 961), 
            content_size = (695, len(items)*160+24),
            name='scrollview')
        scrollview.add_subview(
            ui.Label(
                frame=(0, 0, 695, 24),
                text=search_result,
                alignment=ui.ALIGN_CENTER,
                font=('<system>', 14)
                ))
        for i, item in enumerate(items):
            v = ui.load_view('gui/itemcell.pyui')
            v.xdid_load(item)
            if url_category == 'downloads':
                v['button_delete_download'].hidden = False
                v['button_delete_download'].action = self.delete_download
            v.frame = (0, 160*i+24, 695, 160)
            scrollview.add_subview(v)
        return scrollview
 
    @ui.in_background
    def delete_download(self, sender):
        # 此参数用来恢复scrollview的阅读位置
        content_offset = self['scrollview'].content_offset
        foldername = verify_url(sender.superview.url)
        folderpath = os.path.join(IMAGEPATH, foldername)
        title = sender.superview['label_title'].text
        t = console.alert('确认删除？', title, 'Yes')
        if t == 1:
            shutil.rmtree(folderpath)
            gid = foldername[:foldername.find('_')]
            delete_by_gid(gid)
            self.refresh()
            self['scrollview'].content_offset = content_offset
            console.hud_alert('已删除')

    @ui.in_background
    def jump_to_page_button(self, sender):
        n = self['label_total_pages'].text
        if n != '1':
            t = console.input_alert('输入页码(1-{})'.format(n))
            if re.fullmatch(r'\d+', t) and 1 <= int(t) <= int(n):
                self.url = add_querydict_to_url({'page': int(t)-1}, self.url)
                self.refresh()
            else:
                console.hud_alert('输入不合法', 'error')
            
    def next_page_button(self, sender):
        m = self['label_current_page'].text
        n = self['label_total_pages'].text
        if re.fullmatch(r'\d+', m):
            if int(m) < int(n):
                self.url = add_querydict_to_url({'page': int(m)}, self.url)
                self.refresh()
        else:
            a, b = re.fullmatch(r'(\d+)-(\d+)', m).groups()
            if int(b) < int(n):
                self.url = add_querydict_to_url({'page': int(b)}, self.url)
                self.refresh()
    
    def previous_page_button(self, sender):
        m = self['label_current_page'].text
        if re.fullmatch(r'\d+', m):
            if 1 < int(m):
                self.url = add_querydict_to_url({'page': int(m)-2}, self.url)
                self.refresh()
        else:
            a, b = re.fullmatch(r'(\d+)-(\d+)', m).groups()
            if 1 < int(a):
                self.url = add_querydict_to_url({'page': int(a)-1}, self.url)
                self.refresh()
    
    def refresh_button(self, sender):
        self.refresh()

    @ui.in_background
    def close_view(self, sender):
        t = console.alert('确认退出？', '', 'Yes')
        if t == 1:
            self.close()
    
    @ui.in_background
    def open_url(self, sender):
        text = clipboard.get()
        try:
            verify_url(text)
        except:
            input = ''
        else:
            input = text
        url = console.input_alert('直接打开url', '', input)
        try:
            verify_url(url)
        except:
            console.hud_alert('URL错误', 'error')
        else:
            galleryview(url)
    
    def search_button(self, sender):
        index_to_category = {
            -1: 'default',
            0: 'default',
            1: 'watched',
            2: 'favorites',
            3: 'downloads'
            }
        querydict = self['asv'].get_querydict()
        search_text = self['textfield_search'].text
        index = self['asv']['segmentedcontrol1'].selected_index
        url_category = index_to_category[index]
        if querydict or (search_text and search_text != self.search_phrase):
            querydict.update({'f_search':search_text})
            url = get_search_url(querydict, url_category=url_category)
            self.url = url
            self.refresh()
            global SEARCH_PHRASES
            if search_text:
                if not search_text in SEARCH_PHRASES[:10]:
                    SEARCH_PHRASES = [search_text] + SEARCH_PHRASES[:9]
                else:
                    tmp = SEARCH_PHRASES[:10]
                    index = tmp.index(search_text)
                    tmp.pop(index)
                    SEARCH_PHRASES = [search_text] + tmp
                save_config()

    def update_textfield_by_tableview(self, sender):
        self['textfield_search'].text = sender.items[sender.selected_row]
        
# 以下为storage_search_phrases_view
    def present_storage_search_phrases_view(self, sender):
        if self['storage_search_phrases_view']:
            self.remove_subview(self['storage_search_phrases_view'])
        else:
            # 此处直接传递STORAGE_SEARCH_PHRASES这一对象，
            # 在其他模块中会直接操作此对象，因此本模块此处不需要再操作此对象
            view = render_storage_search_phrases_view(
                STORAGE_SEARCH_PHRASES,
                self.add_action,
                self.select_action,
                frame=(self.width-320-10, 63, 320, 480)
                )
            view.name = 'storage_search_phrases_view'
            view.flex = 'L'
            self.add_subview(view)
        
    def select_action(self, phrase):
        self['textfield_search'].text = phrase
    
    @ui.in_background
    def add_action(self, sender):
        raw = self['textfield_search'].text
        t = dialogs.form_dialog(
            title='添加搜索词',
            fields=[
                {
                    'type': 'text', 'title': '搜索词',
                    'key': 'raw', 'value': raw
                    },
                {
                    'type': 'text', 'title': '提示词',
                    'key': 'display', 'placeholder': 'optional'
                    }
                ]
            )
        if t:
            if t['display']:
                item = {'display': t['display'], 'raw': t['raw']}
            else:
                item = t['raw']
            if item:
                sender.superview.add_item(item)
        
# 以下为sidebar
    def present_sidebar(self, sender):
        if self['sidebar']:
            self.remove_subview(self['sidebar'])
        else:
            sidebar_view = ui.load_view('gui/sidebar.pyui')
            sidebar_view.frame = (16, 63, 163, 320)
            sidebar_view.name = 'sidebar'
            sidebar_view['button_default'].url = DEFAULT_URL
            sidebar_view['button_default'].action = self.open_url_sidebar
            sidebar_view['button_watched'].action = self.open_url_sidebar
            sidebar_view['button_popular'].action = self.open_url_sidebar
            sidebar_view['button_favorites'].action = self.open_url_sidebar
            sidebar_view['button_downloads'].action = self.open_url_sidebar
            sidebar_view['button_settings'].action = self.present_settings
            self.add_subview(sidebar_view)
    
    def open_url_sidebar(self, sender):
        self.url = sender.url
        self.refresh()
        if self['sidebar']:
            self.remove_subview(self['sidebar'])

# 以下为settings
    def present_settings(self, sender):
        view = ui.load_view('gui/settings.pyui')
        view['switch1'].action = self.set_display_downloads_on_start
        view['switch1'].value = DISPLAY_DOWNLOADS_ON_START
        view['textfield_default_url'].text = DEFAULT_URL
        view['textfield_default_url'].action = self.set_default_url_from_textfield
        view['button_default_url'].action = self.set_default_url_from_button
        view['button_reset_account'].action = self.reset_account
        view['button_login'].action = self.login
        view['button_update_db'].action = self.update_db
        view['button_rm_cache'].action = self.rm_cache
        view['button_rm_unfav_downloads'].action = self.rm_unfav_downloads
        view['button_rm_all_downloads'].action = self.rm_all_downloads
        if FAVORITES_ORDER_METHOD == 'Posted':
            view['segmentedcontrol_favorites'].selected_index = 1
        else:
            #包含Favorited和None两种情况
            view['segmentedcontrol_favorites'].selected_index = 0
        view['segmentedcontrol_favorites'].action = self.set_favorites_order
        if DOWNLOADS_ORDER_METHOD == 'st_mtime':
            view['segmentedcontrol_downloads'].selected_index = 1
        else:
            #包含gid和None两种情况
            view['segmentedcontrol_downloads'].selected_index = 0
        view['segmentedcontrol_downloads'].action = self.set_downloads_order
        self.init()
        view.present('sheet')
        
    def set_display_downloads_on_start(self, sender):
        global DISPLAY_DOWNLOADS_ON_START
        DISPLAY_DOWNLOADS_ON_START = sender.value
        save_config()
    
    @ui.in_background
    def set_default_url_from_textfield(self, sender):
        if sender.text != self.url:
            t = console.alert('修改default url？', '', 'Yes')
            if t == 1:
                global DEFAULT_URL
                DEFAULT_URL = sender.text
                save_config()
                console.hud_alert('完成')
            else:
                sender.text = DEFAULT_URL
    
    @ui.in_background
    def set_default_url_from_button(self, sender):
        t = console.alert('将当前url作为default url？', '', 'Yes')
        if t == 1:
            global DEFAULT_URL
            DEFAULT_URL = self.url
            sender.superview['textfield_default_url'].text = self.url
            save_config()
            console.hud_alert('完成')

    @ui.in_background
    def reset_account(self, sender):
        try:
            username, password = console.login_alert('请输入账号密码')
        except KeyboardInterrupt:
            pass
        else:
            text = json.dumps(dict(username=username, password=password), indent=2)
            with open(ACCOUNT_FILE, 'w') as f:
                f.write(text)
            console.hud_alert('完成')

    @ui.in_background
    def login(self, sender):
        t = console.alert('确定要重新登录？', '', 'Yes')
        if t == 1:
            parse.exhentaiparser.renew()
            console.hud_alert('完成')

    @ui.in_background
    def update_db(self, sender):
        t = console.alert('确定要更新数据库？', '', 'Yes')
        if t == 1:
            create_db()
            for i in Path(IMAGEPATH).iterdir():
                if len(list(i.iterdir())) > 2:
                    info = json.loads(i.joinpath('manga_infos.json').open().read())
                    insert_info(info)
            console.hud_alert('完成')

    @ui.in_background
    def rm_cache(self, sender):
        t = console.alert('确定要清除缓存？', '', 'Yes')
        if t == 1:
            shutil.rmtree(CACHEPATH)
            os.mkdir(CACHEPATH)
            for i in Path(IMAGEPATH).iterdir():
                if len(list(i.iterdir())) == 2:
                    shutil.rmtree(str(i))
            console.hud_alert('完成')

    @ui.in_background
    def rm_unfav_downloads(self, sender):
        t = console.alert('确定要清除未收藏的下载内容？', '', 'Yes')
        if t == 1:
            for i in Path(IMAGEPATH).iterdir():
                if not json.loads(i.joinpath('manga_infos.json').open().read()).get('favcat'):
                    shutil.rmtree(str(i))
            console.hud_alert('完成')

    @ui.in_background
    def rm_all_downloads(self, sender):
        t = console.alert('确定要清除全部下载内容？', '', 'Yes')
        if t == 1:
            shutil.rmtree(IMAGEPATH)
            os.mkdir(IMAGEPATH)
            console.hud_alert('完成')

    @ui.in_background
    def set_favorites_order(self, sender):
        global FAVORITES_ORDER_METHOD
        if sender.selected_index == 0:
            glv.PARSER.set_favorites_use_favorited()
            FAVORITES_ORDER_METHOD = 'Favorited'
        else:
            glv.PARSER.set_favorites_use_posted()
            FAVORITES_ORDER_METHOD = 'Posted'
        save_config()

    @ui.in_background
    def set_downloads_order(self, sender):
        global DOWNLOADS_ORDER_METHOD
        if sender.selected_index == 0:
            DOWNLOADS_ORDER_METHOD = 'gid'
        else:
            DOWNLOADS_ORDER_METHOD = 'st_mtime'
        save_config()


class TextFieldPopupDelegate (object):
    def textfield_did_begin_editing(self, textfield):
        textfield.superview['asv'].hidden = False
        textfield.superview['asv'].bring_to_front()
        textfield.superview['asv'].re_init(SEARCH_PHRASES, FAVCAT_NUMS_TITLES)


class ScrollViewDelegate (object):
    def scrollview_did_scroll(self, scrollview):
        scrollview.superview.init()

class CellView (ui.View):
    def __init__(self):
        self.update_interval = 0.1
        self.loading_flag = True
    
    def xdid_load(self, item):
        self.border_color = '#c3c3c3'
        self.border_width = 1
        self.url = item['url']
        self['label_category'].text, self['label_category'].background_color = get_color(item["category"])
        self['label_length'].text = item["length"] + '页'
        self['label_posted'].text = item["posted"]
        if item["visible"] == 'Yes':
            self['delete_line_view'].hidden = True
        else:
            self['delete_line_view'].hidden = False
        self['label_uploader'].text = item["uploader"]
        self['label_title'].text = item['title']
        x, y, w, h = self['rating_location_view'].frame
        if item['is_personal_rating']:
            rating = item['display_rating']
            personal = True
        else:
            rating = item['rating']
            personal = False
        rating_stars_view =render_rating_stars_view(
            rating,
            personal=personal,
            width=w,
            height=h,
            name='rating_stars_view'
            )
        rating_stars_view.x = x
        rating_stars_view.y = y
        self.add_subview(rating_stars_view)
        favcat = item.get('favcat')
        if favcat:
            self['label_posted'].border_color = get_color_from_favcat(favcat)
        self['textview_taglist'].text = render_taglist_to_text(translate_taglist(item['taglist']))
        self['button_open_gallery'].action = self.open_gallery
        self.add_subview(ui.ActivityIndicator(name='indicator', center=(56, 80)))
        thumbnail_url = item['thumbnail_url']
        self.img_path = os.path.join(CACHEPATH, os.path.split(urllib.parse.urlparse(thumbnail_url).path)[1])
        glv.PARSER.start_download_pic_normal([(self.img_path, thumbnail_url)], CACHEPATH)
        self.refresh()
        
    def refresh(self):
        self._load_slide()
        
    def open_gallery(self, sender):
        galleryview(self.url)
    
    def _get_pic_path(self):
        if os.path.exists(self.img_path):
            return self.img_path
        else:
            return 'loading'
    
    def _load_slide(self):
        pic_path = self._get_pic_path()
        if pic_path != 'loading':
            image = ui.Image.named(pic_path)
            w1, h1 = image.size
            self['imageview_thumbnail'].frame = get_coordinate(1, 1, 112, 158, w1, h1)
            self['imageview_thumbnail'].image = image
            self.loading_flag = False
            self['indicator'].stop()
        else:
            self['indicator'].start() 
            self.loading_flag = True
    
    def update(self):
        if self.loading_flag:
            try:
                self.refresh()
            except AttributeError:
                pass
                
class StorageSearchPhrasesView (ui.View):
    def __init__(self):
        pass
        
    def did_load(self):
        self['button_edit'].action = self.edit
        
    def xdid_load(self, items):
        self['tableview1'].data_source.items = items
    
    def edit(self, sender):
        sender.superview['tableview1'].editing = not sender.superview['tableview1'].editing
      

def get_items(url, url_category):
    """此函数根据url去获取对应的dict
    Returns
    dict keys: entries, current_page_str, total_pages_str
    """
    def get_listview_dict(url):
        return glv.PARSER.get_list_infos(url)

    def transfer_config(path):
        config = json.loads(open(path).read())
        if config['japanese_title']:
            config['title'] = config['japanese_title']
        else:
            config['title'] = config['english_title']
        config['category'] = config['category'].lower()
        return config

    def checkpics(path):
        nums_of_pics = len(os.listdir(path)) - 2
        return nums_of_pics

    def get_storageview_dict(url):
        search_result = search_by_url(url)
        folders =[
            Path(IMAGEPATH).joinpath(i)
            for i in search_result
            if Path(IMAGEPATH).joinpath(i).exists
            ]
        if len(folders) != len(search_result):
            console.hud_alert('数据库出错，请更新', 'error')
        if DOWNLOADS_ORDER_METHOD == 'gid':
            key=lambda f: int(f.name[:f.name.find('_')])
        elif DOWNLOADS_ORDER_METHOD == 'st_mtime':
            key = lambda f: f.stat().st_mtime
        folders = sorted(
            folders, 
            key=key,
            reverse=True
            )
        t = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        if t.get('page'):
            page = int(t.get('page')[0])
        else:
            page = 0
        items = []
        for i in folders[page*50:page*50+50]:
            info = transfer_config(str(i.joinpath('manga_infos.json')))
            items.append(info)
        search_result = 'Showing {} results'.format(len(folders))
        return dict(
            items=items,
            current_page_str=str(page + 1),
            total_pages_str=str(math.ceil(len(folders)/50)),
            search_result=search_result,
            favcat_nums_titles=None
            )

    if url_category == 'downloads':
        return get_storageview_dict(url)
    else:
        return get_listview_dict(url)


def listview(url=None):
    v = ui.load_view('gui/listview.pyui')
    v.xdid_load(url)
    v.present('fullscreen',hide_title_bar=True)

    
if __name__ == '__main__':
    listview()
