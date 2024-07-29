class globalVar:
    state: "globalVar" = None

    def __new__(cls):
        if cls.state is None:
            cls.state = super(globalVar, cls).__new__(cls)
            cls.state.__initialized = False
        return cls.state

    def __init__(self):
        if not self.__initialized:
            self.__initialized = True
            self.__data = {}

    def __getitem__(self, key):
        return self.__data[key]

    def __setitem__(self, key, value):
        self.__data[key] = value

    def __delitem__(self, key):
        del self.__data[key]

    def __contains__(self, key):
        return key in self.__data

    def __iter__(self):
        return iter(self.__data)

    def __len__(self):
        return len(self.__data)

    def __str__(self):
        return str(self.__data)

    def __repr__(self):
        return repr(self.__data)

    def __getattr__(self, key):
        return self.__data[key]

    def __setattr__(self, key, value):
        self.__data[key] = value


gv = globalVar()


def get_global_var(key):
    return gv[key]


def set_global_var(key, value):
    gv[key] = value
