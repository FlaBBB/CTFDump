from requests.utils import CaseInsensitiveDict

from core.ctfs.ctfd import CTFd
from core.ctfs.intechfest import IntechFest
from core.ctfs.rctf import rCTF

CTFs = CaseInsensitiveDict(data={"CTFd": CTFd, "rCTF": rCTF, "IntechFest": IntechFest})
