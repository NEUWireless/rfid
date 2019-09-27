import logging
import time
from typing import Generator

from .data_store import DataStore, CardUid
from .json_store import JsonFileStore
from .nfc import Nfc
from .status_led import StatusLeds

logger = logging.getLogger(__name__)


def setup_logging():
    # Set up logging
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    fm = logging.Formatter(
        "%(asctime)s - %(name)-25s - %(funcName)-10s - %(levelname)-5s"
        + " - %(message)s")
    ch.setFormatter(fm)
    root.addHandler(ch)


def unique_card_generator(nfc: Nfc) -> Generator[CardUid, None, None]:
    try:
        last_cards = set()
        while True:
            curr_cards = nfc.poll_uids()
            diff_cards = curr_cards - last_cards
            last_cards = (last_cards & curr_cards) | diff_cards
            for uid in diff_cards:
                yield uid
            time.sleep(0.5)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt - exiting")


def mode_log_attendance(data_store: DataStore, nfc: Nfc,
                        leds: StatusLeds) -> None:
    logger.info("Begin logging attendance")

    for uid in unique_card_generator(nfc):
        owner = data_store.find_person_by_card(uid)
        if owner is None:
            logger.info("Registering new person for card %x", uid)
            with leds.enter_new_person():
                name = input("Enter your name: ")
                person = data_store.new_person(name)
                person.register_card(uid)
                person.log_attendance()
                logger.info(
                    "Success - registered %s and logged attendance",
                    name)
        else:
            owner.log_attendance()
            leds.blink_ok()


def main():
    setup_logging()

    try:
        logger.info("Starting attendance")
        with Nfc() as nfc:
            devices = nfc.get_devices()
            logger.info("Found nfc devices %s", devices)
            if len(devices) == 0:
                logger.error("No nfc devices found")
                raise SystemExit()
            logger.info("Using reader %s", devices[0])
            nfc.select_device(devices[0])

            data_store = JsonFileStore()
            leds = StatusLeds()
            mode_log_attendance(data_store, nfc, leds)
    except Exception:
        logger.exception("Ran into error")
