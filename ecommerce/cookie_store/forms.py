from django import forms

PAYMENT_CHOICES = (
    ('S', 'Stripe'),
    ('P','Paypal')
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