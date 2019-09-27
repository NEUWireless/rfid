import json
import logging
import pathlib
from typing import Set, List

from .data_store import Person, DataStore, CardUid, UnixTime

logger = logging.getLogger(__name__)


class JsonFileStore(DataStore):
    '''
    JSON-file-based data storage.
    '''
    FILENAME = pathlib.Path.home() / "attendance.json"

    def __init__(self):
        if JsonFileStore.FILENAME.is_file():
            with JsonFileStore.FILENAME.open('r') as file:
                raw = json.loads(file.read())
                self.people = {x['id']: JsonPerson(x, self) for x in raw}
        else:
            self.people = {}

    def _save(self):
        with JsonFileStore.FILENAME.open('w') as file:
            file.write(json.dumps([x.json_obj for x in self.people.values()]))

    def new_person(self, name: str) -> Person:
        person = JsonPerson({'id': self._random_id(),
                             'name': name,
                             'cards': [],
                             'attendance': []}, self)
        self.people[person.get_id()] = person
        self._save()
        return person

    def find_person_by_id(self, person_id: str) -> Person:
        return self.people[person_id]

    def find_person_by_name(self, person_name: str) -> Person:
        for k, v in self.people.items():
            if v.get_name() == person_name:
                return v
        return None

    def find_person_by_card(self, card_id: CardUid) -> Person:
        for k, v in self.people.items():
            if card_id in v.get_cards():
                return v
        return None

    def all_person_ids(self) -> Set[str]:
        return self.people.keys()


class JsonPerson(Person):
    def __init__(self, json_obj: dict, parent: JsonFileStore):
        self.json_obj = json_obj
        self.parent = parent

    def get_id(self) -> str:
        return self.json_obj['id']

    def get_name(self) -> str:
        return self.json_obj['name']

    def get_cards(self) -> Set[CardUid]:
        return set(self.json_obj['cards'])

    def get_attendance(self) -> List[UnixTime]:
        return list(self.json_obj['attendance'])

    # Methods to update data

    def set_name(self, name: str) -> None:
        self.json_obj['name'] = name
        self.parent._save()

    def register_card(self, card_id: CardUid) -> bool:
        if self.parent.find_person_by_card(card_id) is not None:
            return False
        if card_id not in self.json_obj['cards']:
            self.json_obj['cards'].append(card_id)
            self.parent._save()
            return True
        return False

    def unregister_card(self, card_id: CardUid) -> bool:
        if card_id in self.json_obj['cards']:
            self.json_obj['cards'].remove(card_id)
            self.parent._save()
            return True
        return False

    def log_attendance(self) -> bool:
        time = self.parent._utc_now()
        attendance = self.json_obj['attendance']
        if len(attendance) > 0:
            last_time = attendance[len(attendance) - 1]
            # Avoid spamming the logs with duplicate attendance
            # Cooldown period of 1 minute
            if time - last_time < 60:
                logger.info("Not logging repeat attendance for %s",
                            self.get_name())
                return False
        logger.info("Logged attendance for %s", self.get_name())
        attendance.append(time)
        self.parent._save()
        return True
