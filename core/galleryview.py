import json
import math
import os
import shutil
import threading
from pathlib import Path

import clipboard
import console
import dialogs
import ui
import webbrowser

import html2text

from conf.config import IMAGEPATH
import conf.global_variables as glv
from core.database import insert_info, delete_by_gid, search
from core.enlarged_comments_view import EnlargedCommentsView
from core.mpv import mpv, InfoView
from core.rating_stars_view import render_rating_stars_view
from core.tagtableview import TagTableView
from core.utility import get_coordinate, get_bilingual_taglist, get_color, get_color_from_favcat, verify_url, get_diamond


class GalleryView(ui.View):
    def __init__(self):
        self.update_interval = 1
        self.translated = True
        
    def did_load(self):
        self['button_try_import_old_version'].action = self.try_import_old_version
        self['button_update'].action = self.update_gallery_version
        self['button_info'].action = self.present_infoview
        self['button_safari'].action = self.open_safari_button
        self['button_share'].action = self.share_button
        self['button_refresh'].action = self.refresh_button
        self['button_close_view'].action = self.close_view
    
    def layout(self):
        self['gallery_info_view'].width = self.width - 57 - 16
        self['gallery_info_view'].refresh()
        self['scrollview'].width = self.width - 57 - 16
        self['scrollview']['comments_view'].width = self['scrollview'].width
        self['scrollview']['full_tagtable_view'].width = self['scrollview'].width
        self['scrollview']['full_tagtable_view'].refresh()
        self['scrollview']['thumbnails_view'].width = self['scrollview'].width
        self['scrollview']['thumbnails_view'].refresh()
        self['scrollview']['comments_view'].y = self['scrollview']['full_tagtable_view'].height
        self['scrollview']['thumbnails_view'].y = self['scrollview']['full_tagtable_view'].height + self['scrollview']['comments_view'].height
        self['scrollview'].frame = (16, 276, self.width - 57 - 16, self.height - 276)
        self['scrollview'].content_size = (
            self.width - 57 - 16, 
            (self['scrollview']['full_tagtable_view'].height
            + self['scrollview']['comments_view'].height
            + self['scrollview']['thumbnails_view'].height)
            )
        
        
    def will_close(self):
        """功能：
        - 将阅读过的gallery存入db
        - 更新manga_infos.json
        """
        if len(list(Path(IMAGEPATH).joinpath(verify_url(self.info['url'])).iterdir())) > 2:
            insert_info(self.info)
        glv.PARSER.save_mangainfo(self.info, self.dl_path)
        
    def update(self):
        """功能：
        - 控制下载thumbnails
        """
        if self.on_screen and self.thread_list:
            c = threading.active_count()
            if c <= 30:
                thread_list_start = self.thread_list[:30-c]
                self.thread_list = self.thread_list[30-c:]
                for i in thread_list_start:
                    i.start()

    def xdid_load(self, url):
        """功能：
        - 伪全局变量self.url, self.dl_path, self.info
        - 下载列表
        - 启动self.refresh()
        """
        self.url = url
        self.dl_path, self.info = self._get_info(self.url)
        self.thread_list = glv.PARSER.start_download_thumbnails(self.info['pics'], os.path.join(self.dl_path, 'thumbnails'), start=False)
        self.refresh()
        
    def refresh(self):
        """功能：
        - 基于self.info和self.dl_path构建页面
        """
        if self['scrollview']:
            self.remove_subview(self['scrollview'])
        if self['gallery_info_view']:
            self.remove_subview(self['gallery_info_view'])
            
        self.add_subview(self._render_gallery_info_view())
        self.add_subview(self._render_scrollview())
        
        if self.info.get('parent_url') and len(os.listdir(self.dl_path)) == 2:
            self['button_try_import_old_version'].hidden = False
        else:
            self['button_try_import_old_version'].hidden = True
            if self.info.get('newer_versions'):
                self['button_update'].new_url = self.info.get('newer_versions')[-1][0]
                self['button_update'].hidden = False
            else:
                self['button_update'].hidden = True
        
    def _get_info(self, url, refresh=False):
        foldername = verify_url(url)
        dl_path = os.path.join(IMAGEPATH, foldername)
        manga_infos_file = os.path.join(dl_path, 'manga_infos.json')
        if not refresh and os.path.exists(manga_infos_file):
            info = json.loads(open(manga_infos_file).read())
        else:
            info = glv.PARSER.get_gallery_infos_mpv(url)
            glv.PARSER.save_mangainfo(info, dl_path)
        return dl_path, info
            
    def _render_gallery_info_view(self):
        v = ui.load_view('gui/gallery_info_view.pyui')
        v.frame = (16, 18, self.width - 57 - 16, 257)
        v.xdid_load(self.info, self.dl_path)
        v['button_start_mpv'].action = self.start_mpv
        v['button_favorite'].action = self.favorite
        v['button_rate_gallery'].action = self.rate_gallery
        v['button_select_uploader'].action = self.select_uploader
        return v
        
    def _render_scrollview(self):
        full_tagtable_view = self._render_full_tagtable_view()
        comments_view = self._render_comments_view()
        thumbnails_view = self._render_thumbnails_view()
        scrollview = ui.ScrollView(
            name='scrollview'
            )
        comments_view.y = full_tagtable_view.height
        thumbnails_view.y = full_tagtable_view.height + comments_view.height
        scrollview.add_subview(full_tagtable_view)
        scrollview.add_subview(comments_view)
        scrollview.add_subview(thumbnails_view)
        scrollview.frame = (16, 276, self.width - 57 - 16, self.height - 276)
        scrollview.content_size = (self.width, full_tagtable_view.height + comments_view.height + thumbnails_view.height)
        return scrollview
        
    def _render_full_tagtable_view(self):
        v = FullTagTableView(self.info, self.translated)
        v['button_translate'].action = self.change_translated
        v['button_copy'].action = self.copy_selected_label
        return v
        
    def _render_comments_view(self):
        v = CommentsView(self.info)
        v['button_enlarge'].action = self.present_enlarged_comments
        return v
    
    def _render_thumbnails_view(self):
        v = ThumbnailsView(self.info, self.dl_path)
        return v
    
    def favorite(self, sender):
        t = glv.PARSER.get_favcat_favnote(self.info['url'])
        favcat_selected = t['favcat_selected']
        favcat_titles = t['favcat_titles']
        favnote = t['favnote']
        is_favorited = t['is_favorited']
        self.old_is_favorited = is_favorited
        v = ui.load_view('gui/favorite.pyui')
        v.xdid_load(favcat_titles, favcat_selected, favnote, is_favorited)
        v['button_confirm'].action = self.confirm_favorite
        v.present('sheet', hide_title_bar=True)
        
    def confirm_favorite(self, sender):
        if len(sender.superview['textview1'].text.encode('utf-8')) > 200:
            console.hud_alert('Favorite Notes超字数限制', 'error')
        else:
            t = sender.superview.new_favcat_selected
            try:
                glv.PARSER.add_fav(
                    self.info['url'],
                    favcat=t,
                    favnote=sender.superview['textview1'].text,
                    old_is_favorited=self.old_is_favorited
                )
            except:
                console.hud_alert('失败', 'error')
            else:
                if t != 'favdel':
                    self.info['favcat'] = t
                    self.info['favcat_title'] = sender.superview['tableview1'].data_source.items[sender.superview['tableview1'].selected_row[1]]['title']
                    self['gallery_info_view']['label_favorite_title'].background_color = get_color_from_favcat(self.info['favcat'])
                    self['gallery_info_view']['label_favorite_title'].text = self.info['favcat_title']
                    self['gallery_info_view']['label_favorite_title'].text_color = 'white'
                else:
                    self.info['favcat'] = None
                    self.info['favcat_title'] = None
                    self['gallery_info_view']['label_favorite_title'].background_color = 'white'
                    self['gallery_info_view']['label_favorite_title'].text = '未收藏'
                    self['gallery_info_view']['label_favorite_title'].text_color = 'black'
                glv.PARSER.save_mangainfo(self.info, os.path.join(glv.PARSER.storage_path, verify_url(self.info['url'])))
                sender.superview.close()
                
    def rate_gallery(self, sender):
        if self.info['is_personal_rating']:
            rating = self.info['display_rating']
        else:
            rating = self.info['rating']
        v = ui.load_view('gui/rategallery.pyui')
        v.xdid_load(rating)
        v['button_confirm'].action = self.confirm_rate_gallery
        v.present('sheet', hide_title_bar=True)
        
    def confirm_rate_gallery(self, sender):
        rating = sender.superview['label1'].text
        try:
            glv.PARSER.rate_gallery(rating, self.info['apikey'], self.info['apiuid'], self.info['gid'], self.info['token'])
        except:
            console.hud_alert('失败', 'error')
        else:
            self.info['is_personal_rating'] = True
            self.info['display_rating'] = rating
            self['gallery_info_view'].refresh()
            glv.PARSER.save_mangainfo(self.info, os.path.join(glv.PARSER.storage_path, verify_url(self.info['url'])))
            sender.superview.close()
    
    def select_uploader(self, sender):
        if not sender.superview['label_uploader'].selected:
            sender.superview['label_uploader'].background_color = 'grey'
            sender.superview['label_uploader'].selected = True
        else:
            sender.superview['label_uploader'].background_color = 'white'
            sender.superview['label_uploader'].selected = False
    
    def start_mpv(self,sender):
        mpv(url=self.info['url'], page=0)
        
    def change_translated(self, sender):
        self.translated = not self.translated
        self['scrollview']['full_tagtable_view'].change_translated()
        self['scrollview']['comments_view'].y = self['scrollview']['full_tagtable_view'].height
        self['scrollview']['thumbnails_view'].y = self['scrollview']['full_tagtable_view'].height + self['scrollview']['comments_view'].height
        self['scrollview'].frame = (16, 276, self.width - 57 - 16, self.height - 276)
        self['scrollview'].content_size = (
            self.width - 57 - 16, 
            (self['scrollview']['full_tagtable_view'].height
            + self['scrollview']['comments_view'].height
            + self['scrollview']['thumbnails_view'].height)
            )
        
    def copy_selected_label(self, sender):
        texts = []
        t = self['scrollview']['full_tagtable_view']['tagtableview'].get_selected()
        if t:
            for i in t:
                if i[1].find('|') != -1:
                    tag = i[1][:i[1].find('|')].strip()
                else:
                    tag = i[1]
                if i[0] != 'misc':
                    if tag.find(' ') != -1:
                        texts.append('{}:"{}$"'.format(i[0], tag))
                    else:
                        texts.append('{}:{}$'.format(i[0], tag))
                else:
                    if tag.find(' ') != -1:
                        texts.append('"{}$"'.format(tag))
                    else:
                        texts.append('{}$'.format(tag))
        if self['gallery_info_view']['label_uploader'].selected:
            texts.append(self['gallery_info_view']['label_uploader'].text.replace('uploader: ', 'uploader:'))
        if texts:
            clipboard.set(' '.join(texts))
            console.hud_alert('已复制标签')
        else:
            console.hud_alert('没选中任何标签', 'error')
        
    def present_enlarged_comments(self, sender):
        info = glv.PARSER.get_gallery_infos_only(self.url)
        self.info.update(comments=info['comments'])
        v = EnlargedCommentsView(self.info)
        v.present('sheet')
    
    def try_import_old_version(self, sender):
        def escape(keyword):
            keyword = keyword.replace("/", "//")
            keyword = keyword.replace("'", "''")
            keyword = keyword.replace("[", "/[")
            keyword = keyword.replace("]", "/]")
            keyword = keyword.replace("%", "/%")
            keyword = keyword.replace("&","/&")
            keyword = keyword.replace("_", "/_")
            keyword = keyword.replace("(", "/(")
            keyword = keyword.replace(")", "/)")
            return keyword
        parent_url = self.info.get('parent_url')
        foldername = verify_url(parent_url)
        if os.path.exists(os.path.join(IMAGEPATH, foldername)):
            old_dl_path, old_info = self._get_info(parent_url)
        else:
            clause = """SELECT DISTINCT gid||'_'||token
            FROM downloads
            WHERE uploader='{}'
            AND english_title='{}'
            AND gid < {}
            ORDER BY gid DESC
            LIMIT 1
            """
            clause = clause.format(
                escape(self.info.get('uploader')),
                escape(self.info.get('english_title')),
                self.info.get('gid')
                )
            print(clause)
            t = [i[0] for i in search(clause)]
            if t:
                old_dl_path = os.path.join(IMAGEPATH, t[0])
                manga_infos_file = os.path.join(old_dl_path, 'manga_infos.json')
                old_info = json.loads(open(manga_infos_file).read())
            else:
                console.hud_alert('未找到旧版本', 'error')
                return
        self.thread_list.clear()
        imgid_extname_dict = dict([
            os.path.splitext(i)
            for i in os.listdir(old_dl_path)
            if i not in ['manga_infos.json', 'thumbnails']
            ])
        old_pics = dict([
            (i['key'], (i['img_id'], imgid_extname_dict[i['img_id']]))
            for i in old_info['pics']
            if i['img_id'] in imgid_extname_dict
            ])
        new_pics = dict([
            (i['key'], i['img_id'])
            for i in self.info['pics']
            ])
        for key in set(old_pics.keys()) & set(new_pics.keys()):
            old_path = os.path.join(old_dl_path, old_pics[key][0] + old_pics[key][1])
            new_path = os.path.join(self.dl_path, new_pics[key] + old_pics[key][1])
            if os.path.exists(old_path) and not os.path.exists(new_path):
                shutil.move(old_path, new_path)
            old_thumbnail_path = os.path.join(old_dl_path, 'thumbnails', old_pics[key][0] + '.jpg')
            new_thumbnail_path = os.path.join(self.dl_path, 'thumbnails', new_pics[key] + '.jpg')
            if os.path.exists(old_thumbnail_path) and not os.path.exists(new_thumbnail_path):
                shutil.move(old_thumbnail_path, new_thumbnail_path)
        delete_by_gid(old_info['gid'])
        shutil.rmtree(old_dl_path)
        self.thread_list = glv.PARSER.start_download_thumbnails(self.info['pics'], os.path.join(self.dl_path, 'thumbnails'), start=False)
            
    def update_gallery_version(self, sender):
        if hasattr(sender, 'new_url'):
            url = sender.new_url
            old_info = self.info
            old_dl_path = self.dl_path
            dl_path, info = self._get_info(url)
            if not os.path.exists(os.path.join(dl_path, 'thumbnails')):
                os.mkdir(os.path.join(dl_path, 'thumbnails'))
            imgid_extname_dict = dict([
                os.path.splitext(i)
                for i in os.listdir(old_dl_path)
                if i not in ['manga_infos.json', 'thumbnails']
                ])
            old_pics = dict([
                (i['key'], (i['img_id'], imgid_extname_dict[i['img_id']]))
                for i in old_info['pics']
                if i['img_id'] in imgid_extname_dict
                ])
            new_pics = dict([
                (i['key'], i['img_id'])
                for i in self.info['pics']
                ])
            for key in set(old_pics.keys()) & set(new_pics.keys()):
                old_path = os.path.join(old_dl_path, old_pics[key][0] + old_pics[key][1])
                new_path = os.path.join(self.dl_path, new_pics[key] + old_pics[key][1])
                if os.path.exists(old_path) and not os.path.exists(new_path):
                    shutil.move(old_path, new_path)
                old_thumbnail_path = os.path.join(old_dl_path, 'thumbnails', old_pics[key][0] + '.jpg')
                new_thumbnail_path = os.path.join(dl_path, 'thumbnails', new_pics[key] + '.jpg')
                if os.path.exists(old_thumbnail_path) and not os.path.exists(new_thumbnail_path):
                    shutil.move(old_thumbnail_path, new_thumbnail_path)
            self.dl_path = dl_path
            self.url = url
            self.info = info
            self.thread_list = glv.PARSER.start_download_thumbnails(self.info['pics'], os.path.join(self.dl_path, 'thumbnails'), start=False)
            self.refresh()
            delete_by_gid(old_info['gid'])
            shutil.rmtree(old_dl_path)
            console.hud_alert('已完成')
    
    def present_infoview(self, sender):
        info_view = InfoView(self.info)
        info_view.present('popover') 

    @ui.in_background
    def open_safari_button(self, sender):
        webbrowser.get('safari').open(self.info['url'])
        
    @ui.in_background
    def share_button(self, sender):
        if self.info['japanese_title']:
           title = self.info['japanese_title']
        else:
           title = self.info['english_title']
        dialogs.share_text(title + '\n' + self.info['url'])

    def refresh_button(self, sender):
        # 此处并不会重启thumbnail的下载，只会刷新info
        self.dl_path, self.info = self._get_info(self.url, refresh=True)
        self.refresh()
        console.hud_alert('已更新')
        
    def close_view(self, sender):
        self.close()

class CommentsView (ui.View):
    def __init__(self, info, width=None):
        if width:
            self.width = width
        else:
            self.width = 768 - 57 - 16
        self.border_color = '#efeff4'
        self.border_width = 1
        self.frame = (0, 0, self.width, 150)
        self.name = 'comments_view'
        self.info = info
        button_enlarge = ui.Button(
            #action=self.present_enlarged_comments,
            flex='L',
            frame=(self.width - 50 + 8, 75 - 16, 32, 32),
            image=ui.Image.named('iob:arrow_expand_32'),
            name='button_enlarge'
            )
        textview_comments = ui.TextView(
            background_color='white',
            flex='WR',
            frame=(0, 0, self.width - 50, 150),
            font=('<system>', 12),
            editable=False,
            name='textview_comments',
            text=self.get_comments_text()
            )
        line = ui.View(
            background_color='#efeff4',
            flex='L',
            frame=(self.width - 50, 0, 1, 150)
            )
        self.add_subview(textview_comments)
        self.add_subview(button_enlarge)
        self.add_subview(line)
        
    def refresh(self):
        self['textview_comments'].text = self.get_comments_text()
        
    def get_comments_text(self):
        comments_text = []
        html2text_engine = html2text.HTML2Text()
        html2text_engine.ignore_images = True
        for i in self.info['comments']:
            if i['is_uploader']:
                c4text = 'uploader'
            elif i['score']:
                c4text = i['score']
            else:
                c4text = ''
            text = i['posted_time'] + ' by ' + i['commenter'] + ', ' + c4text + '\n\n' + html2text_engine.handle(i['comment_div']).strip()
            comments_text.append(text)
        sep = '\n\n' + '—' * 30 + '\n'
        comments_text = sep.join(comments_text)
        return comments_text
        

class FavoriteView (ui.View):
    def __init__(self):
        self.new_favcat_selected = None
    
    def xdid_load(self, favcat_titles, favcat_selected, favnote, is_favorited):
        self.background_color = '#efeff4'
        l = ui.ListDataSource([])
        l.items = [
            {'title': list(i.values())[0],
            'image': get_diamond(get_color_from_favcat(list(i.keys())[0])),
            'accessory_type':'none'}
            for i in favcat_titles
            ]
        if is_favorited:
            l.items.append({
                'title': '取消收藏',
                'image': 'iob:close_32',
                'accessory_type':'none'
            })
        self['tableview1'].height = 32*len(l.items)
        l.delete_enabled = False
        l.action = self.set_new_favcat_selected
        if is_favorited and favcat_selected:
            self['tableview1'].selected_row = (0, int(favcat_selected[6]))
            self.new_favcat_selected = favcat_selected
        self['tableview1'].scroll_enabled = False
        self['tableview1'].data_source = l
        self['tableview1'].delegate = l
        self['textview1'].text = favnote
        self['button_close'].action = self.close_view
    
    def close_view(self, sender):
        self.close()
    
    def set_new_favcat_selected(self, sender):
        if self['tableview1'].selected_row[1] <= 9:
            self.new_favcat_selected = 'favcat' + str(self['tableview1'].selected_row[1])
        else:
            self.new_favcat_selected = 'favdel'

class FullTagTableView (ui.View):
    def __init__(self, info, translated, width=None):
        if width:
            self.width = width
        else:
            self.width = 768 - 57 - 16
        self.border_color = '#efeff4'
        self.border_width = 1
        self.name = 'full_tagtable_view'
        self.info = info
        self.translated = translated
        # tagtableview的装饰view
        line = ui.View(
            background_color='#efeff4',
            flex='HL',
            frame=(self.width - 50, 0, 1, self.height)
            )
        button_translate = ui.Button(
            #action=self.change_translated,
            flex='TBL',
            image=ui.Image.named('gui/translate_icon.png'),
            name='button_translate'
            )
        button_translate.frame = (self.width - 50 + 8, self.height * 0.25 - 16, 32, 32)
        button_copy = ui.Button(
            #action=self.copy_selected_label,
            flex='TBL',
            frame=(self.width - 50 + 8, self.height * 0.75 - 16, 32, 32),
            image=ui.Image.named('iob:ios7_copy_32'),
            name='button_copy'
            )
        self.add_subview(button_translate)
        self.add_subview(button_copy)
        self.add_subview(line)
        self.refresh()
        
    def refresh(self):
        if self['tagtableview']:
            self.remove_subview(self['tagtableview'])
        tagtableview = TagTableView(
            get_bilingual_taglist(self.info['taglist']),
            translated=self.translated,
            width=self.width - 2 - 50
            )
        self.height = max(tagtableview.height, 94) + 6
        tagtableview.frame = (1, 3, self.width - 2 - 50, tagtableview.height)
        tagtableview.name = 'tagtableview'
        self.add_subview(tagtableview)
        self.frame = (0, 0, self.width, self.height)
        
    def change_translated(self):
        self.translated = not self.translated
        self.refresh()
        
            
class GalleryInfoView (ui.View):
    def __init__(self):
        #self.flex = 'WHLRTB'
        self.update_interval = 0.1
        self.loading_flag = True
        
    def update(self):
        if self.loading_flag:
            try:
                self._load_slide()
            except AttributeError:
                pass
        
    def xdid_load(self, info, dl_path):
        self.dl_path = dl_path
        self.info = info
        x, y, w, h = self['thumbnail_location_view'].frame
        self.add_subview(ui.ActivityIndicator(
            name='indicator',
            center=(w/2 + x, h/2 + y)
            ))
        self.refresh()
        
    def refresh(self):
        if self['rating_stars_view']:
            self.remove_subview(self['rating_stars_view'])
        self['label_japanese_title'].text = self.info.get('japanese_title')
        self['label_english_title'].text = self.info.get('english_title')
        self['label_url'].text = self.info.get('url')
        self['label_category'].text, self['label_category'].background_color = get_color(self.info['category'].lower())
        self['label_length'].text = self.info["length"] + ' pages'
        self['label_posted'].text = 'posted: ' + self.info["posted"]
        self['label_uploader'].text = 'uploader: ' + self.info["uploader"]
        self['label_favorite_num'].text = 'favorited: ' + self.info['favorited']
        self['label_language'].text = self.info['language']
        self['label_filesize'].text = self.info['file size']
        
        x, y, w, h = self['rating_location_view'].frame
        if self.info['is_personal_rating']:
            rating = self.info['display_rating']
            personal = True
        else:
            rating = self.info['rating']
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
        self['button_rate_gallery'].bring_to_front()
        
        self['label_review'].text = self.info['rating'] + ' on ' + self.info['number of reviews'] + ' reviews'
        if self.info.get('favcat'):
            self['label_favorite_title'].background_color = get_color_from_favcat(self.info['favcat'])
            self['label_favorite_title'].text = self.info['favcat_title']
            self['label_favorite_title'].text_color = 'white'
        self._load_slide()
            
    def _get_pic_path(self):
        p = os.path.join(self.dl_path, 'thumbnails', self.info['pics'][0]['img_id']+'.jpg')
        if os.path.exists(p):
            return p
        else:
            return 'loading'

    def _load_slide(self):
        pic_path = self._get_pic_path()
        if pic_path != 'loading':
            image = ui.Image.named(pic_path)
            w1, h1 = image.size
            x, y, w, h = self['thumbnail_location_view'].frame
            self['imageview_thumbnail1'].frame = get_coordinate(x, y, w, h, w1, h1)
            self['imageview_thumbnail1'].image = image
            self['indicator'].stop()
            self.loading_flag = False
        else:
            self['indicator'].start() 
            self.loading_flag = True
    
class RateGalleryView (ui.View):
    def __init__(self):
        self.update_interval = 0.1
        
    def xdid_load(self, rating):
        self['button_cancel'].action = self.close_view
        self['slider1'].value = float(rating)/5
    
    def close_view(self, sender):
        self.close()
    
    def update(self):
        self['label1'].text = str((int(self['slider1'].value*9)+1)/2)
        
        
class ThumbnailView (ui.View):
    """长宽固定为(139, 213)
    """
    def __init__(self, img_id, img_path, url):
        self.update_interval = 0.1
        self.img_path = img_path
        self.url = url
        self.page = int(img_id) - 1
        self.add_subview(ui.ImageView(name='imageview'))
        self.add_subview(ui.Label(
            name='label',
            frame=(0,195,158,18),
            font=('<system>', 12),
            alignment=ui.ALIGN_CENTER,
            text=img_id
            ))
        self.add_subview(ui.ActivityIndicator(
            name='indicator',
            center=(69, 97)
            ))
        self.add_subview(ui.Button(
            frame=(0, 0, 139, 195),
            action=self.start_mpv
            ))
        self.loading_flag = True
        self.refresh()

    def update(self):
        if self.loading_flag:
            try:
                self.refresh()
            except AttributeError:
                pass
    
    def refresh(self):
        self._load_slide()
    
    def start_mpv(self,sender):
        mpv(url=self.url, page=self.page)
        
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
            self['imageview'].frame = get_coordinate(1, 0, 137, 195, w1, h1)
            self['imageview'].image = image
            self['indicator'].stop()
            self.loading_flag = False
        else:
            self['indicator'].start() 
            self.loading_flag = True
                
class ThumbnailsView (ui.View):
    def __init__(self, info, dl_path):
        self.background_color = '#efeff4'
        self.frame = (0, 0, 695, 500)
        self.name = 'thumbnails_view'
        self.info = info
        self.dl_path = dl_path
        self.locate()
        
    def locate(self):
        nums_in_a_row = self.width // 139
        if nums_in_a_row <= 1:
            raise Exception('the width of thumbnailsview is too small')
        interval_width = (self.width % 139) / (nums_in_a_row - 1)
        for n, pic in enumerate(self.info['pics']):
            p = os.path.join(self.dl_path, 'thumbnails', pic['img_id']+'.jpg')
            thumbnailview = ThumbnailView(pic['img_id'], p, self.info['url'])
            thumbnailview.frame = (139 * (n % nums_in_a_row) + interval_width * (n % nums_in_a_row), 213 * (n // nums_in_a_row), 139, 213)
            self.add_subview(thumbnailview)
        self.height = 213 * math.ceil(len(self.info['pics']) / nums_in_a_row)
    
    def refresh(self):
        nums_in_a_row = self.width // 139
        if nums_in_a_row <= 1:
            raise Exception('the width of thumbnailsview is too small')
        interval_width = (self.width % 139) / (nums_in_a_row - 1)
        for n, v in enumerate(self.subviews):
            v.frame = (139 * (n % nums_in_a_row) + interval_width * (n % nums_in_a_row), 213 * (n // nums_in_a_row), 139, 213)
        self.height = 213 * math.ceil(len(self.info['pics']) / nums_in_a_row)

def galleryview(url):
    v = ui.load_view('gui/galleryview.pyui')
    v.xdid_load(url)
    v.present('fullscreen',hide_title_bar=True,animated=False)
    
if __name__ == '__main__':
    url = 'https://exhentai.org/g/1421690/8879faf2a6/'
    galleryview(url)
