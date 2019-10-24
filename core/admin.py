from django.contrib import admin
from .models import BusinessTrip, BusinessTripQueue,\
    DeputyGovernor, EmailSending, Order, ApplicationFunding,\
    ActiveSetting, PassportData


admin.site.register(BusinessTrip)
admin.site.register(BusinessTripQueue)
admin.site.register(DeputyGovernor)
admin.site.register(EmailSending)
admin.site.register(Order)
admin.site.register(ApplicationFunding)
admin.site.register(ActiveSetting)
admin.site.register(PassportData)
