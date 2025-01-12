from requests.utils import CaseInsensitiveDict

from core.ctfs.ad import AD
from core.ctfs.ctfd import CTFd
from core.ctfs.gzctf import GZctf
from core.ctfs.rctf import rCTF

CTFs = CaseInsensitiveDict(data={"CTFd": CTFd, "rCTF": rCTF, "GZctf": GZctf, "AD": AD})
