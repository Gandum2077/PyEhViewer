import json
import math
import os
import threading
import time

import yaml

import console
import dialogs
import photos
import ui
import webbrowser

from conf.config import CONFIGPATH, IMAGEPATH
import conf.global_variables as glv
from core.image_with_gesture_view import ImageWithGestureView
from core.utility import verify_url, translate_taglist, render_taglist_to_text


AUTOPAGE_INTERVAL = yaml.load(open(CONFIGPATH, encoding='utf-8').read()).get('autopage_interval', 5)
NUM_OF_THREAD_AT_THE_SAME_TIME = 10

def get_max_wh():
    "此处不写死，而是用时获取，是考虑屏幕旋转的需要而预备的"
    ui_width, ui_height = ui.get_screen_size()
    max_height = ui_height - 18
    max_width = ui_width - 57
    return max_width, max_height
                                               
class MultiPageView(ui.View):
    def __init__(self):
        self.update_interval = 0.05
        # 此处不使用全局变量
        self.autopage_interval = AUTOPAGE_INTERVAL
        self.loading_flag = True
        self.flag_auto_load_next = False
    
    def did_load(self):
        self.background_color = 'white'
        # 按钮：显示信息，对应load_info
        self['button_info'].action = self.load_info
        # 按钮：刷新，对应refresh_slide
        self['button_refresh'].action = self.refresh_slide
        # 按钮：关闭，对应close_view
        self['button_close'].action = self.close_view
        # 按钮：自动翻页，对应auto_load_next
        self['button_autoload'].action = self.auto_load_next
        # 按钮：设置，对应load_setting
        self['button_setting'].action = self.load_settingview
        # 滑块：翻页
        self['slider1'].action = self.load_specified_slide_for_slider
        max_width, max_height = get_max_wh()
        self.add_subview(ui.ActivityIndicator(name='indicator', center=(max_width/2, max_height/2+18), flex='LRTB'))

    def layout(self):
        self.refresh()
    
    def touch_began(self, touch):
        pass

    def touch_ended(self, touch):
        if self.loading_flag:
            if 0 < touch.location[0] <= self.width - 57:
                if 18 < touch.location[1] <= self.height/2 + 9:
                    if self.page > 0:
                        self.page -= 1
                        self.refresh()
                elif self.height/2 + 9 < touch.location[1] <= self.height:
                    if self.length > self.page + 1:
                        self.page += 1
                        self.refresh()
        
    def update(self):
        if self.loading_flag:
            try:
                self.refresh_without_slider()
            except AttributeError:
                pass
        if self.flag_auto_load_next:
            if time.time() - self.time_last_auto_load >= self.autopage_interval:
                self.time_last_auto_load = time.time()
                if self.length > self.page + 1:
                    self.page += 1
                    self.refresh()
        if self.on_screen and self.thread_list:
            c = threading.active_count()
            n = NUM_OF_THREAD_AT_THE_SAME_TIME
            if c <= n:
                thread_list_start = self.thread_list[: n - c]
                self.thread_list = self.thread_list[n - c:]
                for i in thread_list_start:
                    i.start()
    
    def xdid_load(self, url, page=0):
        self.url = url
        # 获取info和下载列表
        self.dlpath = os.path.join(IMAGEPATH, verify_url(self.url))
        manga_infos_file = os.path.join(self.dlpath, 'manga_infos.json')
        self.infos = json.loads(open(manga_infos_file).read())
        self.thread_list = glv.PARSER.start_download_mpv(self.infos['pics'], self.dlpath, start=False)
        # 其他标记
        self.page = page # 当前页码（从0开始），核心变量
        self.length = int(self.infos['length']) # 总页码
        self['text_total_page'].text = str(self.length)
        self.thread_list.sort(key=self._sort_func) # 排序从page的页面开始下载
        self.refresh()
    
    def refresh_without_slider(self):
        self._load_slide()
        if self.flag_auto_load_next:
            self.time_last_auto_load = time.time()

    def refresh(self):
        self._load_slide()
        self['text_current_page'].text = str(self.page + 1)
        self['slider1'].value = (self.page + 1)/self.length
        if self.flag_auto_load_next:
            self.time_last_auto_load = time.time()

    def _get_pic_path(self, img_id):
        for i in os.listdir(self.dlpath):
            if os.path.splitext(i)[0] == img_id:
                self.loading_flag = False
                return os.path.join(self.dlpath, i)
        self.loading_flag = True
        return 'loading'   

    def _load_slide(self):
        if self['igv']:
            self.remove_subview(self['igv'])
        pic_path = self._get_pic_path(self.infos['pics'][self.page]['img_id'])
        if pic_path != 'loading':
            max_width, max_height = get_max_wh()
            igv = ImageWithGestureView(
                frame=(0, 18, max_width, max_height),
                image_file=pic_path,
                name='igv',
                action_prev=self.action_prev,
                action_next=self.action_next
                )
            self.add_subview(igv)
            self['indicator'].stop()
        else:
            self['indicator'].start()
    
    def _sort_func(self, x):
        page = int(x.name[8:]) - 1
        if page < self.page:
            return page + self.length
        else:
            return page
        
    def action_prev(self):
        if self.page > 0:
            self.page -= 1
            self.refresh()
            
    def action_next(self):
        if self.length > self.page + 1:
            self.page += 1
            self.refresh()
            
    def auto_load_next(self, sender):
        if not self.flag_auto_load_next:
            self.flag_auto_load_next = True
            self.time_last_auto_load = time.time()
            sender.tint_color = 'red'
        else:
            self.flag_auto_load_next = False
            sender.tint_color = None
    
    def close_view(self, sender):
        self.close()

    def load_info(self, sender):
        info_view = InfoView(self.infos)
        info_view.present('popover') 
    
    def load_specified_slide_for_slider(self, sender):
        ratio = sender.value
        now_text_num = max(1, math.ceil(ratio * self.length))
        if now_text_num != self.page + 1:
            self.page = now_text_num - 1
            self.thread_list.sort(key=self._sort_func)
            self.refresh()

    def refresh_slide(self, sender):
        #未完成张数
        unfinished_pics = int(self.infos['length']) - len(os.listdir(self.dlpath)) + 2
        # 未完成任务
        unfinished_downloads = len(self.thread_list) + len([i for i in threading.enumerate() if i.name[:7] == 'pic_mpv'])
#TO-DO: 让未完成任务不包括其他gallery或短时间内反复打开同一个gallery所生成的线程
        if unfinished_pics == 0:
            console.hud_alert('已完成')
        elif unfinished_downloads == 0:
            glv.PARSER.start_download_mpv(self.infos['pics'], self.dlpath)
            console.hud_alert('重启{}张'.format(unfinished_pics))
        else:
            # unfinished_downloads为负的临时解决方案
            console.hud_alert('当前下载未完成，还有{}张未完成，{}张已失败'.format(unfinished_pics, max(0, unfinished_pics - unfinished_downloads)), 'error')

# 以下为settings部分
    def load_settingview(self, sender):
        self.setting_view = ui.load_view('gui/setting.pyui')
        self.setting_view['slider_autopage_speed'].value = (self.autopage_interval - 1)/29
        self.setting_view['label_autopage_speed'].text = '{}'.format(self.autopage_interval)
        self.setting_view['slider_autopage_speed'].action = self.set_autopage_interval
        self.setting_view['button_share_picture'].action = self.share_picture
        self.setting_view['button_safari'].action = self.open_safari
        self.setting_view['button_refresh_infos'].action = self.refresh_infos
        self.setting_view['button_save'].action = self.save_picture
        self.setting_view['button_delete_thispage'].action = self.delete_thispage
        self.setting_view.present('sheet', hide_title_bar=False)

    def open_safari(self, sender):
        webbrowser.get('safari').open(self.url)
    
    def share_picture(self, sender):
        pic_path = self._get_pic_path(self.infos['pics'][self.page]['img_id'])
        if pic_path != 'loading':
            dialogs.share_image(ui.Image.named(pic_path))
        else:
            console.hud_alert('error', 'error')
        
    def refresh_infos(self, sender):
        self.infos = glv.PARSER.get_gallery_infos_mpv(self.url)
        glv.PARSER.save_mangainfo(self.infos, self.dlpath)
        console.hud_alert('infos已刷新')
        
    def save_picture(self, sender):
        pic_path = self._get_pic_path(self.infos['pics'][self.page]['img_id'])
        if pic_path != 'loading.jpg':
            photos.create_image_asset(pic_path)
            console.hud_alert('已保存')
        else:
            console.hud_alert('此图片不存在', 'error')
        
    def delete_thispage(self, sender):
        pic_path = self._get_pic_path(self.infos['pics'][self.page]['img_id'])
        if pic_path != 'loading.jpg':
            os.remove(pic_path)
            console.hud_alert('此图片已删除')
        else:
            console.hud_alert('此图片不存在', 'error')

    def set_autopage_interval(self, sender):
        self.autopage_interval = round(self.setting_view['slider_autopage_speed'].value * 29 + 1)
        self.setting_view['label_autopage_speed'].text = '{}'.format(self.autopage_interval)
                    
    
class InfoView(ui.View):
    def __init__(self, infos):
        self.background_color = 'white'
        self.name = 'Info'
        self.height = 500
        self.width = 320
        
        names_url = [
            infos["url"],
            infos["japanese_title"],
            infos["english_title"]
            ]
        other_tags = [
            "category: " + infos["category"],
            "uploader: " + infos["uploader"],
            "posted: " + infos["posted"],
            "language: " + infos["language"],
            "length: " + infos["length"]
            ]
        review = [
            infos["rating"] + "/5.0",
            infos["number of reviews"] + " reviews",
            infos["favorited"][:-6] + " favorites"
            ]
        names_url = '\n'.join(names_url)
        other_tags = '\n'.join(other_tags)
        review = '\n'.join(review)
        
        taglist = render_taglist_to_text(infos['taglist'])
        taglist_translated = render_taglist_to_text(translate_taglist(infos['taglist']))

        self.add_subview(ui.TextView(text=names_url, editable=False, selectable=True, frame=(0,0,self.width,100)))
        self.add_subview(ui.TextView(text=other_tags, editable=False, frame=(0,100,self.width/2,200)))
        self.add_subview(ui.TextView(text=review, editable=False, frame=(self.width/2,100,self.width/2,200)))
        self.add_subview(ui.TextView(text=taglist, editable=False, frame=(0,200,self.width/2,300)))
        self.add_subview(ui.TextView(text=taglist_translated, editable=False, frame=(self.width/2,200,self.width/2,300)))

    
def mpv(url='', page=0):
    view = ui.load_view(pyui_path='gui/mpv.pyui')
    view.xdid_load(url, page=page)
    view.present('fullscreen', hide_title_bar=True, animated=False)

if __name__ == '__main__':
    mpv()
