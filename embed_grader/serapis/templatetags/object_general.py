"""
We create several filters to allow invoking a method from an object. If we do

    obj.some_method(arg1, arg2)

this template allows you to invoke by the following syntax:

    obj|pm:'some_method'|pa:arg1|pa:arg2|invoke

This is helpful especially when using a method in if template tag.
"""

from django.core.urlresolvers import reverse

from django import template
from django.utils.html import format_html

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
def pm(callee, method_name):
    return ObjectCallingNode(callee, method_name)

@register.filter
def pa(object_middle_node, arg):
    if type(object_middle_node) is not ObjectCallingNode:
        raise Exception('Expect an ObjectCallingNode object')
    if object_middle_node.state not in [
            ObjectCallingNode.STATE_GOT_CALLEE, ObjectCallingNode.STATE_GOT_ARG]:
        raise Exception('Invalid state for passing an argument')

    object_middle_node.args.append(arg)
    object_middle_node.state = ObjectCallingNode.STATE_GOT_ARG
    return object_middle_node

@register.filter
def invoke(object_middle_node, arg=None):
    if type(object_middle_node) is not ObjectCallingNode:
        raise Exception('Expect an ObjectCallingNode object')
    if object_middle_node.state != ObjectCallingNode.STATE_GOT_ARG:
        raise Exception('Invalid state for invoking a method')
    if arg != None:
        raise Exception('Redundant filter argument')

    object_middle_node.state = ObjectCallingNode.STATE_EXECUTED
    return object_middle_node.method_to_call(*(object_middle_node.args))
