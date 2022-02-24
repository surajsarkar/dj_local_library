from django import forms
import datetime

from django.core.exceptions import ValidationError
# from django.utils.translation import ugettext_lazy as _


class RenewBookForm(forms.Form):
    renewal_date = forms.DateField(help_text='Enter the date between now and 4 weeks (default is 3)')

    def clean_renewal_date(self):
        data = self.cleaned_data['renewal_date']

        if data < datetime.date.today():
            raise ValidationError("Invalid data :- renewal in past")

        if data > datetime.date.today() + datetime.timedelta( weeks=4 ):
            raise ValidationError("Invalid data:- renewal more than 4 weeks ahead")

        return data
