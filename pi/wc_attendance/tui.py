import npyscreen
import signal
import curses
from datetime import datetime

from .json_store import JsonFileStore
from .nfc import Nfc


class AttendanceSheet(npyscreen.GridColTitles):
    def __init__(self, *args, **kwargs):
        npyscreen.GridColTitles.__init__(self, *args, **kwargs)
        self.col_titles = ["Name", "Cards", "Attendance Count"]
        self.select_whole_line = True
        self.default_column_number = 3
        self.refresh_data()

    def refresh_data(self):
        curr_p = self.get_selected()
        saved_id = None if curr_p is None else curr_p.get_id()
        self.values = []
        db = self.parent.parentApp.database
        for id in db.all_person_ids():
            person = db.find_person_by_id(id)
            name = person.get_name()
            cards = person.get_cards()
            attendance = person.get_attendance()
            row = [
                name,
                "No cards" if len(cards) == 0 else
                ", ".join([hex(x) for x in cards]),
                str(len(attendance)),
                person
            ]
            self.values.append(row)
        self.values.sort(key=lambda x: x[0])
        for i in range(len(self.values)):
            if self.values[i][3].get_id() == saved_id:
                self.edit_cell[0] = i
                break

    def set_up_handlers(self):
        npyscreen.GridColTitles.set_up_handlers(self)
        self.handlers[curses.ascii.NL] = self.h_select

    def h_select(self, inpt):
        self.parent.root_menu()

    def get_selected(self):
        if self.edit_cell is None:
            return None
        row = self.values[self.edit_cell[0]]
        return row[3] if row is not None else None


class InputLinePopup(npyscreen.Popup):
    def __init__(self, title, prompt, init_value, update_func):
        self.update_func = update_func
        npyscreen.Popup.__init__(self, name=title, color="STANDOUT")
        self.wgName = self.add(npyscreen.TitleText, name=prompt,
                               value=init_value)

    def edit(self, *args, **kwargs):
        npyscreen.Popup.edit(self, *args, **kwargs)
        self.update_func(self.wgName.value)


class AttendanceDisplay(npyscreen.FormWithMenus):
    class ExitButton(npyscreen.MiniButtonPress):
        def whenPressed(self):
            self.parent.a_exit()

    FIX_MINIMUM_SIZE_WHEN_CREATED = False
    OK_BUTTON_TEXT = "Exit"
    OKBUTTON_TYPE = ExitButton

    def create(self):
        npyscreen.FormWithMenus.create(self)
        self.wMain = self.add(AttendanceSheet)
        m = self.new_menu()
        m.addItem("View Attendance", self.m_view_att)
        m.addItem("Edit Cards", self.m_edit_cards)
        m.addItem("Edit Name", self.m_edit_name)
        m.addItem("Cancel", lambda *args: None)

    def m_view_att(self, *args):
        person = self.wMain.get_selected()
        self.parentApp.getForm("ATTVIEW").value = person
        self.parentApp.switchForm("ATTVIEW")

    def m_edit_name(self, *args):
        person = self.wMain.get_selected()
        popup = InputLinePopup("Edit Name", "Name:", person.get_name(),
                               person.set_name)
        popup.edit()
        self.wMain.refresh_data()

    def m_edit_cards(self, *args):
        person = self.wMain.get_selected()
        self.parentApp.getForm("CARDVIEW").value = person
        self.parentApp.switchForm("CARDVIEW")

    def beforeEditing(self):
        self.handlers["^X"] = lambda *args: None
        self.wMain.refresh_data()

    def draw_form(self):
        npyscreen.Form.draw_form(self)

    def a_exit(self):
        self.parentApp.switchForm(None)


class AttendanceViewPerson(npyscreen.Form):
    FIX_MINIMUM_SIZE_WHEN_CREATED = False

    def create(self):
        self.value = None
        self.wgAttList = self.add(npyscreen.GridColTitles,
                                  col_titles=["Attendance"],
                                  select_whole_line=True)
        self.wgAttList.default_column_number = 1
        self.wgAttList.values = []

    def beforeEditing(self):
        if self.value is not None:
            self.name = "View Attendance For: " + self.value.get_name()
            attendance = self.value.get_attendance()
            self.wgAttList.values = [
                [datetime.utcfromtimestamp(ts)
                 .strftime('%A %B %d %Y, %H:%M:%S')]
                for ts in attendance
            ]
            if len(self.wgAttList.values) == 0:
                self.wgAttList.values = [["<No attendance>"]]
        else:
            self.wgAttList.values = [["<No person selected>"]]

    def afterEditing(self):
        self.parentApp.switchFormPrevious()


class AttendanceEditCards(npyscreen.ActionFormV2):
    def create(self):
        self.value = None
        self.wgCards = self.add(npyscreen.BoxTitle,
                                name="Cards:", max_width=40)
        self.wgAdd = self.add(npyscreen.ButtonPress,
                              name="Add Card",
                              rely=self.wgCards.rely + 3, relx=42,
                              when_pressed_function=self.a_add)
        self.wgDel = self.add(npyscreen.ButtonPress,
                              name="Delete Card",
                              rely=self.wgCards.rely + 1, relx=42,
                              when_pressed_function=self.a_del)

    def beforeEditing(self):
        if self.value is None:
            self.name = "Edit Cards"
            self._values = []
        else:
            self.name = "Edit Cards For: " + self.value.get_name()
            self._values = [x for x in self.value.get_cards()]
        self._refresh_list()

    def _refresh_list(self):
        self.wgCards.entry_widget.values = []
        for card in self._values:
            self.wgCards.entry_widget.values.append(
                hex(card) + (" " * 100))
        self.wgCards.update()

    def _add_uid(self, uid):
        if type(uid) is not int:
            try:
                uid = int(uid, 16)
            except ValueError:
                npyscreen.notify_wait("Invalid UID")
                return
        test_other = self.parentApp.database.find_person_by_card(uid)
        if test_other is not None:
            npyscreen.notify_wait(
                "{} already has card {}".format(
                    test_other.get_name(), hex(uid)))
            return
        if uid not in self._values:
            self._values.append(uid)
        self._refresh_list()
        npyscreen.notify_wait("Added card {}".format(hex(uid)))

    def a_add(self, *args):
        npyscreen.notify("Loading NFC")
        with Nfc() as nfc:
            devs = nfc.get_devices()
            if len(devs) == 0:
                popup = InputLinePopup("No NFC Devices Found",
                                       "Enter UID:", "",
                                       self._add_uid)
                popup.edit()
                return
            nfc.select_device(devs[0])
            npyscreen.notify("Scan a card now")
            uids = []
            while len(uids) == 0:
                uids = list(nfc.poll_uids())
            self._add_uid(uids[0])

    def a_del(self, *args):
        num = self.wgCards.entry_widget.value
        if num is None:
            npyscreen.notify_wait(
                "No card selected. Use ENTER to select a card")
            return
        if not npyscreen.notify_ok_cancel(
                "Really delete {}?".format(hex(self._values[num]))):
            return
        del self._values[num]
        self._refresh_list()

    def on_ok(self):
        # Attempt to commit changes
        updated_set = set(self._values)
        old_set = set(self.value.get_cards())
        to_add = updated_set - old_set
        to_remove = old_set - updated_set
        for card in to_remove:
            self.value.unregister_card(card)
        errors = []
        for card in to_add:
            if not self.value.register_card(card):
                errors.append(card)
        if len(errors) > 0:
            npyscreen.notify_wait(
                "Unexpected error registering {}".format(
                    ", ".join([hex(x) for x in errors])))
        self.parentApp.switchFormPrevious()

    def on_cancel(self):
        self.parentApp.switchFormPrevious()


class AttendanceTui(npyscreen.NPSAppManaged):
    def onStart(self):
        self.database = JsonFileStore()
        self.addForm("MAIN", AttendanceDisplay, name="Attendance Database")
        self.addForm("ATTVIEW", AttendanceViewPerson,
                     name="View Attendance Dates")
        self.addForm("CARDVIEW", AttendanceEditCards,
                     name="Edit Cards")


def sigint(myApp):
    if npyscreen.notify_ok_cancel("Exit?"):
        myApp.switchForm(None)


def main():
    myApp = AttendanceTui()
    signal.signal(signal.SIGINT, lambda *args: sigint(myApp))
    myApp.run()


if __name__ == "__main__":
    main()
