from django import forms


class BookingForm(forms.Form):
    seats_booked = forms.IntegerField(min_value=1)
