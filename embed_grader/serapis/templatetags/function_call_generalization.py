"""
We create several filters to allow invoking a method from an object. If we do

    func(arg1, arg2)

this tag allows you to invoke the function call by the following syntax (in template):

    func_wrapper|pfa:arg1|pfa:arg2|invoke_function

and by the way, the wrapper is defined as (in python)

    func_wrapper = [func]

This is helpful when using a function in template language. The reason that we cannot pass a
function directly to the template is that the template will silently convert a function variable
into undefined. Wrapping the function into the list is the trick to secure the function object.
"""

import inspect


from django import template

from serapis.models import *


register = template.Library()


class FunctionCallingNode:
    STATE_GOT_ARG = 0
    STATE_EXECUTED = 1
    def __init__(self, func, arg):
        self.func = func
        self.args = [arg]
        self.state = FunctionCallingNode.STATE_GOT_ARG


@register.filter
def pfa(callee, arg):
    """
    Short name of "passing function argument"
    """
    print(callee, type(callee), arg, type(arg))
    if type(callee) is list:
        # if callee is a function wrapped by a list, then put the node into the initial state.
        # The reason that the function has to be wrapped by a list is that, if we pass a function
        # directly into a template, it will automatically converted to undefined. Wrapping into
        # a list will secure the function.
        if len(callee) != 1:
            raise Exception('Expect one-element list')
        func = callee[0]
        if not inspect.isfunction(func):
            raise Exception('Expect a function who resides in the list')
        return FunctionCallingNode(func, arg)
    else:
        # otherwise, the callee should be a FunctionCallingNode in the state of receiving arguments
        if type(callee) is not FunctionCallingNode:
            raise Exception('Expect an FunctionCallingNode object')
        if callee.state != FunctionCallingNode.STATE_GOT_ARG:
            raise Exception('Invalid state for passing an argument')

        callee.args.append(arg)
        return callee

@register.filter
def invoke_function(object_middle_node, arg=None):
    if type(object_middle_node) is not FunctionCallingNode:
        raise Exception('Expect an FunctionCallingNode object')
    if object_middle_node.state != FunctionCallingNode.STATE_GOT_ARG:
        raise Exception('Invalid state for invoking the function')
    if arg != None:
        raise Exception('Redundant filter argument')

    object_middle_node.state = FunctionCallingNode.STATE_EXECUTED
    return object_middle_node.func(*(object_middle_node.args))
