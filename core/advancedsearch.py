import ui

from core.utility import get_diamond, get_color_from_favcat


class AdvancedSearchView (ui.View):
    def __init__(self, search_phrases, favcat_nums_titles, **kwargs):
        self.favcat_nums_titles = favcat_nums_titles
        self.background_color = 'white'
        self.update_interval = 0.1
        self.width = kwargs.get('width', 603)
        self.height = kwargs.get('height', 44*4+10+29)
        tableview1 = ui.TableView(frame=(0, 0, self.width, 44*4), name='tableview1')
        self.add_subview(tableview1)
        self.lds = ui.ListDataSource(items=search_phrases)
        self['tableview1'].data_source = self.lds
        self['tableview1'].delegate = self.lds
        segmentedcontrol1 = ui.SegmentedControl(frame=(2, 44*4+10, self.width-4, 29), name='segmentedcontrol1', segments=['Home', 'Watched', 'Favorites', 'Downloads'], action=self.show_aso)
        self.add_subview(segmentedcontrol1)
        
    def re_init(self, search_phrases, favcat_nums_titles):
        self.height = 44*4+10+29
        if self['option_view']:
            self.remove_subview(self['option_view'])
        self['segmentedcontrol1'].selected_index = -1
        self.lds.items = search_phrases
        self.favcat_nums_titles = favcat_nums_titles

    def show_aso(self, sender):
        if self['option_view']:
            self.remove_subview(self['option_view'])
        if sender.selected_index in [0, 1]:
            option_view = OptionHomeView()
        elif sender.selected_index == 2:
            option_view = OptionFavoritesView(self.favcat_nums_titles)
        elif sender.selected_index == 3:
            option_view = OptionDownloadsView()
        self.height = 550
        option_view.y = 215 + 10
        option_view.name = 'option_view'
        self.add_subview(option_view)
        
    def get_querydict(self):
        if self['option_view']:
            return self['option_view'].get_query()
        else:
            return {}

    def set_action(self, action):
        self.lds.action = action


class OptionHomeView (ui.View):
    def __init__(self):
        self.width = 603
        self.height = 335
        v = ui.load_view('gui/asv_categories.pyui')
        v.name = 'v'
        self.add_subview(v)
        v.x = 14
        v.y = 0
        v2 = ui.load_view('gui/asv_options_home.pyui')
        v2.name = 'v2'
        #v2.hidden = False
        self.add_subview(v2)
        v2.x = 101
        v2.y = 120
        button = ui.Button(
            title='高级搜索',
            image=ui.Image.named('iob:arrow_down_b_32'),
            tint_color='#6e6eff',
            action=self.show_asv,
            font=('<system>', 15),
            frame = (14, 80, 94, 32)
            )
        self.add_subview(button)

    def show_asv(self, sender):
        if self['v2'].hidden:
            self['v2'].hidden = False
            sender.image = ui.Image.named('iob:arrow_down_b_32')
        else:
            self['v2'].hidden = True
            sender.image = ui.Image.named('iob:arrow_right_b_32')

    def get_query(self):
        text = []
        if not self['v2'].hidden:
            text.append(('advsearch', '1'))
            for i in self['v2'].subviews:
                if isinstance(i, ui.Button) and i.chosen:
                    text.append((i.name, 'on'))
                elif i.name == 'f_srdd' and self['v2']['f_sr'].chosen:
                    text.append((i.name, i.selected_index+2))
                elif i.name in ['f_spf', 'f_spt']:
                    text.append((i.name, i.text))
        f_cats = 0
        for i in self['v'].subviews:
            if isinstance(i, ui.Label) and i.alpha != 1.0:
                f_cats += int(i.name[6:])
        if f_cats:
            text.append(('f_cats', f_cats))
        return dict(text)

class FavcatLabel (ui.View):
    def __init__(self, favcat, num, title, action):
        self.chosen = False
        self.width = 180
        self.height = 38
        self.favcat = favcat
        self.add_subview(ui.Label(
            frame=(3, 3, 50, 32),
            text=num,
            alignment=ui.ALIGN_RIGHT,
            font=('<system>', 16)
            ))
        self.add_subview(ui.ImageView(
            frame=(53, 3, 24, 32),
            image=get_diamond(get_color_from_favcat(favcat)),
            alignment=ui.ALIGN_LEFT,
            font=('<system>', 16)
            ))
        self.add_subview(ui.Label(
            frame=(77, 3, 100, 32),
            text=title,
            alignment=ui.ALIGN_LEFT,
            font=('<system>', 16)
            ))
        self.add_subview(ui.Button(
            frame=(0, 0, 180, 38),
            action=action
            ))

    def init_border(self):
        self.border_width = 0
        self.chosen = False

    def display_border(self):
        self.border_width = 3
        self.chosen = True

class OptionFavoritesView (ui.View):
    def __init__(self, favcat_nums_titles):
        self.width = 603
        self.height = 335
        n = 0
        y = 0
        x1 = 81
        x2 = 81*2+180
        for favcat, num, title in favcat_nums_titles:
            fl = FavcatLabel(favcat, num, title, self.change_border)
            fl.y = y
            if n < 5:
                fl.x = x1
            else:
                fl.x = x2
            n += 1
            y += 40
            if n == 5:
                y = 0
            self.add_subview(fl)
        v = ui.load_view('gui/asv_options_favorites.pyui')
        v.name = 'v'
        v.x = 81
        v.y = 220
        self.add_subview(v)

    def change_border(self, sender):
        old_chosen = sender.superview.chosen
        for i in self.subviews:
            if isinstance(i, FavcatLabel):
                i.init_border()
        if not old_chosen:
            sender.superview.display_border()

    def get_query(self):
        text = []
        for i in self['v'].subviews:
            if isinstance(i, ui.Button) and i.chosen:
                text.append((i.name, 'on'))
        for i in self.subviews:
            if isinstance(i, FavcatLabel) and i.chosen:
                text.append(('favcat', i.favcat[6]))
        return dict(text)

class OptionDownloadsView (ui.View):
    def __init__(self):
        self.width = 603
        self.height = 335
        v = ui.load_view('gui/asv_categories.pyui')
        v.name = 'v'
        self.add_subview(v)
        v.x = 14
        v.y = 0
        v2 = ui.load_view('gui/asv_options_downloads.pyui')
        v2.name = 'v2'
        #v2.hidden = False
        self.add_subview(v2)
        v2.x = 101
        v2.y = 120
        button = ui.Button(
            title='高级搜索',
            image=ui.Image.named('iob:arrow_down_b_32'),
            tint_color='#6e6eff',
            action=self.show_asv,
            font=('<system>', 15),
            frame = (14, 80, 94, 32)
            )
        self.add_subview(button)
    
    def show_asv(self, sender):
        if self['v2'].hidden:
            self['v2'].hidden = False
            sender.image = ui.Image.named('iob:arrow_down_b_32')
        else:
            self['v2'].hidden = True
            sender.image = ui.Image.named('iob:arrow_right_b_32')
            
    def get_query(self):
        text = []
        if not self['v2'].hidden:
            text.append(('advsearch', '1'))
            for i in self['v2'].subviews:
                if isinstance(i, ui.Button) and i.chosen:
                    text.append((i.name, 'on'))
                elif i.name == 'f_srdd' and self['v2']['f_sr'].chosen:
                    text.append((i.name, i.selected_index+2))
                elif i.name in ['f_spf', 'f_spt']:
                    text.append((i.name, i.text))
                elif i.name == 'order':
                    if i.selected_index == 0:
                        text.append((i.name, 'gid'))
                    else:
                        text.append((i.name, 'st_mtime'))
        f_cats = 0
        for i in self['v'].subviews:
            if isinstance(i, ui.Label) and i.alpha != 1.0:
                f_cats += int(i.name[6:])
        if f_cats:
            text.append(('f_cats', f_cats))
        return dict(text)
        
def change_color(sender):
    if sender.background_color != ui.parse_color('white'):
        sender.background_color = 'white'
        sender.chosen = False
    else:
        sender.background_color = '#ff48c2'
        sender.chosen = True

def change_alpha(sender):
    if sender.superview[sender.binding].alpha == 1.0:
        sender.superview[sender.binding].alpha = 0.5
    else:
        sender.superview[sender.binding].alpha = 1.0






