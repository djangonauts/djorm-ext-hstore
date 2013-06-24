
from django.forms import ModelForm

from .models import DataBag


class DataBagForm(ModelForm):
    class Meta:
        model = DataBag
