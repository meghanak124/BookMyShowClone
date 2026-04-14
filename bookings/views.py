from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from movies.models import Show

from .forms import BookingForm
from .models import Booking


@login_required
def book_show(request, show_id):
    show = get_object_or_404(Show, id=show_id)

    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            seats_booked = form.cleaned_data["seats_booked"]

            if seats_booked <= show.available_seats:
                Booking.objects.create(
                    user=request.user, show=show, seats_booked=seats_booked
                )
                show.available_seats -= seats_booked
                show.save()
                return redirect("my_bookings")
            else:
                form.add_error("seats_booked", "Not enough seats available")
    else:
        form = BookingForm()

    return render(request, "bookings/book_show.html", {"show": show, "form": form})


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).order_by("-booking_time")
    return render(request, "bookings/my_bookings.html", {"bookings": bookings})
