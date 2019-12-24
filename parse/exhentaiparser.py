import json
import os
import re
import shutil
import threading
import urllib.parse
from io import BytesIO
from PIL import Image

import requests
from bs4 import BeautifulSoup


VERSION = '1.7'

DEFAULT_TIMEOUT = 20
DEFAULT_STORAGE_PATH = 'image'

url_login = 'https://forums.e-hentai.org/index.php?act=Login&CODE=01'
url_ehentai = 'https://e-hentai.org/'
url_exhentai = 'https://exhentai.org/'
url_exhentai_config = 'https://exhentai.org/uconfig.php'
url_api = 'https://exhentai.org/api.php'

COOKIE_FILE = os.path.join(os.path.split(os.path.realpath(__file__))[0], 'cookie.json')
CONFIGPATH = os.path.join(os.path.split(os.path.realpath(__file__))[0], 'account.json')

semaphore = threading.BoundedSemaphore(5)

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

def verify_url(url):
    "验证url是否合法，若合法返回foldername"
    right_format = r'https://e[-x]hentai\.org/g/(\d*)/(\w*)/?'
    if not re.fullmatch(right_format, url):
        raise Exception('url有误')
    else:
        a, b = re.fullmatch(right_format, url).groups()
        return a + '_' + b

class ExhentaiParser:
    def __init__(self, **options):
        self.username = options.get('username')
        self.password = options.get('password')
        cookies_dict = options.get('cookies_dict')
        if cookies_dict:
            self.cookies = requests.utils.cookiejar_from_dict(cookies_dict)
        else:
            self.cookies = None
        httpproxy = options.get('httpproxy')
        if httpproxy:
            self.proxies = {
                'http': 'http://' + httpproxy,
                'https': 'http://' + httpproxy
                    }
        else:
            self.proxies = None
        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"
        self.headers = {"user-agent": user_agent}
        self.storage_path = options.get('storage_path', DEFAULT_STORAGE_PATH)
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)
        self.timeout = options.get('timeout', DEFAULT_TIMEOUT)
        self.session = requests.Session()
        self.session.proxies = self.proxies
        self.session.headers = self.headers
        if self.cookies:
            self.session.cookies = self.cookies

# 基础函数
    def get_soup(self, url):
        return BeautifulSoup(self.session.get(url).text, 'html5lib')

# 3个与cookies相关的函数
    def is_valid_cookies(self):
        r = self.session.get(url_exhentai)
        if not r.ok:
            return
        if r.content[:9] != b'<!DOCTYPE':
            return
        return True

    def renew_cookies(self):
        cookies_dict = requests.utils.dict_from_cookiejar(self.session.cookies)
        cookies_json = json.dumps(cookies_dict, indent=2)
        with open(COOKIE_FILE, 'w') as f:
            f.write(cookies_json)

    def login(self):
        data = {
            'CookieDate': '1',
            'b': 'd',
            'bt': '1-1',
            'UserName': self.username,
            'PassWord': self.password,
            'ipb_login_submit': 'Login!'
            }
        headers = {
            'cache-control': "no-cache",
            'content-type': "application/x-www-form-urlencoded",
            'referer': "https://e-hentai.org/bounce_login.php?b=d&bt=1-1"
            }
        headers.update(self.headers)
        self.session.post(url_login, data=data, headers=headers)
        self.session.get(url_ehentai)
        self.session.get(url_exhentai)
        self.session.get(url_exhentai_config)
        self.session.get(url_exhentai)

# 与设置相关的函数
    def set_listview(self):
        self.session.get('https://exhentai.org/?inline_set=dm_l')

    def set_thumbnailsview(self):
        self.session.get('https://exhentai.org/?inline_set=dm_t')

    def set_normalpicview(self):
        self.session.get('https://exhentai.org/g/1215584/e28b7dd4c5/?inline_set=ts_m')

    def set_extendedview(self):
        # 对抓取数据最友好，请选择
        self.session.get('https://exhentai.org/?inline_set=dm_e')
        
    def set_favorites_use_favorited(self):
        self.session.get('https://exhentai.org/favorites.php?inline_set=fs_f')

    def set_favorites_use_posted(self):
        self.session.get('https://exhentai.org/favorites.php?inline_set=fs_p')

# 提取list页信息
    def get_list_infos(self, list_url):
        """
        必须在view_type为Extended时才能使用

        Args：
        list_url  对list_url不加验证

        Returns：
        entries
        current_page   此处返回的是页面上所写的current_page，但是真正用于url时需要减1
        total_pages
        """
        def judge_view(soup):
            # 返回列表模式，需要的是Extended
            return soup.select("#dms option[selected]")[0].text
            
        def extract_info(soup):
            items = []
            for i in soup.select("table.itg.glte > tbody > tr"):
                thumbnail_url = i.select("td.gl1e > div > a > img")[0]['src']
                category = i.select("td.gl2e > div > div.gl3e > div")[0].text.lower()
                # 下面的同时得到posted和favourite的信息
                posted_div = i.select("td.gl2e > div > div.gl3e > div")[1]
                posted = posted_div.text
                if posted_div.s:
                    visible = "No"
                else:
                    visible = "Yes"
                favcat_title = posted_div.get('title')
                favcat_style = posted_div.get('style')
                if favcat_style:
                    favcat_color = favcat_style[13:17]
                    favcat = get_favcat_from_color(favcat_color)
                else:
                    favcat = None
                if 'irb' in i.select('td.gl2e > div > div.gl3e > div.ir')[0].get('class'):
                    is_personal_rating = True
                else:
                    is_personal_rating = False
                # 下面三个联动得出近似的rank
                star_style = i.select('td.gl2e > div > div.gl3e > div.ir')[0]['style']
                tmp = re.match(r'background-position:-?(\d{1,2})px -?(\d{1,2})px; ?opacity:[0-9\.]*', star_style).groups()
                rating = str((5-int(tmp[0])/16)-int(tmp[1])//21*0.5)
                uploader = i.select("div.gl3e a")[0].text
                length = re.match(r'(\d*) page', i.select("div.gl3e > div")[4].text).groups()[0]
                url = i.select("td.gl1e > div a")[0]['href']
                title = i.select("div.gl4e.glname > div")[0].text
                taglist = {}
                if i.find('table'):
                    for tr in i.find('table').find_all('tr'):
                        taglist[tr.find_all('td')[0].text[:-1]] = [x.text for x in tr.find_all('td')[1].find_all('div')]
                items.append(dict(
                    thumbnail_url=thumbnail_url,
                    category=category,
                    posted=posted,
                    rating=rating,
                    display_rating=rating,
                    is_personal_rating=is_personal_rating,
                    uploader=uploader,
                    length=length,
                    url=url,
                    title=title,
                    favcat=favcat,
                    favcat_title=favcat_title,
                    visible=visible,
                    taglist=taglist
                    ))
            return items
        
        soup = self.get_soup(list_url)
        items = extract_info(soup)
        if soup.select('table.ptt'):
            # page_str可能是'\d+-\d+'的模式，所以是不能在此处转为整数的
            # page_str和构造url用的page参数的关系是：
            # 若page_str为'\d+'，page = int(page_str) - 1
            # 若page_str为'\d+-\d+'，当前page为第一个数字减1，
            # 下一页page为第二个数字-1+1
            # 但是跳转是可用的，可以跳转到任意page
            current_page_str = soup.select('table.ptt td.ptds')[0].text
            total_pages_str = soup.select('table.ptt td')[-2].text
        else:
            # 此处为了兼容popular
            current_page_str = '1'
            total_pages_str = '1'
        # 仅在favorites页面发挥作用
        if soup.select('div.ido div.nosel'):
            favcat_nums_titles = []
            for i, v in enumerate(soup.select('div.ido div.nosel > .fp')[:10]):
                t = v.find_all('div')
                favcat_nums_titles.append(('favcat'+str(i), t[0].text, t[-1].text))
        else:
            favcat_nums_titles = None
        if soup.find('a', href='https://exhentai.org/favorites.php?inline_set=fs_f'):
            favorites_order_method = 'Posted'
        elif soup.find('a', href='https://exhentai.org/favorites.php?inline_set=fs_p'):
            favorites_order_method = 'Favorited'
        else:
            favorites_order_method = None
        if soup.select('p.ip'):
            search_result = soup.select('p.ip')[0].text
        else:
            # 兼容popular
            search_result = 'Showing {} results'.format(len(items))
        return dict(
            items=items,
            current_page_str=current_page_str,
            total_pages_str=total_pages_str,
            favcat_nums_titles=favcat_nums_titles,
            favorites_order_method = favorites_order_method,
            search_result=search_result
            )
        
    def get_list_infos_all(self, list_url):
        tmp = self.get_list_infos(list_url)
        current_page = tmp['current_page_str']
        total_pages = tmp['total_pages_str']
        items = tmp['items']
        up = urllib.parse.urlparse(list_url)
        querydict = dict(urllib.parse.parse_qsl(up.query))
        urls = []
        for n in range(total_pages):
            querydict.update(page=n)
            new_query = urllib.parse.urlencode(querydict)
            urls.append(up._replace(query=new_query).geturl())
        all_items = []
        for i, v in enumerate(urls):
            if i == current_page - 1:
                all_items.append(items)
            else:
                all_items.append(self.get_list_infos(v)['items'])
        return all_items

# 整合下面的全部内容的下载打包函数
    def download_gallery(self, gallery_url, output_path=None, dl_path=None):
        infos = self.get_gallery_infos_mpv(gallery_url)
        if dl_path is None:
            dl_path = os.path.join(self.storage_path, infos['filename'])
        self.save_mangainfo(infos, dl_path)
        self.start_download_mpv(infos['pics'], dl_path)
        if output_path:
            if not os.path.exists(output_path):
                os.makedirs(output_path)
            if len(os.listdir(dl_path)) - 1 != int(infos['length']):
                print('Failed:', infos['filename'])
                shutil.move(dl_path, output_path)
            else:
                zip_basename = os.path.join(output_path, infos['filename'])
                shutil.make_archive(zip_basename, 'zip', root_dir=dl_path)
                shutil.rmtree(dl_path)

# 提取gallery页的信息
    def get_gallery_infos_mpv(self, gallery_url):
        "提取全部信息的整合，需要两次网络访问，需要账号开通Multi-Page Viewer权限"
        infos = self.get_gallery_infos_only(gallery_url)
        pics = self.extract_page_urls_mpv(gallery_url)
        infos.update(pics=pics)
        return infos

    def get_gallery_infos_only(self, gallery_url, full_comments=True):
        "只提取gallery的信息"
        if full_comments:
            gallery_url_hc = urllib.parse.urlparse(gallery_url)._replace(query='hc=1').geturl()
            soup0 = self.get_soup(gallery_url_hc)
        else:
            soup0 = self.get_soup(gallery_url)
        pics = self.extract_thumbnail_urls(soup0)
        infos = self.extract_manga_infos(soup0)
        comments = self.extract_comments(soup0)
        filename = infos['gid'] + '_' + infos['token']
        infos.update(url=gallery_url, pics=pics, comments=comments, filename=filename, version=VERSION)
        return infos

    def extract_page_urls_mpv(self, gallery_url):
        "服务于get_gallery_infos_mpv"
        mpv_url = gallery_url.replace('/g/', '/mpv/')
        soup = self.get_soup(mpv_url)
        t = soup.find_all('script')[1].text
        gid = re.search(r'var gid=(\d*);', t).group(1)
        mpvkey = re.search(r'var mpvkey = \"(\w*)\";', t).group(1)

        t = t[t.find('['):t.find(']')+1]
        t = json.loads(t)
        number_of_digits = len(str(len(t)))

        return [
            dict(
                img_id='{:0>{n}}'.format(i+1, n=number_of_digits),
                key=v['k'],
                page=i+1,
                img_name=v['n'],
                thumbnail_url=v['t'],
                gid=gid,
                mpvkey=mpvkey
                )
            for i, v in enumerate(t)
            ]

    def extract_manga_infos(self, soup):
        "服务于get_gallery_infos_only"
        manga_infos = {}
        manga_infos['thumbnail_url'] = re.search(r'\((.*)\)', soup.find(id='gd1').div['style']).groups()[0]
        manga_infos['english_title'] = soup.find('h1', id='gn').text
        manga_infos['japanese_title'] = soup.find('h1', id='gj').text
        manga_infos['category'] = soup.find(id='gdc').text
        manga_infos['uploader'] = soup.find(id='gdn').text
        manga_infos['number of reviews'], manga_infos['rating'] = re.match(r'Rating:(\d*)Average: ([\d\.]*)', soup.find(id='gdr').text).groups()
        
        taglist = {}
        # 对于没有任何tag的gallery，taglist可以正常的返回空dict
        for i in soup.find(id='taglist').find_all('tr'):
            taglist[i.find_all('td')[0].text[:-1]] = [x.text for x in i.find_all('td')[1].find_all('div')]
        manga_infos['taglist'] = taglist
        manga_infos_temp = {}
        for i in soup.find(id='gdd').find_all('tr'):
            manga_infos_temp[i.find_all('td')[0].text[:-1]] = i.find_all('td')[1].text
        manga_infos['posted'] = manga_infos_temp.get('Posted')
        manga_infos['parent'] = manga_infos_temp.get('Parent')
        if manga_infos['parent'] != 'None':
            manga_infos['parent_url'] = soup.find(id='gdd').find(string='Parent:').parent.next_sibling.a.get('href')
        else:
            manga_infos['parent_url'] = None
        manga_infos['visible'] = manga_infos_temp.get('Visible')
        manga_infos['language'] = manga_infos_temp.get('Language')
        manga_infos['file size'] = manga_infos_temp.get('File Size')
        manga_infos['length'] = re.match(r'(\d*) page', manga_infos_temp.get('Length')).groups()[0]
        manga_infos['favorited'] = manga_infos_temp.get('Favorited')
        if soup.find('div', id='gdf').a.text == ' Add to Favorites':
            manga_infos['favcat'] = None
            manga_infos['favcat_title'] = None
        else:
            manga_infos['favcat'] = 'favcat' + str(int(re.search(r'background-position:0px -(\d+)px', soup.select('#gdf div.i')[0].get('style')).groups()[0])//19)
            manga_infos['favcat_title'] = soup.select('#gdf')[0].text.strip()

        t = soup.select('script')[1].get_text()
        manga_infos['gid'] = re.search(r'var gid = (\w+);', t).groups()[0]
        manga_infos['token'] = re.search(r'var token = "(\w+)";', t).groups()[0]
        manga_infos['apiuid'] = re.search(r'var apiuid = (\w+);', t).groups()[0]
        manga_infos['apikey'] = re.search(r'var apikey = "(\w+)";', t).groups()[0]
        manga_infos['display_rating'] = re.search(r'var display_rating = ([\d\.]+);', t).groups()[0]
        
        if 'irb' in soup.select('#rating_image')[0].get('class'):
            manga_infos['is_personal_rating'] = True
        else:
            manga_infos['is_personal_rating'] = False
        if soup.find(id='gnd'):
            manga_infos['newer_versions'] = [
                (a.get('href'), a.text, a.next_sibling.title()[8:])
                for a in soup.find(id='gnd').find_all('a')
                ]
        else:
            manga_infos['newer_versions'] = None

        manga_infos['thumbnails_total_pages'] = soup.select('.ptt td')[-2].text
        return manga_infos

    def extract_comments(self, soup):
        "从soup中提取评论，没有评论会返回空列表，服务于get_gallery_infos_only"
        comment_blocks = soup.select("#cdiv > div.c1")
        comments = []
        for block in comment_blocks:
            posted_time = re.match(r'Posted on (.*UTC)',block.select('.c3 ')[0].text).groups(1)[0]
            commenter = block.select('.c3 > a')[0].text
            if block.select('.c4 > a') and block.select('.c4 > a')[0].has_attr('name'): # 上传者评论
                is_uploader = True
                score = None
                comment_id = None
                votes = None
                is_self_comment = False
                voteable = False
                my_vote = None
            else:
                is_uploader = False
                score = block.select('.c5 > span')[0].text
                comment_id = block.select('.c6')[0].get('id')[8:]
                votes = block.select('.c7')[0].text
                if not block.select('.c4'): # 不可投票的普通评论
                    is_self_comment = False
                    voteable = False
                    my_vote = None
                elif len(block.select('.c4 > a')) == 1: # 自己发表的评论
                    is_self_comment = True
                    voteable = False
                    my_vote = None
                else: # 可投票的评论
                    is_self_comment=False
                    voteable=True
                    if block.select('.c4 > a')[0]['style']:
                        my_vote = 1
                    elif block.select('.c4 > a')[1]['style']:
                        my_vote = -1
                    else:
                        my_vote = None

            comment_div = str(block.select('.c6')[0])
            comments.append(dict(
                posted_time=posted_time,
                commenter=commenter,
                comment_id=comment_id,
                is_uploader=is_uploader,
                comment_div=comment_div,
                score=score,
                votes=votes,
                is_self_comment=is_self_comment,
                voteable=voteable,
                my_vote=my_vote
                ))
        return comments

    def extract_thumbnail_urls(self, soup):
        "从soup中提取thumbnail_urls，服务于get_gallery_infos_only"
        pic_blocks = soup.select('#gdt > div.gdtl')
        return [
            dict(
                img_id=block.img['alt'],
                img_name=re.match(r'Page \d+: (.*)', block.img['title']).groups(1)[0],
                img_url=block.a['href'],
                thumbnail_url=block.img['src']
                )
            for block in pic_blocks
            ]

# 收藏相关
    def get_favcat_favnote(self, gallery_url):
        format = r'https://e[-x]hentai\.org/g/(\d*)/(\w*)/?'
        gid, t = re.fullmatch(format, gallery_url).groups()
        querystring = {"gid": gid, "t": t, "act": "addfav"}
        url = urllib.parse.urlunparse(('https', 'exhentai.org', 'gallerypopups.php', '', urllib.parse.urlencode(querystring), ''))
        soup = self.get_soup(url)
        input_selected = soup.find('input',checked='checked')
        if input_selected:
            favcat_selected = 'favcat' + soup.find('input',checked='checked').get('id')[3]
        else:
            favcat_selected = None
        if soup.select('input#favdel'):
            is_favorited = True
        else:
            is_favorited = False
        return {
            'favcat_titles': [{'favcat': 'favcat' + str(i), 'title': v.text.strip()} for i, v in enumerate(soup.select('div.nosel > div')[:10])],
            'favcat_selected': favcat_selected,
            'favnote': soup.find('textarea').text,
            'is_favorited': is_favorited
            }
        
    def add_fav(self, gallery_url, favcat='favcat0', favnote=None, old_is_favorited=False):
        headers = {'content-type': "application/x-www-form-urlencoded"}
        url = "https://exhentai.org/gallerypopups.php"
        format = r'https://e[-x]hentai\.org/g/(\d*)/(\w*)/?'
        gid, t = re.fullmatch(format, gallery_url).groups()
        querystring = {"gid": gid, "t": t, "act": "addfav"}
        if old_is_favorited:
            apply_string = 'Apply Changes'
        else:
            apply_string = 'Add to Favorites'
        if favcat == 'favdel':
            favcat_string = 'favdel'
        else:
            favcat_string = favcat[6]
        payload = {'favcat': favcat_string, 'favnote': favnote, 'apply': apply_string, 'update': '1'}
        self.session.request("POST", url, data=payload, params=querystring, headers=headers)

# api操作
    def rate_gallery(self, rating, apikey, apiuid, gid, token):
        rating = str(int(float(rating)*2))
        headers = {'content-type': "application/json"}
        payload = {
            "method": "rategallery",
            "apikey": apikey,
            "apiuid": apiuid,
            "gid": gid,
            "rating": rating,
            "token": token
            }
        self.session.request("POST", url_api, data=json.dumps(payload), headers=headers)

    def get_pic_api_response(self, gid, key, mpvkey, page):
        headers = {'content-type': "application/json"}
        payload = {
            "method": "imagedispatch",
            "gid": gid,
            "page": page,
            "imgkey": key,
            "mpvkey": mpvkey
            }
        r = self.session.request("POST", url_api, data=json.dumps(payload), headers=headers)
        return r.json()

    def get_pic_url(self, gid, key, mpvkey, page):
        response = self.get_pic_api_response(gid, key, mpvkey, page)
        pic_url = response.get('i')
        if not pic_url:
            raise Exception('网络错误')
        return pic_url

    def get_original_image(self, gid, key, mpvkey, page):
        response = self.get_pic_api_response(gid, key, mpvkey, page)
        fullimg_url = urllib.parse.urljoin(url_exhentai, response.get('lf'))
        return self.session.get(fullimg_url).content

    def post_new_comment(self, gallery_url, text):
        # 最少10个字符（utf-8编码）
        if len(text.encode('utf-8')) < 10:
            raise ValueError('comment is too short')
        payload = {"commenttext_new": text}
        headers = {
            'content-type': "application/x-www-form-urlencoded"
            }
        headers.update(self.headers)
        r = self.session.post(gallery_url, data=payload, headers=headers)
        if r.text[:9] != '<!DOCTYPE':
            return True
        
    def get_edit_comment(self, apikey, apiuid, gid, token, comment_id):
        payload = {
            "method": "geteditcomment",
            "apiuid": apiuid,
            "apikey": apikey,
            "gid": gid,
            "token": token,
            "comment_id": comment_id
            }
        r = self.session.request("POST", url_api, data=json.dumps(payload))
        text = r.json()['editable_comment']
        soup = BeautifulSoup(text, 'html5lib')
        return soup.textarea.text

    def post_edited_comment(self, gallery_url, comment_id, text):
        if len(text.encode('utf-8')) < 10:
            raise ValueError('comment is too short')
        payload = {"edit_comment": comment_id, "commenttext_edit": text}
        headers = {
            'content-type': "application/x-www-form-urlencoded"
            }
        headers.update(self.headers)
        r = self.session.post(gallery_url, data=payload, headers=headers)
        if r.text[:9] != '<!DOCTYPE':
            return True
        
    def vote_comment(self, apikey, apiuid, gid, token, comment_id, comment_vote):
        payload = {
            "method": "votecomment",
            "apiuid": apiuid,
            "apikey": apikey,
            "gid": gid,
            "token": token,
            "comment_id": comment_id,
            "comment_vote": comment_vote
            }
        r = self.session.request("POST", url_api, data=json.dumps(payload))
        if r.ok and not r.json().get('error'):
            return True
        else:
            return False

# 下载相关
    def save_mangainfo(self, infos, dl_path):
        if not os.path.exists(dl_path):
            os.makedirs(dl_path)
        t = json.dumps(infos, sort_keys=True, indent=2)
        open(os.path.join(dl_path, 'manga_infos.json'), 'w').write(t)
    
    def start_download_pic_normal(self, fullpath_url_pairs, dl_path, start=True):
        "通用的下载图片函数，只需要fullpath和url的tuple，以及dl_path"
        if not os.path.exists(dl_path):
            os.makedirs(dl_path)
        
        thread_list = []

        for fullpath, url in fullpath_url_pairs:
            if not os.path.exists(fullpath):
                t = threading.Thread(
                    target=self.download_pic_normal_middle,
                    args=(fullpath, url, self.timeout)
                    )
                thread_list.append(t)
        if start:
            for i in thread_list:
                i.start()
        else:
            return thread_list
                    
    def start_download_mpv(self, pics, dl_path, start=True):
        "多线程下载图片，为manga_infos.json的pics设计"
        def does_exist(img_id, dl_path):
            for i in os.listdir(dl_path):
                if os.path.splitext(i)[0] == img_id:
                    return True

        if not os.path.exists(dl_path):
            os.makedirs(dl_path)
        
        thread_list = []

        for pic in pics:
            if not does_exist(pic['img_id'], dl_path):
                t = threading.Thread(
                    name='pic_mpv_{}'.format(pic['img_id']),
                    target=self.download_pic_mpv_middle,
                    args=(pic['gid'], pic['mpvkey'], pic['page'], pic['key'], pic['img_id'], dl_path, self.timeout)
                    )
                thread_list.append(t)
        if start:
            for i in thread_list:
                i.start()
        else:
            return thread_list

    def download_pic_mpv_middle(self, gid, mpvkey, page, key, img_id, dl_path, timeout):
        with semaphore:
            url = self.get_pic_url(gid, key, mpvkey, page)
            img_extname = os.path.splitext(urllib.parse.urlparse(url).path)[1]
            img_name = img_id + img_extname
            fullpath = os.path.join(dl_path, img_name)
            self.download_pic(fullpath, url, timeout, use_cookies=False)
    
    def start_download_thumbnails(self, pics, dl_path, start=True):
        "为Pythonista专门设计的下载函数，用于下载thumbnails"
        if not os.path.exists(dl_path):
            os.makedirs(dl_path)
            
        thread_list = []

        for pic in pics:
            img_extname = os.path.splitext(urllib.parse.urlparse(pic['thumbnail_url']).path)[1]
            img_name = pic['img_id'] + img_extname
            fullpath = os.path.join(dl_path, img_name)
            if not os.path.exists(fullpath):
                t = threading.Thread(
                    name='pic_thumbnail_{}'.format(pic['img_id']),
                    target=self.download_pic_normal_middle,
                    args=(fullpath, pic['thumbnail_url'], self.timeout)
                    )
                thread_list.append(t)
        if start:
            for i in thread_list:
                i.start()
        else:
            return thread_list
    
    def download_pic_normal_middle(self, fullpath, url, timeout):
        with semaphore:
            self.download_pic(fullpath, url, timeout)
    
    def download_pic(self, fullpath, url, timeout, use_cookies=True):
        def download(src, session, use_cookies=True):
            try:
                if use_cookies:
                    r = session.get(src, timeout=timeout)
                else:
                    r = requests.get(src, timeout=timeout)
            except:
                return
            if not r.ok:
                return
            return r.content
        img_bytes = download(url, self.session, use_cookies=use_cookies)
        if not img_bytes:
            return
        try:
            Image.open(BytesIO(img_bytes))
        except:
            return
        else:
            with open(fullpath, 'wb') as f:
                f.write(img_bytes)
            return fullpath


def renew():
    config = json.loads(open(CONFIGPATH).read())
    username = config['username']
    password = config['password']
    httpproxy = None

    lp = ExhentaiParser(
        username=username,
        password=password,
        httpproxy=httpproxy
            )
    lp.login()
    lp.renew_cookies()

def renew_account(username, password):
    config = {'username': username, 'password': password}
    with open(CONFIGPATH, 'w') as f:
        f.write(json.dumps(config, indent=2))

def download_pics(url, dl_path=None):
    foldername = verify_url(url)
    parser = ExhentaiParser(
        cookies_dict=json.loads(open(COOKIE_FILE).read())
            )
    image_path = os.path.abspath(parser.storage_path)
    dl_path = os.path.join(image_path, foldername)
    manga_infos_file = os.path.join(image_path, foldername, 'manga_infos.json')
    if os.path.exists(manga_infos_file):
        infos = json.loads(open(manga_infos_file).read())
    else:
        infos = parser.get_gallery_infos_mpv(url)
        parser.save_mangainfo(infos, dl_path)
    parser.start_download_mpv(infos['pics'], dl_path)
    return dl_path, manga_infos_file

    
def parse_list(url):
    parser = ExhentaiParser(
        cookies_dict=json.loads(open(COOKIE_FILE).read())
            )
    return parser.get_list_infos(url)

if __name__ == '__main__':
    # url = 'https://exhentai.org/?f_search=artist%3A%22katsurai+yoshiaki%24%22'
    url = 'https://exhentai.org/g/1421451/bb480bf764/'
    # download_thumbnail(url)
    renew()
