import os
import re
import sqlite3
import urllib.parse

from conf.config import DATABASE

def create_db():
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("""CREATE TABLE downloads (
        gid INTEGER NOT NULL, 
        token TEXT, 
        category TEXT, 
        english_title TEXT,
        japanese_title TEXT,
        length INTEGER, 
        posted TEXT, 
        rating REAL,
        uploader TEXT, 
        PRIMARY KEY(gid))""")
    c.execute("""CREATE TABLE tags (
        gid INTEGER NOT NULL, 
        class TEXT, 
        tag TEXT)""")    
    conn.commit()
    conn.close()

def insert_info(info):
    gid = info.get('gid')
    values_downloads = (
        gid,
        info.get('token'),
        info.get('category'),
        info.get('english_title'),
        info.get('japanese_title'),
        info.get('length'),
        info.get('posted'),
        info.get('rating'),
        info.get('uploader')
        )
    values_keys = []
    for k, v in info['taglist'].items():
        for i in v:
            values_keys.append((gid, k, i))
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM downloads WHERE gid=?', (gid,))
        cur.execute('DELETE FROM tags WHERE gid=?', (gid,))
        cur.execute('INSERT INTO downloads VALUES (' + '?,' * (len(values_downloads) - 1) + '?)', values_downloads)
        cur.executemany('INSERT INTO tags VALUES (?,?,?)', tuple(values_keys))
        conn.commit()

def delete_by_gid(gid):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM downloads WHERE gid=?', (gid,))
        cur.execute('DELETE FROM tags WHERE gid=?', (gid,))
        conn.commit()

def search(clause):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute(clause)
        t = cur.fetchall()
    return t


def handle_querydict(querydict):
    """处理querydict，返回sql语句
    """
    def handle_f_search(text):
        query_tags = []
        query_uploader = []
        query_title = []
        text = text.strip()
        while text:
            if re.match(r'\w+:"[^ \$]+ [^ \$]+\$"', text):
                querystring = re.match(r'\w+:"[^ ]+ [^ ]+\$"', text).group()
                text = text[len(querystring):].strip()
                query_tags.append(querystring)
            elif re.match(r'\w+:[^ \$]+\$', text):
                querystring = re.match(r'\w+:[^ \$]+\$', text).group()
                text = text[len(querystring):].strip()
                query_tags.append(querystring)
            elif re.match(r'uploader:[^ ]+', text):
                querystring = re.match(r'uploader:[^ ]+', text).group()
                text = text[len(querystring):].strip()
                query_uploader.append(querystring)
            elif re.match(r'[^ ]+', text):
                querystring = re.match(r'[^ ]+', text).group()
                text = text[len(querystring):].strip()
                query_title.append(querystring)
        if len(query_uploader) > 1:
            raise ValueError('uploader不止一个')
        if len(query_title) > 3:
            raise ValueError('关键词超过3个')
        for i in query_title:
            if len(i.encode('utf-8')) < 3:
                raise ValueError('存在过短的关键词')
        return query_title, query_uploader, query_tags

    cat_sequence = ['Misc', 'Doujinshi', 'Manga', 'Artist CG', 'Game CG', 'Image Set', 'Cosplay', 'Asian Porn', 'Non-H', 'Western']
    condition_clauses = []
    f_search = querydict.get('f_search') # 关键词
    f_cats = querydict.get('f_cats') # 排除的分类
    advsearch = querydict.get('advsearch') #是否启用高级选项，若否下面改为默认选项
    if advsearch:
        f_sname = querydict.get('f_sname') # 是否搜索name
        f_stags = querydict.get('f_stags') # 是否搜索tag
        f_srdd = querydict.get('f_srdd') #评分
        f_sp = querydict.get('f_sp') # 是否搜索页数
    else:
        f_sname = 'on'
        f_stags = 'on'
        f_srdd = None
        f_sp = None
    if f_search:
        query_title, query_uploader, query_tags = handle_f_search(f_search)
        if query_tags and f_stags:
            for i in query_tags:
                condition_clauses.append("EXISTS (SELECT tags.gid FROM tags WHERE downloads.gid=tags.gid AND tags.class='{}' AND tags.tag='{}')".format(i[:i.find(':')], re.match(r'^"?(.*)\$"?',i[i.find(':') + 1:]).groups()[0]))
        if query_uploader:
            condition_clauses.append("downloads.uploader='{}'".format(query_uploader[0][9:]))
        if query_title and f_sname:
            for i in query_title:
                condition_clauses.append("(downloads.japanese_title like '%{}%' OR downloads.english_title like '%{}%')".format(i, i))
    if f_cats:
        nums = '{:0>10}'.format(str(bin(int(f_cats)))[2:])
        filtered_cat = [cat for cat, n in zip(reversed(cat_sequence), nums) if n == '1']
        condition_clauses.append("downloads.category NOT IN ('{}')".format("', '".join(filtered_cat)))
    if f_srdd:
        condition_clauses.append("downloads.rating>={}".format(f_srdd))
    if f_sp:
        f_spf = querydict.get('f_spf', '1') # 起始页数
        f_spt = querydict.get('f_spt') # 结束页数
        if not re.fullmatch(r'\d+', f_spf):
            f_spf = 1
        if f_spt and not re.fullmatch(r'\d+', f_spt):
            f_spt = None
        if f_spt:
            condition_clauses.append("({} < downloads.length AND downloads.length < {})".format(f_spf, f_spt))
        else:
            condition_clauses.append("{} < downloads.length".format(f_spf))
    if condition_clauses:
        where_clause = ' WHERE ' + ' AND '.join(condition_clauses)
    else:
        where_clause = ''
    return "SELECT DISTINCT downloads.gid||'_'||downloads.token FROM downloads" + where_clause


def search_by_url(url):
    querydict = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(url).query))
    clause = handle_querydict(querydict)
    foldernames = [i[0] for i in search(clause)]
    return foldernames

