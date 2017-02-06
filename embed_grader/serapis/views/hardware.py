from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.shortcuts import render, get_object_or_404
from django.http import *
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.db import IntegrityError
from django.db import transaction
from django.db.models import Max
from django.views.generic import TemplateView

from guardian.decorators import permission_required_or_403
from guardian.compat import get_user_model
from guardian.shortcuts import assign_perm

from serapis.models import *
from serapis.forms.hardware_forms import *


@login_required(login_url='/login/')
def create_hardware_type(request):
    username = request.user
    user = User.objects.get(username=username)
    user_profile = UserProfile.objects.get(user=user)

    if not user.has_perm('serapis.view_hardware_type'):
        return HttpResponse("Not enough privilege")

    if request.method == 'POST':
        hardware_form = HardwareTypeForm(request.POST, request.FILES)
        pin_formset = HardwareTypePinFormSet(request.POST)
        if hardware_form.is_valid() and pin_formset.is_valid():
            hardware = hardware_form.save()

            hardware_pins = []
            for form in pin_formset:
                pin_name = form.cleaned_data.get('pin_name')
                hardware_pins.append(HardwareTypePin(hardware_type=hardware, pin_name=pin_name))

            try:
                with transaction.atomic():
                    HardwareTypePin.objects.filter(hardware_type=hardware).delete()
                    HardwareTypePin.objects.bulk_create(hardware_pins)
            except IntegrityError:  # if the transaction failed
                messages.error(request, 'There was an error saving your profile.')
            return HttpResponseRedirect(reverse('hardware-type-list'))
    else:
        hardware_form = HardwareTypeForm()
        pin_formset = HardwareTypePinFormSet(queryset=HardwareTypePin.objects.none())

    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'hardware_form': hardware_form,
            'pin_formset': pin_formset,
    }
    return render(request, 'serapis/create_hardware_type.html', template_context)


@login_required(login_url='/login/')
def hardware_type(request, hardware_type_id):
    username = request.user
    user = User.objects.get(username=username)
    user_profile = UserProfile.objects.get(user=user)

    if not user.has_perm('serapis.view_hardware_type'):
        return HttpResponse("Not enough privilege")

    hardware_type = HardwareType.objects.get(id=hardware_type_id)
    if not hardware_type:
        return HttpResponse("Hardware type cannot be found")

    hardware_type_pins = HardwareTypePin.objects.filter(hardware_type=hardware_type)

    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'hardware_type': hardware_type,
            'hardware_type_pins': hardware_type_pins
    }
    return render(request, 'serapis/hardware_type.html', template_context)


@login_required(login_url='/login/')
def modify_hardware_type(request, hardware_id):
    return HttpResponse("under construction")


@login_required(login_url='/login/')
def hardware_type_list(request):
    username = request.user
    user = User.objects.get(username=username)
    user_profile = UserProfile.objects.get(user=user)

    if not user.has_perm('serapis.view_hardware_type'):
        return HttpResponse("Not enough privilege")

    hardware_type_list = HardwareType.objects.all()
    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'hardware_type_list': hardware_type_list,
    }
    return render(request, 'serapis/hardware_type_list.html', template_context)
