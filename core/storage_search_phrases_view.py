import console
import dialogs
import ui

class StorageSearchPhrasesView (ui.View):
    def __init__(self):
        self.border_width = 1
        self.border_color = '#c8c7cc'
        t = ui.TableView(
            frame=(3, 64, 314, 410),
            name='tableview'
            )
        self.add_subview(t)
        
    def did_load(self):
        self['button_edit'].action = self.edit
        
    def xdid_load(self, items, add_action, select_action):
        self['button_add'].action = add_action
        self['tableview'].data_source = MyTableViewDataSource(items=items)
        self['tableview'].delegate = MyTableViewDelegate(select_action)
        
    def edit(self, sender):
        sender.superview['tableview'].editing = not sender.superview['tableview'].editing
        
    def add_item(self, item):
        self['tableview'].data_source.items.append(item)
        self['tableview'].reload()

class MyTableViewDataSource (object):
    def __init__(self, items=[]):
        self.items = items
        
    def tableview_number_of_sections(self, tableview):
        # Return the number of sections (defaults to 1)
        return 1

    def tableview_number_of_rows(self, tableview, section):
        # Return the number of rows in the section
        return len(self.items)

    def tableview_cell_for_row(self, tableview, section, row):
        # Create and return a cell for the given section/row
        cell = ui.TableViewCell()
        if isinstance(self.items[row], dict):
            cell.text_label.text = self.items[row]['display']
            cell.accessory_type = 'detail_button'
        else:
            cell.text_label.text = self.items[row]
        return cell

    def tableview_can_delete(self, tableview, section, row):
        # Return True if the user should be able to delete the given row.
        return True

    def tableview_can_move(self, tableview, section, row):
        # Return True if a reordering control should be shown for the given row (in editing mode).
        return True

    def tableview_delete(self, tableview, section, row):
        # Called when the user confirms deletion of the given row.
        del self.items[row]
        tableview.reload()

    def tableview_move_row(self, tableview, from_section, from_row, to_section, to_row):
        # Called when the user moves a row with the reordering control (in editing mode).
        t = self.items.pop(from_row)
        self.items.insert(to_row, t)
        tableview.reload()


class MyTableViewDelegate (object):
    def __init__(self, action_select):
        self.action_select = action_select
        
    def tableview_did_select(self, tableview, section, row):
        # Called when a row was selected.
        t = tableview.data_source.items[row]
        if isinstance(t, dict):
            self.action_select(t['raw'])
        else:
            self.action_select(t)

    def tableview_title_for_delete_button(self, tableview, section, row):
        # Return the title for the 'swipe-to-***' button.
        return 'Delete'
    
    @ui.in_background
    def tableview_accessory_button_tapped(self, tableview, section, row):
        t = str(tableview.data_source.items[row]['raw'])
        console.alert(t)
        
def render_storage_search_phrases_view(items, add_action, select_action, frame=None):
    v = ui.load_view('gui/storage_search_phrases_view.pyui')
    v.frame = frame
    v.xdid_load(items, add_action, select_action)
    return v

