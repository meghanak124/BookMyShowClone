from django import forms


class BookingForm(forms.Form):
    selected_seats = forms.CharField(
        label="Selected Seats", help_text="Example: A1,A2,A3"
    )
