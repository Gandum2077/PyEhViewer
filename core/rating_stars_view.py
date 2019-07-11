import ui

class RatingStarsView (ui.View):
    def __init__(self):
        #self.flex = 'TBLR'
        self.width = 180
        self.height = 34
        background_view = ui.ImageView(
            flex='WH',
            frame=(0, 0, self.width, self.height),
            image=ui.Image.named('gui/fivestars_grey.png')
            )
        self.add_subview(background_view)
        upper_view = ui.View(
            flex='WH',
            frame=(0, 0, self.width, self.height),
            name='upper_view'
            )
        self.add_subview(upper_view)
        
    def set_rating(self, rating, personal=False):
        if self['upper_pic']:
            self.remove_subview(self['upper_pic'])
        if personal:
            fivestars_icon = 'gui/fivestars_blue.png'
        else:
            fivestars_icon = 'gui/fivestars.png'
        v = ui.ImageView(
            frame=(0, 0, self.width, self.height),
            image=ui.Image.named(fivestars_icon),
            name='upper_pic'
            )
        self['upper_view'].add_subview(v)
        self['upper_view'].width = self.width * (float(rating) / 5)

def render_rating_stars_view(rating, personal=False, width=180, height=34, name=None):
    v = RatingStarsView()
    v.width = width
    v.height = height
    if name:
        v.name = name
    v.set_rating(rating, personal=personal)
    return v
