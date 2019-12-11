import json
import os
import re
import shutil
from pathlib import Path

from conf.config import COOKIE_FILE, IMAGEPATH, CACHEPATH
from core.utility import verify_url, generate_tag_translator_json
from core.database import create_db, insert_info
import parse.exhentaiparser as exhentaiparser

VERSION = '1.7'
l = os.listdir(IMAGEPATH)

def update_infos():
    n = 1
    for i in l:
       # print(n)
        p = os.path.join(IMAGEPATH, i, 'manga_infos.json')
        infos = json.loads(open(p).read())
        foldername = verify_url(infos['url'])
        if foldername != i:
            print(i)
            continue
        parser = exhentaiparser.ExhentaiParser(
            cookies_dict=json.loads(open(COOKIE_FILE).read())
                )
        image_path = os.path.abspath(parser.storage_path)
        dl_path = os.path.join(image_path, foldername)
        thumbnails_dl_path = os.path.join(dl_path, 'thumbnails')
        if not os.path.exists(thumbnails_dl_path):
            os.mkdir(thumbnails_dl_path)
        manga_infos_file = os.path.join(image_path, foldername, 'manga_infos.json')
        if infos['version'] != VERSION:
            try:
                infos = parser.get_gallery_infos_mpv(infos['url'])
                parser.save_mangainfo(infos, dl_path)
            except:
                print('fail:' + i)
        n += 1


def rebuild_db():
    create_db()
    for i in Path(IMAGEPATH).iterdir():
        if len(list(i.iterdir())) > 2:
            info = json.loads(i.joinpath('manga_infos.json').open().read())
            insert_info(info)

def all_init():
    create_db()
    shutil.rmtree(IMAGEPATH)
    shutil.rmtree(CACHEPATH)
    os.makedirs(IMAGEPATH)
    os.makedirs(CACHEPATH)
    

def fix_infos():
    parser = exhentaiparser.ExhentaiParser(
        cookies_dict=json.loads(open(COOKIE_FILE).read())
            )
    n = 1
    for i in l:
       # print(n)
        p = os.path.join(IMAGEPATH, i, 'manga_infos.json')
        infos = json.loads(open(p).read())
        foldername = verify_url(infos['url'])
        image_path = os.path.abspath(parser.storage_path)
        dl_path = os.path.join(image_path, foldername)
        infos['url'] = infos['url'].replace('e-hentai', 'exhentai')
        parser.save_mangainfo(infos, dl_path)
        

def update_ehtagtranslator_json():
    generate_tag_translator_json()
    
def rm_cache():
    shutil.rmtree(CACHEPATH)
    os.mkdir(CACHEPATH)
    for i in Path(IMAGEPATH).iterdir():
        if len(list(i.iterdir())) == 2:
            print(i)
            shutil.rmtree(str(i))
    
if __name__ == '__main__':
    #rebuild_db()
    #update_infos()
    #all_init()
    #fix_infos()
    update_ehtagtranslator_json()
    #rm_cache()
