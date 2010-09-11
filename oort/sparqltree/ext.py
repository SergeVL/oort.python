try:
    import json # In the stdlib since Python 2.6
except ImportError:
    import simplejson as json # External requirement


class autosuper(type):
    """
    Use this as a metaclass for types to set the magic attribute '__super' on
    them. When this is accessed through self the result is an object
    constructed as if super(ThisType, self) had been called. (Makes it a little
    bit more like in Python 3, where super() will work like this attribute.)
    """
    def __init__(cls, name, bases, members):
        super(autosuper, cls).__init__(name, bases, members)
        setattr(cls, "_%s__super" % name, super(cls))


