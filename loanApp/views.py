from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .forms import LoanRequestForm, LoanTransactionForm, OTPForm
from .models import loanRequest, loanTransaction, CustomerLoan, OTPRecord, loanCategory
from loginApp.models import CustomerSignUp
from django.shortcuts import redirect
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.db.models import Sum
from datetime import datetime,timedelta
from django_otp.util import random_hex
from django_otp.oath import hotp
from django.conf import settings
from django.core.mail import send_mail
import pytz
from urllib.parse import urlencode
from django.http import HttpResponseRedirect
from django.urls import reverse
import json
import re


# @login_required(login_url='/account/login-customer')
def home(request):

    return render(request, 'home.html', context={})


@login_required(login_url='/account/login-customer')
def LoanRequest(request):
    form_is_valid_message = None  # Initialize the variable
    form_data = None
    
    if request.method == 'POST':
        form = LoanRequestForm(request.POST)
        if form.is_valid():
             # form data
            form_data = form.cleaned_data
        
            # Form validation succeeded
            user = request.user
            email = request.user.email
            
            # # Generate a random secret key
            secret_key = random_hex(20)
            # create otp
            otp = hotp(key=secret_key.encode(), counter=1, digits=6)

             # Store the otp and generated time into OTPRecord model
            current_time = datetime.now(pytz.timezone('Africa/Nairobi'))
            otp_record = OTPRecord.objects.create(user=user, email=email, otp=otp, creation_time=current_time)
            otp_record.save()

            # Send the email
            subject = 'OTP code!'
            message = f'Here is your OTP code: {otp}'
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [email]

            send_mail(subject, message, from_email, recipient_list)

            # After sending the OTP email, pass the form_data as a URL parameter
            redirect_url = '/loan/verify-otp/?' + urlencode({'form_data': form_data})
            return redirect(redirect_url)

        else:
            # Form validation failed
            print("Form is not valid...")
    else:
        form = LoanRequestForm()

    return render(request, 'loanApp/loanrequest.html', context={'form': form, 'form_is_valid_message': form_is_valid_message, 'form_data': form_data})


# verify otp
def verify_otp(request):
    message = ""
    otp_record = None
    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data.get('otp')

            otp_record = OTPRecord.objects.filter(user=request.user, otp=entered_otp).first()
            if otp_record:
                message = f'otp - {otp_record.email}'
                stored_otp = otp_record.otp
                stored_timestamp = otp_record.creation_time

                current_time = datetime.now(pytz.timezone('Africa/Nairobi'))
                expiration_duration = timedelta(minutes=5)
                expiration_time = stored_timestamp + expiration_duration

                if (current_time <= expiration_time) and (entered_otp == stored_otp):
                    # Access the form_data from the URL parameter
                    form_data_str = request.GET.get('form_data', '{}')
                    # Replace single quotes with double quotes
                    formatted_data_str = form_data_str.replace("'", '"')
                    try:
                        # Extract the loanCategory name
                        category_match = re.search('<loanCategory: (.*?)>', formatted_data_str)
                        if category_match:
                            category_name = category_match.group(1)
                            # Replace the <loanCategory: ...> with the actual category name
                            formatted_data_str = formatted_data_str.replace(category_match.group(0), '"' + category_name + '"')

                        # Deserialize the 'form_data' string
                        form_data = json.loads(formatted_data_str)

                        # Retrieve or create the loanCategory instance based on the category value
                        category_name = form_data.get('category', '')
                        category_instance = loanCategory.objects.get(loan_name=category_name)

                        # Retrieve the CustomerSignUp instance based on the logged-in user
                        customer_instance = CustomerSignUp.objects.get(user=request.user)
                        
                        # Create the LoanRequest object with the parsed form_data
                        loan_request = loanRequest.objects.create(
                            customer=customer_instance,
                            category=category_instance,
                            reason = form_data.get('reason'),
                            amount = form_data.get('amount'),
                            year = form_data.get('year')
                        )
                        loan_request.save()
                        
                        # You can also delete the OTP record if needed
                        otp_record.delete()
                        return redirect('/loan/loan-request/')
                    
                    except json.JSONDecodeError:
                        return JsonResponse({'error': 'Invalid data format'}, status=400)
                else:
                    otp_record.delete()
                    message = 'OTP is expired!'
                
            else:
                message = "Invalid OTP."
        else:
            message = "Form is not valid"
    else:
        form = OTPForm()

    context = {'form': form, 'message': message}
    return render(request, 'loanApp/verify_otp.html', context=context)


@login_required(login_url='/account/login-customer')
def LoanPayment(request):
    form = LoanTransactionForm()
    if request.method == 'POST':
        form = LoanTransactionForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.customer = request.user.customer
            payment.save()
            # pay_save = loanTransaction()
            return redirect('/')

    return render(request, 'loanApp/payment.html', context={'form': form})


@login_required(login_url='/account/login-customer')
def UserTransaction(request):
    transactions = loanTransaction.objects.filter(
        customer=request.user.customer)
    return render(request, 'loanApp/user_transaction.html', context={'transactions': transactions})


@login_required(login_url='/account/login-customer')
def UserLoanHistory(request):
    loans = loanRequest.objects.filter(
        customer=request.user.customer)
    return render(request, 'loanApp/user_loan_history.html', context={'loans': loans})


@login_required(login_url='/account/login-customer')
def UserDashboard(request):

    requestLoan = loanRequest.objects.all().filter(
        customer=request.user.customer).count(),
    approved = loanRequest.objects.all().filter(
        customer=request.user.customer).filter(status='approved').count(),
    rejected = loanRequest.objects.all().filter(
        customer=request.user.customer).filter(status='rejected').count(),
    totalLoan = CustomerLoan.objects.filter(customer=request.user.customer).aggregate(Sum('total_loan'))[
        'total_loan__sum'],
    totalPayable = CustomerLoan.objects.filter(customer=request.user.customer).aggregate(
        Sum('payable_loan'))['payable_loan__sum'],
    totalPaid = loanTransaction.objects.filter(customer=request.user.customer).aggregate(Sum('payment'))[
        'payment__sum'],
    

    dict = {
        'request': requestLoan[0],
        'approved': approved[0],
        'rejected': rejected[0],
        'totalLoan': totalLoan[0],
        'totalPayable': totalPayable[0],
        'totalPaid': totalPaid[0],
    }

    return render(request, 'loanApp/user_dashboard.html', context=dict)


def error_404_view(request, exception):
    print("not found")
    return render(request, 'notFound.html')