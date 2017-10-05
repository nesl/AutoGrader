"""
We create several filters to allow invoking a method from an object. If we do

    obj.some_method(arg1, arg2)

this tag allows you to invoke the method call by the following syntax:

    obj|pom:'some_method'|poa:arg1|pa:arg2|invoke_method

This is helpful when calling a method in template language.
"""

from django import template

from serapis.models import *


register = template.Library()


class ObjectCallingNode:
    STATE_GOT_CALLEE = 0
    STATE_GOT_ARG = 1
    STATE_EXECUTED = 2
    def __init__(self, callee_obj, method_name):
        self.method_to_call = getattr(callee_obj, method_name)
        self.args = []
        self.state = ObjectCallingNode.STATE_GOT_CALLEE


@register.filter
def pom(callee, method_name):
    """
    Short name of "passing object method"
    """
    return ObjectCallingNode(callee, method_name)

@register.filter
def poa(object_middle_node, arg):
    """
    Short name of "passing object argument"
    """
    if type(object_middle_node) is not ObjectCallingNode:
        raise Exception('Expect an ObjectCallingNode object')
    if object_middle_node.state not in [
            ObjectCallingNode.STATE_GOT_CALLEE, ObjectCallingNode.STATE_GOT_ARG]:
        raise Exception('Invalid state for passing an argument')

    object_middle_node.args.append(arg)
    object_middle_node.state = ObjectCallingNode.STATE_GOT_ARG
    return object_middle_node

@register.filter
def invoke_method(object_middle_node, arg=None):
    if type(object_middle_node) is not ObjectCallingNode:
        raise Exception('Expect an ObjectCallingNode object')
    if object_middle_node.state != ObjectCallingNode.STATE_GOT_ARG:
        raise Exception('Invalid state for invoking a method')
    if arg != None:
        raise Exception('Redundant filter argument')

    object_middle_node.state = ObjectCallingNode.STATE_EXECUTED
    return object_middle_node.method_to_call(*(object_middle_node.args))
