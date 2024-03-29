from functools import wraps
import inspect
from collections import defaultdict


def mk_args_kwargs_merger(func):
    """
    Make a function that will return a dict containing all {argname: argval} pairs from a function's call.
    That is, it merges all non-keyword arguments with the keyword-arguments, with the right name, so that
    the arguments can be handled more uniformly.
    :param func: The function that will be called, whose signature should be looked at to make the
        merging function
    :return: A function merge_args_and_kwargs(args, kwargs) that can be used to merge arguments

    >>> def func(a, b, c=3):
    ...     return a * (b + c)
    >>> merger = mk_args_kwargs_merger(func)
    >>> dict(merger([1], {'b': 10}))
    {'a': 1, 'b': 10}
    >>> dict(merger([], {'a': 1, 'b': 10}))
    {'a': 1, 'b': 10}
    >>> dict(merger([1, 10], {}))
    {'a': 1, 'b': 10}
    >>> dict(merger([], {}))
    {}
    >>> # Usage demo:
    >>> assert func(*[1], **{'b': 10}) == func(**merger([1], {'b': 10}))
    >>> assert func(*[], **{'a': 1, 'b': 10}) == func(**merger([], {'a': 1, 'b': 10}))
    >>> assert func(**{'a': 1, 'b': 10}) == func(**merger([], {'a': 1, 'b': 10}))
    """

    def merge_args_and_kwargs(args, kwargs):
        if len(args) > 0:
            return inspect.signature(func).bind_partial(*args, **kwargs).arguments
        else:
            return kwargs

    return merge_args_and_kwargs


def assert_attrs(attrs):
    """
    Asserts, at construction time, that the class contains a specific set of attributes
    :param attrs: An attribute name (string) or a list of attribute names whose existence needs to be enforced.
    :return: A class decorator that will enforce the existence of the attrs when an instance is made
    >>> @assert_attrs('foo')
    ... class A:
    ...     bar = 10
    ...
    >>> try:
    ...     a = A()
    ... except AttributeError:
    ...     print("AttributeError, as expected, because missing the foo attribute")
    AttributeError, as expected, because missing the foo attribute
    >>> @assert_attrs('foo')
    ... class B:
    ...     def foo(self): pass
    >>> b = B()
    >>>
    >>> class A:
    ...     bar = 10
    >>> class B:
    ...     def foo(self): pass
    >>>
    >>> @assert_attrs(['foo', 'bar'])
    ... class C(A, B):
    ...     pass
    >>> c = C()
    """
    if isinstance(attrs, str):
        attrs = [attrs]

    def _assert_attrs(klass):
        @wraps(klass)
        def get_instance(*args, **kw):
            for attr in attrs:
                if not hasattr(klass, attr):
                    raise AttributeError("class {} needs to have a {} attribute:".format(
                        klass.__name__, attr))
            return klass(*args, **kw)

        return get_instance

    return _assert_attrs


def preprocess(pre):
    def decorator(func):
        if inspect.ismethod(func):
            def wrapper(self, *args, **kwargs):
                return func(self, pre(*args, **kwargs))
        else:
            def wrapper(*args, **kwargs):
                return func(pre(*args, **kwargs))
        return wraps(func)(wrapper)

    return decorator


def postprocess(post):
    def decorator(func):
        def wrapper(*args, **kwargs):
            return post(func(*args, **kwargs))

        return wraps(func)(wrapper)

    return decorator


def input_output_decorator(preprocess=None, postprocess=None):
    """
    Makes a decorator that preprocesses inputs and postprocesses outputs.
    Use it if you want to transform the input of a function or method before calling it, or if you want
    to transform the returned value before returning it.
    :param preprocess: Function to be applied to input
    :param postprocess: Function to be applied to output
    :return: a decorator that preprocesses inputs and postprocesses outputs
    See also: preprocess and postprocess decorators if you need only to pre or post process!

    >>> # Examples with "normal functions"
    >>> def f(x=3):
    ...     '''Some doc...'''
    ...     return x + 10
    >>> ff = input_output_decorator()(f)
    >>> print((ff(5.0)))
    15.0
    >>> ff = input_output_decorator(preprocess=int)(f)
    >>> print((ff(5.0)))
    15
    >>> ff = input_output_decorator(preprocess=int, postprocess=lambda x: "Hello {}!".format(x))(f)
    >>> print((ff('5')))
    Hello 15!
    >>> ff = input_output_decorator(postprocess=lambda x: "Hello {}!".format(x))(f)
    >>> print((ff(5.0)))
    Hello 15.0!
    >>> print((ff.__doc__))
    Some doc...
    >>>
    >>> # examples with methods (bounded, class methods, static methods
    >>> class F:
    ...     '''This is not what you'd expect: The doc of the class, not the function'''
    ...     def __init__(self, y=10):
    ...         '''Initialize'''
    ...         self.y = y
    ...     def __call__(self, x=3):
    ...         '''Some doc...'''
    ...         return self.y + x
    ...     @staticmethod
    ...     def static_method(x, y):
    ...         return "What {} {} you have".format(x, y)
    ...     @classmethod
    ...     def class_method(cls, x):
    ...         return "{} likes {}".format(cls.__name__, x)
    >>>
    >>> f = F()
    >>> ff = input_output_decorator()(f)
    >>> print((ff(5.0)))
    15.0
    >>> ff = input_output_decorator(preprocess=int)(f)
    >>> print((ff(5.0)))
    15
    >>> ff = input_output_decorator(preprocess=int, postprocess=lambda x: "Hello {}!".format(x))(f)
    >>> print((ff('5')))
    Hello 15!
    >>> ff = input_output_decorator(postprocess=lambda x: "Hello {}!".format(x))(f)
    >>> print((ff(5.0)))
    Hello 15.0!
    >>> print((ff.__doc__))
    This is not what you'd expect: The doc of the class, not the function

    # >>>
    # >>> f.static_method = input_output_decorator(preprocess=lambda x: '"' + x + '"',
    # ...                                          postprocess=lambda x: x + '!!!')(f.static_method)
    # >>> print(ff.static_method('big', 'eyes'))
    # What big "eyes" you have!!!
    """

    def decorator(func):
        if preprocess and postprocess:
            def func_wrapper(*args, **kwargs):
                return postprocess(func(preprocess(*args, **kwargs)))
        elif preprocess:  # a preprocess but no postprocess
            def func_wrapper(*args, **kwargs):
                return func(preprocess(*args, **kwargs))
        elif postprocess:  # a postprocess but no preprocess
            def func_wrapper(*args, **kwargs):
                return postprocess(func(*args, **kwargs))
        else:  # neither pre nor post processing, so leave func as is
            return func

        return wraps(func)(func_wrapper)

    return decorator

    # TODO: Replaced with above, but not sure yet if I need to process methods separately...
    # def decorator(func):
    #     if inspect.ismethod(func):
    #         if preprocess is not None:
    #             if postprocess is not None:  # both pre and post processes
    #                 @wraps(func)
    #                 def func_wrapper(self, *args, **kwargs):
    #                     return postprocess(func(self, preprocess(*args, **kwargs)))
    #             else:  # a preprocess but no postprocess
    #                 @wraps(func)
    #                 def func_wrapper(self, *args, **kwargs):
    #                     return func(self, preprocess(*args, **kwargs))
    #         else:  # no preprocess
    #             if postprocess is not None:  # no preprocess, but a postprocess
    #                 @wraps(func)
    #                 def func_wrapper(self, *args, **kwargs):
    #                     return postprocess(func(*args, **kwargs))
    #             else:  # no pre or post process at all
    #                 func_wrapper = func
    #         return func_wrapper
    #     else:
    #         if preprocess is not None:
    #             if postprocess is not None:  # both pre and post processes
    #                 @wraps(func)
    #                 def func_wrapper(*args, **kwargs):
    #                     return postprocess(func(preprocess(*args, **kwargs)))
    #             else:  # a preprocess but no postprocess
    #                 @wraps(func)
    #                 def func_wrapper(*args, **kwargs):
    #                     return func(preprocess(*args, **kwargs))
    #         else:  # no preprocess
    #             if postprocess is not None:  # no preprocess, but a postprocess
    #                 @wraps(func)
    #                 def func_wrapper(*args, **kwargs):
    #                     return postprocess(func(*args, **kwargs))
    #             else:  # no pre or post process at all
    #                 func_wrapper = func
    #         return func_wrapper
    #
    # return decorator


def transform_args(**trans_func_for_arg):
    """
    Make a decorator that transforms function arguments before calling the function.
    Works with plain functions and bounded methods.
    For example:
        * original argument: a relative path --> used argument: a full path
        * original argument: a pickle filepath --> used argument: the loaded object
    :param rootdir: rootdir to be used for all name arguments of target function
    :param name_arg: the position (int) or argument name of the argument containing the name
    :return: a decorator
    >>> # Example with a plain function
    >>> def f(a, b, c='default_c'):
    ...     return "a={a}, b={b}, c={c}".format(a=a, b=b, c=c)
    >>> def prepend_root(x):
    ...     return 'ROOT/' + x
    >>>
    >>> def test(f):
    ...     assert f('foo', 'bar', 3) == 'a=foo, b=bar, c=3'
    ...     ff = transform_args()(f)  # no transformation specification, so function is unchanged
    ...     assert ff('foo', 'bar', c=3) == 'a=foo, b=bar, c=3'
    ...     ff = transform_args(a=prepend_root)(f)  # prepend root to a
    ...     assert ff('foo', c=3, b='bar') == 'a=ROOT/foo, b=bar, c=3'  # note: testing different order of args
    ...     ff = transform_args(b=prepend_root)(f)  # prepend root to b
    ...     assert ff(c=3, b='bar', a='foo') == 'a=foo, b=ROOT/bar, c=3'  # note: testing different order of args
    ...     ff = transform_args(a=prepend_root, b=prepend_root)(f)  # prepend root to a and b
    ...     assert ff('foo', 'bar', 3) == 'a=ROOT/foo, b=ROOT/bar, c=3'
    ...     assert ff('foo', 'bar') == 'a=ROOT/foo, b=ROOT/bar, c=default_c'  # defaults still work
    >>>
    >>> test(f)
    >>>
    >>> # Example with bounded method, wrapping from instance
    >>> class A:
    ...     def __init__(self, sep=''):
    ...         self.sep = sep
    ...     def f(self, a, b, c='default_c'):
    ...         return f"a={a}{self.sep} b={b}{self.sep} c={c}"
    >>>
    >>> a = A(sep=',')
    >>> test(a.f)
    >>>
    >>> # Example with bounded method, wrapping from class
    >>> A.f = transform_args(a=prepend_root, b=prepend_root)(A.f)
    >>> a = A(sep=',')
    >>> assert a.f('foo', 'bar', 3) == 'a=ROOT/foo, b=ROOT/bar, c=3'
    >>> assert a.f('foo', 'bar') == 'a=ROOT/foo, b=ROOT/bar, c=default_c'  # defaults still work
    """

    def transform_args_decorator(func):
        if len(trans_func_for_arg) == 0:  # if no transformations were specified...
            return func  # just return the function itself
        else:
            @wraps(func)
            def transform_args_wrapper(*args, **kwargs):
                # get a {argname: argval, ...} dict from *args and **kwargs
                # Note: Didn't really need an if/else here but I am assuming that...
                # Note: ... getcallargs gives us an overhead that can be avoided if there's only keyword args.
                if len(args) > 0:
                    val_of_argname = inspect.signature(func).bind_partial(*args, **kwargs).arguments
                else:
                    val_of_argname = kwargs
                for argname, trans_func in trans_func_for_arg.items():
                    val_of_argname[argname] = trans_func(val_of_argname[argname])
                # apply transform functions to argument values
                return func(**val_of_argname)

            return transform_args_wrapper

    return transform_args_decorator


def wrap_method_output(wrapper_func):
    def _wrap_output(wrapped):
        @wraps(wrapped)
        def _wrapped(self, *args, **kwargs):
            return wrapper_func(wrapped(self, *args, **kwargs))

        return _wrapped

    return _wrap_output


def wrap_class_methods(_return_a_copy_of_the_class=True,
                       _raise_error_if_non_existent_method=True,
                       **wrapper_for_method):
    """
    Make a decorator that wraps specific methods.

    IMPORTANT: The decorator will by default return a copy of the class. This might incur some run time overhead.
    If this is desirable, for example, when you want to create several decorations of a same class.
    If you want to change the class itself (e.g. you're only loading it once in a module, and decorating it), then
    specify _return_a_copy_of_the_class=False

    Note that _return_a_copy_of_the_class=True has a side effect of building russian dolls of essentially subclasses
    of the class, which may have some undesirable results if repeated too many times.

    :param _return_a_copy_of_the_class: Specifies whether to
        return a copy of the class (_return_a_copy_of_the_class=True, the default),
        or change the actual loaded class itself (_return_a_copy_of_the_class=False)
    :param wrapper_for_method: method_name=wrapper_function pairs.
    :return: A class wrapper. That is, a decorator that takes a class and returns a decorated version of it
        (or decaorates "in-place" if _return_a_copy_of_the_class=False

    SEE ALSO:
        * wrap_method_output: The function that is called for every method we wrap.
        * transform_class_method_input_and_output: A wrap_class_methods that is specialized for input arg and output
            transformation.

    >>> from functools import wraps
    >>> class A:
    ...     def __init__(self, a=10):
    ...         self.a = a
    ...     def add(self, x):
    ...         return self.a + x
    ...     def multiply(self, x):
    ...         return self.a * x
    ...
    >>> a = A()
    >>> a.add(2)
    12
    >>> a.multiply(2)
    20
    >>>
    >>> def log_calls(func):
    ...     name = func.__name__
    ...     @wraps(func)
    ...     def _func(self, *args, **kwargs):
    ...         print("Calling {} with\\n  args={}\\n  kwargs={}".format(name, args, kwargs))
    ...         return func(self, *args, **kwargs)
    ...     return _func
    ...
    >>> AA = wrap_class_methods(**{k: log_calls for k in ['add', 'multiply']})(A)
    >>> a = AA()
    >>> a.add(x=2)
    Calling add with
      args=()
      kwargs={'x': 2}
    12
    >>> a.multiply(2)
    Calling multiply with
      args=(2,)
      kwargs={}
    20
    """

    def class_wrapper(cls):
        if _return_a_copy_of_the_class:
            _cls = type('_' + cls.__name__, cls.__bases__, dict(cls.__dict__))
            # class _cls(cls):
            #     pass
        else:
            _cls = cls
        for method, wrapper in wrapper_for_method.items():
            if hasattr(_cls, method):
                setattr(cls, method, wrapper(getattr(cls, method)))
            elif _raise_error_if_non_existent_method:
                if hasattr(cls, '__name__'):
                    class_name = cls.__name__
                else:
                    class_name = str(cls)
                raise ValueError("{} has no '{}' method!".format(class_name, method))
        return _cls

    return class_wrapper


def mk_input_and_output_method_wrapper(method_output_trans=None, **arg_trans):
    def wrap_method(method_func):
        wrapped_method = transform_args(**arg_trans)(method_func)
        if method_output_trans is not None:
            return wrap_method_output(method_output_trans)(wrapped_method)
        else:
            return wrapped_method

    return wrap_method


def transform_class_method_input_and_output(cls, method, method_output_trans=None, **arg_trans):
    wrapped_method = transform_args(**arg_trans)(getattr(cls, method))
    if method_output_trans is not None:
        setattr(cls, method, wrap_method_output(method_output_trans)(wrapped_method))
    else:
        setattr(cls, method, wrapped_method)


def wrap_class_methods_input_and_output(_return_a_copy_of_the_class=True,
                                        _raise_error_if_non_existent_method=True,
                                        **method_trans_spec):
    """
    Make a decorator that wraps specific methods, transforming specific argument values a nd output values.

    IMPORTANT: The decorator will by default return a copy of the class. This might incur some run time overhead.
    If this is desirable, for example, when you want to create several decorations of a same class.
    If you want to change the class itself (e.g. you're only loading it once in a module, and decorating it), then
    specify _return_a_copy_of_the_class=False

    :param _return_a_copy_of_the_class: Specifies whether to
        return a copy of the class (_return_a_copy_of_the_class=True, the default),
        or change the actual loaded class itself (_return_a_copy_of_the_class=False)
    :param method_trans_spec: method_name=trans_specs_for_method pairs.
        The trans_specs_for_method is a dict that is understood by transform_class_method_input_and_output.
        Except for one special case, it's keys are argument names and values are callables to call on those
        arguments' values.
        The special case is method_output_trans. This specifies that the callable it points to should be called
        on output of method. Here's one recipe for outputs: If the output of a function is an iterable and you want
        to apply a function trans to each element of the output, specify method_output_trans=lambda x: map(trans, x).
    :return: A wrapped class

    SEE ALSO:
        * mk_method_trans_spec_from_methods_specs_dict: a utility to make method_trans_spec more easily
        * transform_class_method_input_and_output: The function that is called for every method we wrap.

    >>> # In the following, we will show two examples.
    >>> # The first is a toy example to demonstrate the basic functionality.
    >>> # The second demonstrates a more involved case, but is still a silly example.
    >>> # The third demonstrates more the type of application we'd use wrap_class_methods_input_and_output for in real life.
    >>>
    >>> from collections import UserDict
    >>> import re
    >>> from collections import Counter
    >>>
    >>> ############################################################################################################
    >>> # FIRST EXAMPLE
    >>> # We make an Ops class that wraps Counter, allowing one to add items and show the counts of items added.
    >>> class Ops:
    ...     def __init__(self):
    ...         self.counter = Counter()
    ...     def add_item(self, item):
    ...         self.counter.update({item: 1})
    ...     def show(self):
    ...         return self.counter
    >>> # Here's an example of what Ops does
    >>> ops = Ops()
    >>> for item in ['this', 'is', 'that', 'and', 'that', 'is', 'this']:
    ...     ops.add_item(item)
    ...
    >>> ops.show()
    Counter({'this': 2, 'is': 2, 'that': 2, 'and': 1})
    >>>
    >>> # But say we don't want to count actual words added, but just the first two letters of these words,
    >>> # and say we want to show() to return the dict, not the Counter.
    >>> NewOps = wrap_class_methods_input_and_output(
    ...     _return_a_copy_of_the_class=False,
    ...     add_item=dict(item=lambda x: x[:2]),  # intercept items fed to add_item and keep only 2 first letters
    ...     show=dict(method_output_trans=dict)  # intercept output of show method, converting to dict
    ... )(Ops)
    >>> # let's try it out!
    >>> ops = NewOps()
    >>> for item in ['this', 'is', 'that', 'and', 'that', 'is', 'this']:
    ...     ops.add_item(item)
    ...
    >>> ops.show()
    {'th': 4, 'is': 2, 'an': 1}
    >>> # See that we specified _return_a_copy_of_the_class=False?
    >>> # Now look at what happens if we try to use Ops, the original class, again. It behaves like NewOps.
    >>> # That's usually not the behavior we want, so becareful!
    >>> ops = Ops()
    >>> for item in ['this', 'is', 'that', 'and', 'that', 'is', 'this']:
    ...     ops.add_item(item)
    ...
    >>> ops.show()
    {'th': 4, 'is': 2, 'an': 1}
    >>>
    >>>
    >>> ############################################################################################################
    >>> # SECOND EXAMPLE
    >>> # Wrap a dict (or rather, the safer collections.UserDict), doing weird things to the input and output
    >>> # keys and values
    >>> val_in_trans = lambda x: 'hello {}'.format(x)  # prepend "hello " to incoming values
    >>> val_out_trans = lambda x: re.sub('hello', 'hi', x)  # replace "hello" by "hi" in output values
    >>> key_in_trans = lambda x: '__' + x  # prepend incoming keys with double underscore
    >>> key_out_trans = lambda x: x[2:]  # remove the first two characters (underscores) from keys when output
    >>>
    >>> methods_specs_dict = {
    ...     ('__contains__', '__getitem__', '__setitem__', '__delitem__'): dict(key=key_in_trans),
    ...     '__setitem__': dict(item=val_in_trans),
    ...     '__iter__': dict(method_output_trans=lambda x: map(key_out_trans, x)),
    ...     '__getitem__': dict(method_output_trans=val_out_trans)
    ... }
    >>>
    >>> methods_specs_dict = mk_method_trans_spec_from_methods_specs_dict(methods_specs_dict)
    >>>
    >>> @wrap_class_methods_input_and_output(**methods_specs_dict)
    ... class AA(UserDict):
    ...     pass
    ...
    >>> aa = AA()
    >>> aa['foo'] = 'shoo'  # store 'shoo' under 'foo'
    >>> # the __str__ method isn't wrapped, so we see the actual STORED keys and values
    >>> # we see that __foo, not foo is the actual key, and "hello shoo" the value:
    >>> assert str(aa) == "{'__foo': 'hello shoo'}"
    >>> assert 'foo' in aa  # yet from the interface, it looks like 'foo' is a key of aa...
    >>> assert '__foo' not in aa  # ... and '__foo' is not a key.
    >>> aa['foo'] = 'bar'  # let's replace the value of 'foo'
    >>> assert str(aa) == "{'__foo': 'hello bar'}"  # see what's stored
    >>> aa['star'] = 'wars'  # let's add another
    >>> assert list(aa) == ['foo', 'star']  # what are the keys? (this uses __iter__ under the hood)
    >>> # In the following, we'll use methods keys(), values(), and items(), none of which we wrapped.
    >>> # And yet, they work as expected, since they pass on their work to methods we wrapped.
    >>> assert list(aa.keys()) == ['foo', 'star']  # another way to get keys
    >>> # see here that when we ask for values, we don't get what we asked to store, ...
    >>> # ... nor what is actually stored, but something else
    >>> assert list(aa.values()) == ['hi bar', 'hi wars']
    >>> assert str(list(aa.items())) == "[('foo', 'hi bar'), ('star', 'hi wars')]"  # the keys and values we get from items()
    >>> assert str(aa) == "{'__foo': 'hello bar', '__star': 'hello wars'}"  # what is actually stored
    >>> del aa['foo']  # testing deletion of a key
    >>> assert str(aa) == "{'__star': 'hello wars'}"  # it worked!
    >>>
    >>>
    >>> ############################################################################################################
    >>> # THIRD EXAMPLE
    >>> # Here again, we'll wrap UserDict. But instead of being silly, we'll pretend we need to store waveforms
    >>> # in binary format (so input values will have to be wrapped), but still retrieving these waveforms as lists
    >>> # (so output values will have to be wrapped).
    >>> # Additionally, we'll pretend we're working with wav files within some root directory, but don't
    >>> # want the root dir or the '.wav' extension to appear in our keys. So we'll have to wrap input and output keys.
    >>> # Of course, this is just pretend. Don't use this with real waveforms. It won't work.
    >>>
    >>> root = '/ROOT/DIR/'
    >>> abs_path_of_rel_path = lambda rel_path: root + rel_path + '.wav'  # transform a relative path to an absolute one
    >>> rel_path_of_abs_path = lambda x: x.replace(root, '').replace('.wav', '')  # transform an absolute path to a relative one
    >>> list_to_bytes = bytes
    >>> bytes_to_list = list
    >>>
    >>> methods_specs_dict = {
    ...     ('__contains__', '__getitem__', '__setitem__', '__delitem__'): dict(key=abs_path_of_rel_path),
    ...     '__setitem__': dict(item=list_to_bytes),
    ...     '__iter__': dict(method_output_trans=lambda x: map(rel_path_of_abs_path, x)),
    ...     '__getitem__': dict(method_output_trans=bytes_to_list)
    ... }
    >>>
    >>> methods_specs_dict = mk_method_trans_spec_from_methods_specs_dict(methods_specs_dict)
    >>>
    >>> @wrap_class_methods_input_and_output(**methods_specs_dict)
    ... class Wf(UserDict):
    ...     pass
    ...
    >>> year = [2, 0, 1, 9]
    >>> down = [5, 4, 3, 2, 1]
    >>>
    >>> wf = Wf()
    >>> wf['year'] = year
    >>> print(str(wf).replace("b'", "'"))
    {'/ROOT/DIR/year.wav': '\\x02\\x00\\x01\\t'}
    >>> 'year' in wf
    True
    >>> wf['down'] = down
    >>> print(str(wf).replace("b'", "'"))
    {'/ROOT/DIR/year.wav': '\\x02\\x00\\x01\\t', '/ROOT/DIR/down.wav': '\\x05\\x04\\x03\\x02\\x01'}
    >>> list(wf.keys())
    ['year', 'down']
    >>> list(wf.values())
    [[2, 0, 1, 9], [5, 4, 3, 2, 1]]
    >>> list(wf.items())
    [('year', [2, 0, 1, 9]), ('down', [5, 4, 3, 2, 1])]
    >>> len(wf)
    2
    >>> del wf['year']
    >>> len(wf)
    1
    >>> list(wf.items())
    [('down', [5, 4, 3, 2, 1])]
    """

    wrapper_for_method = {method: mk_input_and_output_method_wrapper(**method_trans)
                          for method, method_trans in method_trans_spec.items()}
    return wrap_class_methods(_return_a_copy_of_the_class=True,
                              _raise_error_if_non_existent_method=True, **wrapper_for_method)

    # def class_wrapper(cls):
    #     if _return_a_copy_of_the_class:
    #         class _cls(cls):
    #             pass
    #     else:
    #         _cls = cls
    #     for method, method_trans in method_trans_spec.items():
    #         if hasattr(_cls, method):
    #             transform_class_method_input_and_output(_cls, method, **method_trans)
    #         elif _raise_error_if_non_existent_method:
    #             if hasattr(cls, '__name__'):
    #                 class_name = cls.__name__
    #             else:
    #                 class_name = str(cls)
    #             raise ValueError("{} has no '{}' method!".format(class_name, method))
    #     return _cls
    #
    # return class_wrapper


from ocore.utils.pobj import add_method


def transform_instance_method_input_and_output(obj, method, method_output_trans=None, **arg_trans):
    from warnings import warn
    warn("Not sure transform_instance_method_input_and_output works yet")
    wrapped_method = transform_args(**arg_trans)(getattr(type(obj), method))
    if method_output_trans is not None:
        obj = add_method(obj, wrap_method_output(method_output_trans)(wrapped_method), method_name=method)
    else:
        obj = add_method(obj, wrapped_method, method_name=method)
    return obj


def wrap_instance_methods(_return_a_copy_of_the_class=True,
                          _raise_error_if_non_existent_method=True,
                          **method_trans_spec):
    def obj_wrapper(obj):
        for method, method_trans in method_trans_spec.items():
            if hasattr(obj, method):
                obj = transform_instance_method_input_and_output(obj, method, **method_trans)
            elif _raise_error_if_non_existent_method:
                if hasattr(obj.__class__, '__name__'):
                    class_name = obj.__name__
                else:
                    class_name = str(obj)
                raise ValueError("{} has no '{}' method!".format(class_name, method))
        return obj

    return obj_wrapper


def mk_method_trans_spec_from_methods_specs_dict(methods_specs_dict):
    """
    Utility to make inputs for wrap_class_methods_input_and_output more easily.
    :param methods_specs_dict: a dict where
        keys are method names (either a single string, or a tuple of strings)
        values are the trans_spec dicts that should be associated to those methods
    :return: A dict in the method_trans_spec (input of wrap_class_method) format.
    >>> methods_specs_dict = {}
    >>> methods_specs_dict['foo'] = {'x': str, 'y': int}
    >>> methods_specs_dict[('foo', 'bar')] = {'z': list, 'method_output_trans': float}
    >>> methods_specs_dict[('bar', )] = {'zz': int}
    >>> method_trans_spec = mk_method_trans_spec_from_methods_specs_dict(methods_specs_dict)
    >>> list(method_trans_spec.keys())
    ['foo', 'bar']
    >>> method_trans_spec['foo']
    {'x': <class 'str'>, 'y': <class 'int'>, 'z': <class 'list'>, 'method_output_trans': <class 'float'>}
    >>> method_trans_spec['bar']
    {'z': <class 'list'>, 'method_output_trans': <class 'float'>, 'zz': <class 'int'>}
    """
    method_trans_spec = defaultdict(dict)
    for methods, specs in methods_specs_dict.items():
        if isinstance(methods, str):
            methods = (methods,)
        for method in methods:
            method_trans_spec[method].update(specs)
    return dict(method_trans_spec)


from typing import Callable, Tuple, Dict, Any

Args = Tuple
Kwargs = Dict
WhatToLog = Callable[[Callable, Args, Kwargs], Any]


def _special_str(x: Any, max_len=100) -> str:
    """ A util function for _call_signature"""
    if isinstance(x, str):
        return "'" + x + "'"
    else:
        x_str = str(x)
        if len(x_str) > max_len:
            type_str = getattr(type(x), '__name__', str(type(x)))
            if hasattr(x, '__repr__'):
                value_str = x.__repr__()
            else:
                value_str = x_str
            x_str = "{}({}...)".format(type_str, value_str[:20])
        return x_str


def _call_signature(func: Callable, args: Args, kwargs: Kwargs) -> str:
    """
    A util to make a string representation of a call of a function func with given args and kwargs.
    Meant to be the default mk_log_str of mk_call_logger.
    :param func: A callable
    :param args: A tuple of positional arguments
    :param kwargs: A dict of key=val arguments
    :return: A string to represent all of that.

    >>> args = (2, 'sdf', list(range(1000)))
    >>> kwargs = {'z': 'boo', 'zzz': 10}
    >>> print(_call_signature(_call_signature, args, kwargs))
    _call_signature(2, 'sdf', list([0, 1, 2, 3, 4, 5, 6...), z='boo', zzz=10)
    """
    args_signature = ", ".join(map(_special_str, args))
    kwargs_signature = ", ".join(("{}={}".format(k, _special_str(v)) for k, v in kwargs.items()))
    return "Executing: {func_name}({signature})".format(func_name=func.__name__,
                                                        signature=", ".join([args_signature, kwargs_signature]))


def mk_call_logger(logger=print, what_to_log: WhatToLog = _call_signature, func_is_bounded=False):
    """
    Makes a decorator that logs each call to the wrapped function.
    :param logger: The actual function that logs stuff. Default is print. The "stuff" it logs is given by
        the what_to_log argument (a function).
    :param what_to_log: A function taking inputs (func, args, kwargs) of the call, and returning something to log
        (usually, and by default, a string)
    :param func_is_bounded: Whether the function is bounded (like a method) or not
    :return: A decorator

    >>> # Example of use on (unbounded) function, with default args
    >>> @mk_call_logger()
    ... def useless_computation(x, y=2, z='foo'):
    ...     return z * (x + y)
    ...
    >>> useless_computation(3, y=1, z='ha')
    Executing: useless_computation(3, y=1, z='ha')
    'hahahaha'
    >>>
    >>> # Example of use on class method, with a different what_to_log function.
    >>> class A:
    ...     def __init__(self, a=10):
    ...         self.a = a
    ...     def add(self, x):
    ...         return self.a + x
    ...     def multiply(self, x):
    ...         return self.a * x
    ...
    >>> def _name_args_kwargs(func, args, kwargs) -> str:
    ...     return "Calling {} with\\n  args={}\\n  kwargs={}".format(func.__name__, args, kwargs)
    ...
    >>>
    >>> log_calls = mk_call_logger(what_to_log=_name_args_kwargs, func_is_bounded=True)
    >>> for method in ['add', 'multiply']:
    ...     A_method = getattr(A, method)
    ...     setattr(A, method, mk_call_logger(what_to_log=_name_args_kwargs, func_is_bounded=True)(A_method))
    ...
    >>>
    >>> a = A()
    >>> a.add(x=2)
    Calling add with
      args=()
      kwargs={'x': 2}
    12
    >>> a.multiply(2)
    Calling multiply with
      args=(2,)
      kwargs={}
    20
    """
    if not func_is_bounded:
        def log_calls(func):
            @wraps(func)
            def _func(*args, **kwargs):
                logger(what_to_log(func, args, kwargs))
                return func(*args, **kwargs)

            return _func
    else:
        def log_calls(func):
            @wraps(func)
            def _func(self, *args, **kwargs):
                logger(what_to_log(func, args, kwargs))
                return func(self, *args, **kwargs)

            return _func

    return log_calls
