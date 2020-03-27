from django import forms
from creditcards.forms import CardNumberField, CardExpiryField, SecurityCodeField


PAYMENT_CHOICES = (
    ('S', 'Stripe'),
    ('P','Pagadito')
)

class CheckoutForm(forms.Form):
    first_name=forms.CharField(widget=forms.TextInput(attrs={
        'class':'form-control'
    }))
    last_name=forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))
    payment_options=forms.ChoiceField(widget=forms.RadioSelect(),
                                      choices=PAYMENT_CHOICES)

class CreditCardForm(forms.Form):
    cc_number = CardNumberField(label='Credit card number', widget=forms.TextInput(attrs={
        'class':'form-control'
    }))
    cc_expiry = CardExpiryField(label='Expiration', widget=forms.TextInput(attrs={
        'class':'form-control'
    }))
    cc_code = SecurityCodeField(label='CVV', widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))
