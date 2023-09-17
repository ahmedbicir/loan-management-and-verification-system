from django import forms
from .models import loanRequest, loanTransaction, OTPRecord


class LoanRequestForm(forms.ModelForm):
    class Meta:
        model = loanRequest
        fields = ['category', 'reason', 'amount', 'year']


class LoanTransactionForm(forms.ModelForm):
    class Meta:
        model = loanTransaction
        fields = ('payment',)


class OTPForm(forms.ModelForm):
    class Meta:
        model = OTPRecord
        fields = ['otp']