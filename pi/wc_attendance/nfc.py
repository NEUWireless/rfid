import logging
import ctypes
from ctypes.util import find_library
from typing import List, Set

from .data_store import CardUid

logger = logging.getLogger(__name__)

# C reference
# https://github.com/nfc-tools/libfreefare/blob/master/examples/mifare-desfire-access.c

LIBFREEFARE_NAME = find_library("freefare")
LIBNFC_NAME = find_library("nfc")

# Link in the C libs
libnfc = ctypes.CDLL(LIBNFC_NAME)
libfreefare = ctypes.CDLL(LIBFREEFARE_NAME)

# From nfc-types.h
NFC_BUFSIZE_CONNSTRING = 1024
nfc_connstring = ctypes.c_char * NFC_BUFSIZE_CONNSTRING

# Set up C type hints
# http://www.libnfc.org/api/group__dev.html
# http://www.libnfc.org/api/group__lib.html
libnfc.nfc_init.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
libnfc.nfc_init.restype = None

libnfc.nfc_exit.argtypes = [ctypes.c_void_p]
libnfc.nfc_exit.restype = None

libnfc.nfc_open.argtypes = [ctypes.c_void_p, nfc_connstring]
libnfc.nfc_open.restype = ctypes.c_void_p

libnfc.nfc_close.argtypes = [ctypes.c_void_p]
libnfc.nfc_close.restype = None

libnfc.nfc_list_devices.argtypes = [ctypes.c_void_p,
                                    ctypes.POINTER(nfc_connstring),
                                    ctypes.c_size_t]
libnfc.nfc_list_devices.restype = ctypes.c_size_t

# man freefare
libfreefare.freefare_get_tags.argtypes = [ctypes.c_void_p]
libfreefare.freefare_get_tags.restype = ctypes.POINTER(ctypes.c_void_p)

libfreefare.freefare_get_tag_uid.argtypes = [ctypes.c_void_p]
libfreefare.freefare_get_tag_uid.restype = ctypes.c_char_p

libfreefare.freefare_free_tags.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
libfreefare.freefare_free_tags.restype = None

# Program constants
NFC_MAX_DEVICES = 8

# The type we use when listing devices
nfc_connstring_8 = nfc_connstring * NFC_MAX_DEVICES


class Nfc:
    def __init__(self):
        self.context = ctypes.c_void_p(None)
        self.in_use = False
        self.device = None

    def __enter__(self):
        # Initalize libnfc
        self.in_use = True
        libnfc.nfc_init(ctypes.byref(self.context))
        return self

    def __exit__(self, *args):
        # Clean up libnfc
        self.in_use = False
        if self.device is not None:
            libnfc.nfc_close(self.device)
        libnfc.nfc_exit(self.context)

    def get_devices(self) -> List[str]:
        # Create buffer in format that libnfc wants, call into it
        devs_buf = nfc_connstring_8()
        count = libnfc.nfc_list_devices(self.context, devs_buf,
                                        NFC_MAX_DEVICES)
        # Convert result to python types
        devs_list = []
        for i in range(count):
            devs_list.append(devs_buf[i].value.decode('utf-8'))
        return devs_list

    def select_device(self, device_name: str) -> None:
        if self.device is not None:
            raise Exception("Device already selected")
        dev_raw = nfc_connstring()
        dev_raw.value = device_name.encode('utf-8')

        self.device = libnfc.nfc_open(self.context, dev_raw)
        if self.device is None:
            raise Exception("Failed to open device")

    def poll_uids(self) -> Set[CardUid]:
        if not self.in_use:
            raise Exception("Enter context first")
        if self.device is None:
            raise Exception("Select device first")
        tags = libfreefare.freefare_get_tags(self.device)
        if tags is None:
            raise Exception("freefare_get_tags error")
        i = 0
        uids = []
        while tags[i] is not None:
            uid_str = libfreefare.freefare_get_tag_uid(tags[i])
            uids.append(int(uid_str, 16))
            i += 1
        libfreefare.freefare_free_tags(tags)
        return set(uids)
