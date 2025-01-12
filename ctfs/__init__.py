from requests.utils import CaseInsensitiveDict

from ctfs.ad import AD
from ctfs.ctfd import CTFd
from ctfs.gzctf import GZctf
from ctfs.rctf import rCTF

CTFs = CaseInsensitiveDict(data={"CTFd": CTFd, "rCTF": rCTF, "GZctf": GZctf, "AD": AD})
