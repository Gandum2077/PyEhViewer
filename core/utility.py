import json
import math
import os
import re
import urllib.parse

import requests

try:
    import ui
except:
    pass

from conf.config import TAGTRANSLATOR_JSON

TAGTRANSLATOR_DICT = json.loads(open(TAGTRANSLATOR_JSON).read())

def get_coordinate(x, y, w, h, w1, h1):
    """在一个长方形内居中放置一个长方形(w1,h1)，求新长方形的形如(x,y,w,h)的坐标
    前提条件: w<h
    事实上只需要w1/h1，如有必要可以自行定义其中之一
    """
    if w1/h1 == w/h:
        return (x, y, w, h)
    elif w1/h1 > w/h:
        c = (h - h1/w1*w)/2
        return x, y+c, w, h-2*c
    elif w1/h1 < w/h:
        c = (w - w1/h1*h)/2
        return (x+c, y, w-2*c, h)
        
def verify_url(url):
    "验证url是否合法，若合法返回foldername"
    right_format = r'https://e[-x]hentai\.org/g/(\d*)/(\w*)/?'
    if not re.fullmatch(right_format, url):
        raise Exception('url有误')
    else:
        a, b = re.fullmatch(right_format, url).groups()
        return a + '_' + b
        
def get_color(name):
    d = {
        'misc': {'string': 'Misc', 'color': '#777777'},
        'doujinshi': {'string': 'Doujinshi', 'color': '#9E2720'},
        'manga': {'string': 'Manga', 'color': '#DB6C24'},
        'artist cg': {'string': 'Artist CG', 'color': '#D38F1D'},
        'game cg': {'string': 'Game CG', 'color': '#617C63'},
        'image set': {'string': 'Image Set', 'color': '#325CA2'},
        'cosplay': {'string': 'Cosplay', 'color': '#6A32A2'},
        'asian porn': {'string': 'Asian Porn', 'color': '#A23282'},
        'non-h': {'string': 'Non-H', 'color': '#5FA9CF'},
        'western': {'string': 'Western', 'color': '#AB9F60'}
    }
    return d[name]['string'], d[name]['color']

def get_color_from_favcat(name):
    d = {
        'favcat0': '#000',
        'favcat1': '#f00',
        'favcat2': '#fa0',
        'favcat3': '#dd0',
        'favcat4': '#080',
        'favcat5': '#9f4',
        'favcat6': '#4bf',
        'favcat7': '#00f',
        'favcat8': '#508',
        'favcat9': '#e8e'
    }
    return d[name]

def get_favcat_from_color(name):
    d = {
        '#000': 'favcat0',
        '#f00': 'favcat1',
        '#fa0': 'favcat2',
        '#dd0': 'favcat3',
        '#080': 'favcat4',
        '#9f4': 'favcat5',
        '#4bf': 'favcat6',
        '#00f': 'favcat7',
        '#508': 'favcat8',
        '#e8e': 'favcat9',
    }
    return d[name]

def generate_tag_translator_json():
    url = 'https://api.github.com/repos/EhTagTranslation/Database/releases/latest'
    info = requests.get(url).json()
    db_text_url = list(filter(lambda n: n['name'] == 'db.text.json', info['assets']))[0]['browser_download_url']
    db_text_json = requests.get(db_text_url).json()

    types_dict = {}
    for i in db_text_json['data']:
        types_dict[i['namespace']] = {k:v['name'] for k, v in i['data'].items()}

    text = json.dumps(types_dict, indent=2, sort_keys=True)
    open(TAGTRANSLATOR_JSON, 'w').write(text)

def update_tagtranslator_dict():
    global TAGTRANSLATOR_DICT
    TAGTRANSLATOR_DICT = json.loads(open(TAGTRANSLATOR_JSON).read()) 

def translate_taglist(taglist):
    def translate_key(eng):
            d = {
                'artist': '作者',
                'female': '女性',
                'male': '男性',
                'parody': '原作',
                'character': '角色',
                'group': '团队',
                'language': '语言',
                'reclass': '归类',
                'misc': '杂项'
            }
            return d[eng]
    translated_taglist = {}
    for k, v in taglist.items():
        
        translated_k = translate_key(k)
        translated_v = []
        for i in v:
            if i.find('|') != -1:
                i = i[:i.find('|')].strip()
            translated_v.append(TAGTRANSLATOR_DICT[k].get(i, i))
        translated_taglist.update({translated_k:translated_v})
    return translated_taglist
            
def render_taglist_to_text(taglist):
    def sort_func(x):
            t = x[:x.find(':')]
            return sort_sequence[t]
    sort_sequence = [
        'female', '女性',
        'male', '男性',
        'language', '语言',
        'parody', '原作',
        'character', '角色',
        'group', '团队',
        'artist', '作者',
        'misc', '杂项',
        'reclass', '归类'
        ]
    sort_sequence = dict(zip(sort_sequence, range(len(sort_sequence))))
    texts = []
    for key, value in taglist.items():
        t = key + ':    ' + ', '.join(value)
        texts.append(t)
    return '\n'.join(sorted(texts, key=sort_func))

def translate_tag_type(eng):
    d = {
        'artist': '作者',
        'female': '女性',
        'male': '男性',
        'parody': '原作',
        'character': '角色',
        'group': '团队',
        'language': '语言',
        'reclass': '归类',
        'misc': '杂项'
    }
    return d[eng]

def get_bilingual_taglist(taglist):
    """格式为{'misc':(('3d', '3D'), ...), ...}
    """
    bilingual_taglist = {}
    for k, v in taglist.items():
        bilingual_v = []
        for i in v:
            if i.find('|') != -1:
                i2 = i[:i.find('|')].strip()
            else:
                i2 = i
            translated_i = TAGTRANSLATOR_DICT[k].get(i2, i)
            bilingual_v.append((i, translated_i))
        bilingual_taglist.update({k:bilingual_v})
    return bilingual_taglist
    

def detect_url_category(url):
    "给url分类，结果为default, popular, watched, favourite, downloads"
    if url == 'https://exhentai.org/popular':
        return 'popular'
    t = urllib.parse.urlparse(url)
    if t.scheme == 'downloads':
        return 'downloads'
    if t.path == '/watched':
        return 'watched'
    elif t.path == '/favorites.php':
        return 'favorites'
    else:
        return 'default'
        
def judge_device_model():
    width, height = ui.get_screen_size()
    # 请注意此处不考虑width/height > 1.414的情况，即iPhone横屏使用识别为iPad
    if height/width > 1.414:
        return 'iPhone'
    else:
        return 'iPad'
        
def get_search_url(querydict, url_category='default'):
    if url_category == 'default':
        path = '/'
    elif url_category == 'watched':
        path = 'watched'
    elif url_category == 'favorites':
        path = 'favorites.php'
    elif url_category == 'downloads':
        path = '/'
    if url_category == 'downloads':
        scheme = 'downloads'
        netloc = 'index'
    else:
        scheme = 'https'
        netloc = 'exhentai.org'
    query = urllib.parse.urlencode(querydict)
    url = urllib.parse.urlunparse((scheme, netloc, path, '', query, ''))
    return url

def add_querydict_to_url(querydict, url):
    up = urllib.parse.urlparse(url)
    d = dict(urllib.parse.parse_qsl(up.query))
    d.update(querydict)
    query = urllib.parse.urlencode(d)
    return up._replace(query=query).geturl()
    
def get_diamond(color):
    with ui.ImageContext(100, 100) as ctx:
        ui.set_color(color)
        with ui.GState():
            ui.concat_ctm(ui.Transform.rotation(45/180*math.pi))
            a = 0.1
            ui.fill_rect((0.5+a)/math.sqrt(2)*100, (a-0.5)/math.sqrt(2)*100, math.sqrt(2)*(0.5-a)*100, math.sqrt(2)*(0.5-a)*100)
        im = ctx.get_image()
    return im

def get_round_progess_image(progress):
    with ui.ImageContext(100, 100) as ctx:
        if progress < 1:
            color = '#ffcb0f'
        elif progress == 1:
            color = '#00ff16'
        ui.set_color(color)
        path = ui.Path()
        path.line_width = 1
        path.line_join_style = ui.LINE_JOIN_ROUND
        path.line_cap_style = ui.LINE_CAP_BUTT
        path.move_to(50, 50)
        path.line_to(50, 35)
        path.add_arc(50, 50, 15, -math.pi / 2, -math.pi / 2 + math.pi * 2 * progress)
        path.line_to(50, 50)
        path.stroke()
        path.fill()
        img = ctx.get_image()
    return img
