from django import forms
from .models import BusinessTrip, DeputyGovernor, Order, ApplicationFunding, PassportData


class BusinessTripForm(forms.ModelForm):
    class Meta:
        model = BusinessTrip
        fields = '__all__'
        exclude = ('deputy_governor',)
        widgets = {
            'position': forms.TextInput(attrs={'class': "autocomplete"}),
        }

    def disable_fields(self):
        for field in self.fields:
            self.fields[field].widget.attrs.update({'disabled': True})

    def __init__(self, *args, **kwargs):
        super(BusinessTripForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if field in ('start_date', 'end_date'):
                self.fields[field].widget.attrs.update({'class': "datepicker validate"})


class PassportDataForm(forms.ModelForm):
    class Meta:
        model = PassportData
        fields = '__all__'
        exclude = ('business_trip',)

    def disable_fields(self):
        for field in self.fields:
            self.fields[field].widget.attrs.update({'disabled': True})


class PurchasingDepartmentForm(forms.ModelForm):
    class Meta:
        model = ApplicationFunding
        fields = ('fare', 'daily_allowance', 'hotel_cost',)
        widgets = {
            'fare': forms.TextInput(attrs={'required': "true"}),
        }


class HeadOfDepartmentForm(forms.Form):
    deputy_governor = forms.ModelChoiceField(queryset=DeputyGovernor.objects.all(),
                                             label='Заместитель губернатора',
                                             initial=0)


class DeputyGovernorForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = '__all__'
        exclude = ('business_trip', 'deputy_governor', 'date_added', 'date_modified', 'upload',
                   'deputy_governor_position')


class PersonnelDepartmentForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('upload',)
