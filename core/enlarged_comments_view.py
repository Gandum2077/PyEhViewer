import console
import dialogs
import ui

import html2text

import conf.global_variables as glv

html2text_engine = html2text.HTML2Text()
html2text_engine.ignore_images = True

class EnlargedCommentsView (ui.View):
    def __init__(self, info, **kwargs):
        self.background_color = 'white'
        self.info = info
        self.width = kwargs.get('width', 600)
        self.height = kwargs.get('height', 800)
        self.name = 'Comments'
        self.right_button_items = [ui.ButtonItem(title='New', action=self.post_new_comment)]
        self.refresh()
    
    def refresh(self):
        if self['scrollview']:
            self.remove_subview(self['scrollview'])
        self.add_subview(ui.ScrollView(
            frame=(0, 0, self.width, self.height),
            name='scrollview'
            ))
        y = 0
        for i in self.info['comments']:
            v = CommentView(
                i,
                self.info.get('apikey'),
                self.info.get('apiuid'),
                self.info.get('gid'),
                self.info.get('token'),
                self.info.get('url'),
                width=self.width)
            v.y = y
            y += v.height
            self['scrollview'].add_subview(v)
        self['scrollview'].content_size = (self.width, y)
    
    def post_new_comment(self, sender):
        text = dialogs.text_dialog()
        if text:
            try:
                glv.PARSER.post_new_comment(self.info.get('url'), text)
            except:
                console.hud_alert('Error', 'error')
            else:
                info = glv.PARSER.get_gallery_infos_only(self.info.get('url'))
                self.info.update(comments=info['comments'])
                self.refresh()
        
class CommentView (ui.View):
    def __init__(self, comment, apikey, apiuid, gid, token, url, **kwargs):
        self.comment = comment
        self.apikey = apikey
        self.apiuid = apiuid
        self.gid = gid
        self.token = token
        self.url = url
        self.width = kwargs.get('width', 600)
        self.height = kwargs.get('height', 64)
        self.add_subview(ui.Label(
            background_color='#c8c7cc',
            frame=(0, 0, self.width, 32),
            name='label_title',
            font=('<system>', 15)
            ))
        self.add_subview(ui.Button(
            action=self.voteup,
            hidden=True,
            name='button_voteup',
            tint_color='black',
            title='Vote+'
            ))
        self['button_voteup'].frame = (self.width - 180, 0, 80, 32)
        self.add_subview(ui.Button(
            action=self.votedown,
            hidden=True,
            name='button_votedown',
            tint_color='black',
            title='Vote-'
            ))
        self['button_votedown'].frame = (self.width - 90, 0, 80, 32)
        self.add_subview(ui.Button(
            action=self.edit_post,
            hidden=True,
            name='button_edit',
            #tint_color='black',
            title='Edit'
            ))
        self['button_edit'].frame = (self.width - 135, 0, 80, 32)
        self.add_subview(ui.TextView(
            editable=False,
            frame=(0, 32, self.width, self.height - 32),
            name='textview',
            scroll_enabled=False
            ))
        self.refresh()
    
    def init(self):
        self['button_edit'].hidden = True
        self['button_voteup'].hidden = True
        self['button_votedown'].hiden = True
        self['button_voteup'].tint_color = 'black'
        self['button_votedown'].tint_color = 'black'
        
    def refresh(self):
        self.init()
        
        if self.comment['is_uploader']:
            c4text = 'uploader'
        elif self.comment['score']:
            c4text = self.comment['score']
        else:
            c4text = ''
        label_text = self.comment['posted_time'] + ' by ' + self.comment['commenter'] + ', ' + c4text
        self['label_title'].text = label_text
        
        if self.comment.get('is_self_comment'):
            self['button_edit'].hidden = False
        if self.comment.get('voteable'):
            self['button_voteup'].hidden = False
            self['button_votedown'].hidden = False
            my_vote = self.comment.get('my_vote')
            if my_vote == 1:
                self['button_voteup'].tint_color = 'blue'
            if my_vote == -1:
                self['button_votedown'].tint_color = 'blue'
        comment_text = html2text_engine.handle(self.comment['comment_div']).strip()
        self['textview'].text = comment_text
        self['textview'].size_to_fit()
        self['textview'].width = self.width
        self['textview'].height = max(self['textview'].height, 64)
        self.height = self['textview'].height + 32
    
    def voteup(self, sender):
        glv.PARSER.vote_comment(self.apikey, self.apiuid, self.gid, self.token, self.comment['comment_id'], '1')
        if sender.tint_color == ui.parse_color('black'):
            sender.tint_color = 'blue'
        elif sender.tint_color == ui.parse_color('blue'):
            sender.tint_color = 'black'
        self['button_votedown'].tint_color = 'black'
    
    def votedown(self, sender):
        glv.PARSER.vote_comment(self.apikey, self.apiuid, self.gid, self.token, self.comment['comment_id'], '-1')
        if sender.tint_color == ui.parse_color('black'):
            sender.tint_color = 'blue'
        elif sender.tint_color == ui.parse_color('blue'):
            sender.tint_color = 'black'
        self['button_voteup'].tint_color = 'black'
        
    def edit_post(self, sender):
        old_text = self['textview'].text
        text = dialogs.text_dialog(text=old_text)
        if text and text != old_text:
            glv.PARSER.post_edited_comment(self.url, self.comment['comment_id'], text)
            self['textview'].text = text
