"""
We create several filters to allow invoking a method from an object. If we do

    func(arg1, arg2)

this tag allows you to invoke the function call by the following syntax:

    func|pfa:arg1|pfa:arg2|invoke_function

This is helpful when using a function in template language.
"""

import inspect


from django import template

from serapis.models import *


register = template.Library()


class FunctionCallingNode:
    STATE_GOT_ARG = 0
    STATE_EXECUTED = 1
    def __init__(self, func):
        self.func = func
        self.args = []
        self.state = ObjectCallingNode.STATE_GOT_ARG


@register.filter
def pfa(callee, arg):
    """
    Short name of "passing function argument"
    """
    if inspect.isfunction(callee):
        # if callee is a function, then put the node into the initial state
        return FunctionCallingNode(callee)
    else:
        # otherwise, the callee should be a FunctionCallingNode in the state of receiving arguments
        if type(callee) is not FunctionCallingNode:
            raise Exception('Expect an FunctionCallingNode object')
        if callee.state != FunctionCallingNode.STATE_GOT_CALLEE:
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

    object_middle_node.state = ObjectCallingNode.STATE_EXECUTED
    return object_middle_node.func(*(object_middle_node.args))
