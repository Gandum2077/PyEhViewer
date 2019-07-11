import os
import sys

from parse.exhentaiparser import CONFIGPATH
from core.welcome import welcome

if not os.path.exists(CONFIGPATH):
    welcome()
        
import conf.global_variables as glv
from core.galleryview import galleryview
from core.listview import listview

if __name__ == '__main__':
    glv.init()
    if len(sys.argv) > 1:
        gallery_url = sys.argv[1]
        galleryview(gallery_url)
    else:
        listview()
