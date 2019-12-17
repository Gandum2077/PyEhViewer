import os
import sys

from parse.exhentaiparser import CONFIGPATH, COOKIE_FILE
from core.welcome import welcome


if __name__ == '__main__':
    if not os.path.exists(CONFIGPATH) or not os.path.exists(COOKIE_FILE):
        welcome()
    else:        
        import conf.global_variables as glv
        from core.galleryview import galleryview
        from core.listview import listview
        glv.init()
        if len(sys.argv) > 1:
            gallery_url = sys.argv[1]
            galleryview(gallery_url)
        else:
            listview()
