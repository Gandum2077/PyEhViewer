import json
import os
import shutil
from pathlib import Path

import dialogs

from conf.config import IMAGEPATH, CACHEPATH
from core.utility import generate_tag_translator_json
from core.database import create_db, insert_info


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


def update_ehtagtranslator_json():
    generate_tag_translator_json()
    print('完成')


def rm_cache():
    shutil.rmtree(CACHEPATH)
    os.mkdir(CACHEPATH)
    for i in Path(IMAGEPATH).iterdir():
        if len(list(i.iterdir())) == 2:
            print(i)
            shutil.rmtree(str(i))

def transfer_to_v2():
    import datetime
    import time
    for i in Path(IMAGEPATH).iterdir():
        print(str(i))
        t = i.stat().st_mtime
        tt = datetime.datetime.utcfromtimestamp(t).isoformat()
        info = json.loads(i.joinpath('manga_infos.json').open().read())
        info['create_time'] = tt
        if info.get('version'):
            del info['version']
        text = json.dumps(info, indent=2, sort_keys=True)
        with open(str(i.joinpath('manga_infos.json')), 'w', encoding='utf-8') as f:
            f.write(text)
    rebuild_db()
        
        
    
def show_dialogs():
    items = [
        {
            "index": 0,
            "title": '全部重置',
            "action": all_init
        },
        {
            "index": 1,
            "title": '修复数据库',
            "action": rebuild_db
        },
        {
            "index": 2,
            "title": '删除缓存',
            "action": rm_cache
        },
        {
            "index": 3,
            "title": '升级标签翻译',
            "action": update_ehtagtranslator_json
        },
        {
            "index": 4,
            "title": '迁移到2.0',
            "action": transfer_to_v2
        }
    ]
    result = dialogs.list_dialog(
        title='troublefix',
        items=list(map(lambda x: x['title'], items)),
        multiple=False
        )
    if result:
        action = next(filter(lambda x: x['title'] == result, items))['action']
        action()


if __name__ == '__main__':
    show_dialogs()
