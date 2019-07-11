import ui

from core.utility import translate_tag_type
 
# 总width为693-50, 标题占用90，其余603-50 
class TouchableLabel (ui.View):
    def __init__(self, **kwargs):
        self.touch_enabled = True
        frame = kwargs.pop('frame', (0, 0, 1000, 32))
        alignment = kwargs.pop('alignment', ui.ALIGN_CENTER)
        font = kwargs.pop('font', ('<system>', 14))
        line_break_mode = kwargs.pop('line_break_mode', ui.LB_TRUNCATE_HEAD)
        number_of_lines = kwargs.pop('number_of_lines', 0)
        text = kwargs.pop('text', 'touchable_label')
        text_color = kwargs.pop('color', 'black')
        self.text = text
        self.action = kwargs.pop('action', self.do_nothing)
        self.frame = frame
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.label = ui.Label(text=text, frame=self.frame, font=font, text_color=text_color, alignment=alignment, line_break_mode=line_break_mode, number_of_lines=number_of_lines)
        self.add_subview(self.label)
        
    def do_nothing(self, *args):
        pass
     
    def touch_ended(self, touch):
        if (0 < touch.location[0] < self.width and
            0 < touch.location[1] < self.height):
            self.action(self)
            
    def size_to_fit(self):
        self.label.size_to_fit()
        self.frame = self.label.frame
        
    def size_to_fit_with_margin(self, margin=2):
        self.label.size_to_fit()
        x, y, w, h = self.label.frame
        self.width = w + margin * 2
        self.height = h + margin * 2
        self.label.x = x + margin
        self.label.y = y + margin
        
    def show_orginal(self):
        self.label.text = self.original_text
        
    def show_translated(self):
        self.label.text = self.translated_text

class TagsView (ui.View):
    def __init__(self, tags, translated=True, **kwargs):
        self.background_color = kwargs.get('background_color', 'white')
        self.width = kwargs.get('width', 603)
        self.tag_type = kwargs.get('tag_type')
        self.height = self.handle_tags(tags, translated=translated)
        
        
    def handle_tags(self, tags, translated=True, blank=6):
        x = 0
        y = 0
        for i in tags:
            original_text = i[0]
            translated_text = i[1]
            if translated:
                text = translated_text
            else:
                text = original_text
            t = TouchableLabel(
                text=text,
                action=touch,
                background_color=(0.741, 1.0, 0.765, 1.0),
                tag_type=self.tag_type,
                original_text=original_text,
                translated_text=translated_text
                )
            t.size_to_fit_with_margin()
            if t.width > self.width:
                raise Exception('TagTable的宽度必须大于任一个tag的宽度')
            if x + t.width <= self.width:
                t.x = x
                t.y = y
                x = x + t.width + blank
            else:
                t.x = 0
                t.y = y + t.height + blank
                x = 0 + t.width + blank
                y = y + t.height + blank
            self.add_subview(t)
        return t.y + t.height
            
class TagTableView (ui.View):
    def __init__(self, bilingual_taglist, translated=True, **kwargs):
        self.background_color = kwargs.pop('background_color', 'white')
        self.width = kwargs.pop('width', 693)
        self.height = self.handle_taglist(bilingual_taglist, translated=translated)
        #self.add_subview(ui.View(background_color='#c8c7cc', frame=(89, 0, 1, self.height)))
        
    def handle_taglist(self, bilingual_taglist, translated=True, horizontal_blank=1, vertical_blank=11):
        y = 0
        for k, v in bilingual_taglist.items():
            tagsview = TagsView(v, tag_type=k, width=self.width-90, translated=translated)
            tagsview.x = 90 + horizontal_blank
            tagsview.y = y
            self.add_subview(tagsview)
            h = tagsview.height
            if translated:
                text = translate_tag_type(k)
            else:
                text = k
            titleview = ui.Label(
                alignment=ui.ALIGN_CENTER,
                text=text, 
                height=h, 
                width=90, 
                background_color='white',
                font=('<system>', 14)
                )
            titleview.x = 0
            titleview.y = y
            self.add_subview(titleview)
            y = y + h + vertical_blank
            self.add_subview(ui.View(background_color='#c8c7cc', frame=(0, y-6, self.width, 1)))
        return y - vertical_blank
    
    def get_selected(self):
        selected = []
        for i in self.subviews:
            if isinstance(i, TagsView):
                for j in i.subviews:
                    if j.background_color == (0.5, 0.5, 0.5, 1.0):
                        selected.append((j.tag_type, j.original_text))
        return selected

def touch(sender):
    if sender.background_color == (0.741, 1.0, 0.765, 1.0):
        sender.background_color = (0.5, 0.5, 0.5, 1.0)
    else:
        sender.background_color = (0.741, 1.0, 0.765, 1.0)
