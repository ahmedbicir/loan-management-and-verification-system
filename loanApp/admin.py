from django.contrib import admin
from .models import loanRequest, loanCategory, CustomerLoan, loanTransaction, OTPRecord
# Register your models here.loanCategory,
admin.site.register(loanRequest)
admin.site.register(loanCategory)
admin.site.register(loanTransaction)
admin.site.register(CustomerLoan)
admin.site.register(OTPRecord)
