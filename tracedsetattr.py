import collections

class undefined:
    def __repr__(self):
        return '<undefined>'

class TracingMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        super().__setattr__('_pretraces', collections.defaultdict(list))
        super().__setattr__('_posttraces', collections.defaultdict(list))
    def pretrace(self, name, callback):
        self._pretraces[name].append(callback)
    def posttrace(self, name, callback):
        self._posttraces[name].append(callback)
    def __setattr__(self, name, value):
        if self._pretraces[name] or self._posttraces[name]:
            oldvalue = getattr(self, name, undefined())
        try:
            for callback in self._pretraces[name]:
                value = callback(oldvalue, value)
        except AttributeError:
            return
        super().__setattr__(name, value)
        for callback in self._posttraces[name]:
            callback(oldvalue, value)

class C(TracingMixin):
    def __init__(self):
        super().__init__()
        self.pretrace('x', self.validate_x)
        self.posttrace('x', self.report_x)
        self.logger = print
    def validate_x(self, oldvalue, value):
        return int(value)
    def report_x(self, oldvalue, value):
        self.logger('x: {} -> {}'.format(oldvalue, value))

c = C()
c.x = 1
c.x = 2.5
try:
    c.x = 'spam'
except ValueError as e:
    print(e)
try:
    c.x = None
except TypeError as e:
    print(e)
try:
    del c.x
except TypeError as e:
    print(e)
    
