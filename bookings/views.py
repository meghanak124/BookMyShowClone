from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from movies.models import Show
from .models import Booking


@login_required
def book_show(request, show_id):
    show = get_object_or_404(Show, id=show_id)
    theatre = show.theatre

    # Never show unavailable page
    if show.show_time <= timezone.now() or int(show.available_seats) <= 0:
        return redirect("movie_detail", movie_id=show.movie.id)

    all_seats = []
    for row_index in range(theatre.rows):
        row_letter = chr(65 + row_index)
        for col in range(1, theatre.columns + 1):
            all_seats.append(f"{row_letter}{col}")

    booked_seats = []
    existing_bookings = Booking.objects.filter(show=show)

    for booking in existing_bookings:
        if booking.selected_seats:
            booked_seats.extend(
                [seat.strip() for seat in booking.selected_seats.split(",") if seat.strip()]
            )

    error = None

    if request.method == "POST":
        seat_list = request.POST.getlist("selected_seats")
        seat_list = [seat.strip() for seat in seat_list if seat.strip()]
        seats_booked = len(seat_list)

        if show.show_time <= timezone.now():
            error = "This show has already ended."
        elif int(show.available_seats) <= 0:
            error = "This show is sold out."
        elif seats_booked == 0:
            error = "Please select at least one seat."
        elif any(seat in booked_seats for seat in seat_list):
            error = "Some selected seats are already booked."
        elif seats_booked > int(show.available_seats):
            error = "Not enough seats available."
        else:
            Booking.objects.create(
                user=request.user,
                show=show,
                seats_booked=seats_booked,
                selected_seats=", ".join(seat_list),
            )
            show.available_seats = int(show.available_seats) - seats_booked
            show.save()
            return redirect("my_bookings")

    return render(
        request,
        "bookings/book_show.html",
        {
            "show": show,
            "all_seats": all_seats,
            "booked_seats": booked_seats,
            "error": error,
        },
    )


@login_required
def my_bookings(request):
    now = timezone.now()

    past_bookings = Booking.objects.filter(
        user=request.user, show__show_time__lt=now, status="upcoming"
    )
    past_bookings.update(status="watched")

    bookings = Booking.objects.filter(
        user=request.user, show__show_time__gte=now
    ).order_by("show__show_time")

    return render(request, "bookings/my_bookings.html", {"bookings": bookings})


@login_required
def delete_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if booking.user != request.user:
        return HttpResponseForbidden("You are not allowed to delete this booking.")

    if request.method == "POST":
        booking.show.available_seats = int(booking.show.available_seats) + booking.seats_booked
        booking.show.save()
        booking.delete()

    return redirect("my_bookings")

