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
    cc_number = CardNumberField(label='Credit card number')
    cc_expiry = CardExpiryField(label='Expiration')
    cc_code = SecurityCodeField(label='CVV')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cc_number'].widget.attrs['class'] = "form-control"
        self.fields['cc_expiry'].widget.attrs['class'] = "form-control"
        self.fields['cc_code'].widget.attrs['class'] = "form-control"
