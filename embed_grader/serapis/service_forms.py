from django import forms
from django.forms import formset_factory
from django.forms import Form


class ReturnDutOutputForm(Form):
    id = forms.CharField()
    num_duts = forms.IntegerField()
    dut0_waveform = forms.FileField(allow_empty_file=True)
    dut0_serial_log = forms.FileField(allow_empty_file=True)
