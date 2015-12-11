# tracedproperty
Attributes that trigger tracing callbacks when changed

The `tracedproperty` module contains two types, PostTracedProperty and
PreTracedProperty. Both can be used to automatically generate a
property for a class that acts just like a normal attribute, except
for calling a tracing function whenever that attribute is changed.

I'm not sure why I actually wanted this. My guess is that someone else
asked for it, I said it would be easy, and then decided to see how
easy it actually is. :)

Post-tracing
============

A post-traced property has a callback that's triggered after the
attribute has been changed. It gets the old and new values as
arguments. For example:

    class C:
        @PostTracedProperty
	def x(self, oldvalue, newvalue):
	    print('x: {} => {}'.format(oldvalue, newvalue))

You might use this to, say, set a dirty flag if the user has gone past
the last line:

    class C:
        def __init__(self):
	    self._maxline = -1
        @PostTracedProperty
	def line(self, _, newline):
	    if newline > self._maxline:
	        self._maxline = newline
                self._dirty = True

Or maybe you're missing WPF-style viewmodel code:

    class Service:
        def __init__(self):
	    self.connstate = 'disconnected'
	    self.onconnstate = []
        @PostTracedProperty
	def connstate(self, oldvalue, newvalue):
	    for handler in self.onconstate:
	        handler(newvalue)
	def add_onconnstate(self, callback):
	    self.onconnstate.append(add_onconstate)

... although if you're going to have more than one such thing, you'd
probably want to wrap up even more of the boilerplate in a single
object that manages the property and the list of handlers together.

Undefined
=========

A special "undefined" value will be passed if the attribute didn't
exist before the change, or won't exist after the change (e.g., after
"del c.x"). This value is not equal to anything else (including other
copies of undefined), and prints out as `<undefined>`.

This seems like kind of a hacky solution, so I may well change it in
version 0.2 if I can think of a better alternative.

Pre-tracing
===========

Pre-traced properties call their callback before the attribute is
set, rather than after.

This means the callback can influence the attempted change.

To let the change happen as planned, return the attempted new
value. (This works fine for deletion, too--just return the `undefined`
that you received.)

To store a different value, return that different value.

To delete the attribute instead, return an `undefined` value. (This is
where `undefined` gets really hacky... But then how often do you want
to respond to a `setattr` by doing a `delattr` instead?)

To reject the change entirely, raise an `AttributeError`. (You could
instead return the oldvalue, but it usually makes more sense to do
nothing than to do something redundant.)

Pre-tracing can easily be used for field coercion and/or validation. For
example:

A simple example of pre-tracing:

    class C:
        @PostTracedProperty
	def x(self, oldvalue, newvalue):
	    try:
                return int(newvalue)
	    except (ValueError, TypeError):
	        return AttributeError

Now:

    >>> c = C()
    >>> c.x = 2.5
    >>> c.x
    2
    >>> c.x = 'spam'
    >>> c.x
    2
    >>> c.x = None
    >>> c.x
    2

tracedsetattr
=============

The extra `tracedsetattr` module just shows how to get a similar
effect in a completely different way.

Function-call API
=================

Just like `@property`, you will usually use this as a decorator, but
can use it as a normal call (or, actually, object construction, but
they look the same in Python). The interface in that case is a little
different from `property`.

There's an extra `trace` argument, which is the tracing callback.

There are arguments named `fget`, `fset`, and `fdel`, but they're
booleans. In `property`, these are how you specify the getter, setter,
and deler functions; in `SpamTracedProperty`, they're just flags that
control whether an automatic getter, setter, or deler will be
created. (I suppose these could allow callables, which would then get
wrapped by the tracing, but I don't see a use case for that.)

The `doc` parameter works the same as with `property`; if left out,
the default is to take it from the `trace` function.

Finally, there's a `field` parameter that specifies the name of the
backing attribute. The default for this is `__` plus the name, which
is unlikely to collide with anything else (especially since an
explicit `__spam` elsewhere will get name-mangled). But if you want to
provide a specific name, you can.

Ideas
=====

The whole `undefined` thing is a bad, unpythonic hack. But what's a
better API? Two values and two flags telling you whether to use those
values or not, and you likewise return a pair? (This is one of those
cases where `Maybe` is categorically better than exceptions...)

It might be better to make this a two-step decorator, where you use
`@PostTracedProperty(fset=False, doc='Thingy')`, instead of flattening
those other parameters onto the same call as the decoration call,
which means they can't be used with decorator syntax. I started off
wanting to follow the API of `property`, but now that seems more
misleading than helpful... (And if I do that, then there's no reason
for this to be a subclass of `property`, take a useless `self`, and
`super` around; it could just be a normal factory function that
constructs and returns a `property`.)

If this _is_ going to stay a class, it would probably be better to
store stuff in instance variables, instead of closure cells that all
of the local functions share. And either way, exposing `trace` might
be nice (as `property` exposes its functions).

The value doesn't have to be stored in a normal attribute. And, even
if it is, we could gensym it instead of just hoping `__name` is
safe. Then we wouldn't need `field`. Although having a predictable
name can be handy for debugging or reflection...

Are we actually getting anything out of `property` here, or would it
be simpler just to build a custom descriptor? I suppose the public
`getter`, etc. members can be handy, and the fact that it shows up as
a `property` when you look at it on the class, and that it presumably
satisfies `@abstractproperty`... but how important are those?
