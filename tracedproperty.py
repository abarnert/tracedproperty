class undefined:
    def __repr__(self):
        return '<undefined>'

class PostTracedProperty(property):
    """An automatic property that triggers a callback on changes

    Your callback function is called after the change is made.
    If you want to affect the change (e.g., for validation), try
    PreTracedProperty.

    >>> class C:
    ...     @PostTracedProperty
    ...     def x(self, oldvalue, newvalue):
    ...         print('{}.x: {} => {}'.format(type(self).__name__, 
    ...                                       oldvalue, newvalue))
    >>> 
    >>> c = C()
    >>> c.x = 2
    C.x: <undefined> => 2
    >>> c.x = 3
    C.x: 2 => 3
    >>> del c.x
    C.x: 3 => <undefined>
    """

    def __init__(dummyself, trace,
                 fget=True, fset=True, fdel=True, doc=None,
                 *, field=None):
        name = trace.__name__
        if field is None:
            field = '__' + name
        args = []
        if fget:
            def fget(self):
                return getattr(self, field)
            fget.__name__, fget.__doc__ = name, doc
            args.append(fget)
        if fset:
            def fset(self, value):
                oldvalue = getattr(self, field, undefined())
                setattr(self, field, value)
                trace(self, oldvalue, value)
            fset.__name__, fset.__doc__ = name, doc
            args.append(fset)
        if fdel:
            def fdel(self):
                oldvalue = getattr(self, field, undefined())
                delattr(self, field)
                trace(self, oldvalue, undefined())
            fdel.__name__, fdel.__doc__ = name, doc
            args.append(fdel)
        if doc:
            args.append(doc)
        super().__init__(*args)

class PreTracedProperty(property):
    """An automatic property that triggers a callback on changes

    Your callback function is called before the change is made.
    Whatever value you return will replace the attempted value. Or you
    can raise AttributeError to disallow the change (or just return
    the old value). Returning undefined() will delete the attribute.

    >>> class C:
    ...     @PreTracedProperty
    ...     def count(self, oldvalue, newvalue):
    ...         return int(newvalue)
    >>> 
    >>> c = C()
    >>> c.count = 2.5
    >>> c.count
    2
    >>> c.count = 'spam'
    Traceback (most recent call last):
        ...
    ValueError: invalid literal for int() with base 10: 'spam'
    >>> del c.count
    Traceback (most recent call last):
        ...
    TypeError: int() argument must be a string, a bytes-like object or a number, not 'undefined'
    """

    def __init__(dummyself, trace,
                 fget=True, fset=True, fdel=True, doc=None,
                 *, field=None):
        name = trace.__name__
        if field is None:
            field = '__' + name
        args = []
        def _set(self, value):
            oldvalue = getattr(self, field, undefined())
            try:
                value = trace(self, oldvalue, value)
            except AttributeError:
                return
            if value is undefined or isinstance(value, undefined):
                delattr(self, field)
            else:
                setattr(self, field, value)
        if fget:
            def fget(self):
                return getattr(self, field)
            fget.__name__, fget.__doc__ = name, doc
            args.append(fget)
        if fset:
            def fset(self, value):
                _set(self, value)
            fset.__name__, fset.__doc__ = name, doc
            args.append(fset)
        if fdel:
            def fdel(self):
                _set(self, undefined())
            fdel.__name__, fdel.__doc__ = name, doc
            args.append(fdel)
        if doc:
            args.append(doc)
        super().__init__(*args)
