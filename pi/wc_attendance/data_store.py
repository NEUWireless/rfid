import logging
from datetime import datetime
import calendar
import uuid
from typing import NewType, List, Set

CardUid = NewType('CardUid', int)
UnixTime = NewType('UnixTime', int)

logger = logging.getLogger(__name__)

__all__ = ["Person", "DataStore", "CardUid", "UnixTime"]


class Person:
    '''
    Class for an individual with attendance data. Has a UUID, name, list of
    card UIDs associated with them, and a list of UNIX timestamps when they
    signed in for attendance.
    '''
    def __init__(self):
        raise NotImplementedError()

    # Data associated with a person: A unique ID, display name, list of card
    # UIDs (stored as ints) and attendance log (list of UNIX timestamps)

    def get_id(self) -> str:
        raise NotImplementedError()

    def get_name(self) -> str:
        raise NotImplementedError()

    def get_cards(self) -> Set[CardUid]:
        raise NotImplementedError()

    def get_attendance(self) -> List[UnixTime]:
        raise NotImplementedError()

    # Methods to update data

    def set_name(self, name: str) -> None:
        raise NotImplementedError()

    def register_card(self, card_id: CardUid) -> bool:
        raise NotImplementedError()

    def unregister_card(self, card_id: CardUid) -> bool:
        raise NotImplementedError()

    def log_attendance(self) -> bool:
        raise NotImplementedError()

    def __repr__(self) -> str:
        return "Person[id={}, name={}, card_ids={}, attendance_log={}]".format(
            self.get_id(),
            self.get_name(),
            self.get_cards(),
            self.get_attendance()
        )


class DataStore:
    '''
    Interface for data storage. This exists to create a consistent interface
    for data storage, in case someone eventually wants to replace the
    JSON-based data storage system with something else.
    '''
    def __init__(self):
        raise NotImplementedError()

    # External API

    def new_person(self, name: str) -> Person:
        '''
        Creates a new person with the given name.
        '''
        raise NotImplementedError()

    def find_person_by_id(self, person_id: str) -> Person:
        '''
        Finds a person by their UUID.
        '''
        raise NotImplementedError()

    def find_person_by_name(self, person_name: str) -> Person:
        '''
        Finds a person by their display name.
        '''
        raise NotImplementedError()

    def find_person_by_card(self, card_id: CardUid) -> Person:
        '''
        Finds a person by the UID of a card they own.
        '''
        raise NotImplementedError()

    def all_person_ids(self) -> Set[str]:
        '''
        Gets all UUIDs of people in the data.
        '''
        raise NotImplementedError()

    # Utility methods for subclasses

    def _utc_now(self) -> int:
        d = datetime.utcnow()
        unixtime = calendar.timegm(d.utctimetuple())
        return unixtime

    def _random_id(self) -> str:
        return uuid.uuid4().hex
