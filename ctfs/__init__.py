from requests.utils import CaseInsensitiveDict

from ctfs.ad import AD
from ctfs.ctfd import CTFd
from ctfs.gzctf import GZctf
from ctfs.rctf import rCTF
from ctfs.siberlab import SiberLab

CTFs = CaseInsensitiveDict(
    data={
        "CTFd": CTFd,
        "rCTF": rCTF,
        "GZctf": GZctf,
        "AD": AD,
        "SiberLab": SiberLab,
    }
)
