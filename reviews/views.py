from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from movies.models import Movie

from .forms import CommentForm, ReviewForm
from .models import Comment, Like, Review


@login_required
def add_review(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.movie = movie
            review.save()
            return redirect("movie_detail", movie_id=movie.id)
    else:
        form = ReviewForm()

    return render(request, "reviews/add_review.html", {"form": form, "movie": movie})


@login_required
def like_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    Like.objects.get_or_create(user=request.user, review=review)
    return redirect("movie_detail", movie_id=review.movie.id)


@login_required
def add_comment(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.movie = movie

            parent_id = request.POST.get("parent_id")
            if parent_id:
                parent_comment = get_object_or_404(Comment, id=parent_id)
                comment.parent = parent_comment

            comment.save()

    return redirect("movie_detail", movie_id=movie.id)


@login_required
def edit_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)

    if review.user != request.user:
        return HttpResponseForbidden("You are not allowed to edit this review.")

    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "Review updated successfully.")
            return redirect("movie_detail", movie_id=review.movie.id)
    else:
        form = ReviewForm(instance=review)

    return render(request, "reviews/edit_review.html", {"form": form, "review": review})
