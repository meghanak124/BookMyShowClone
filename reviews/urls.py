from django.urls import path

from .views import add_comment, add_review, delete_comment, edit_review, like_review, delete_review

urlpatterns = [
    path("add-review/<int:movie_id>/", add_review, name="add_review"),
    path("edit-review/<int:review_id>/", edit_review, name="edit_review"),
    path("like-review/<int:review_id>/", like_review, name="like_review"),
    path("add-comment/<int:movie_id>/", add_comment, name="add_comment"),
    path("delete-comment/<int:comment_id>/", delete_comment, name="delete_comment"),
    path("delete/<int:review_id>/", delete_review, name="delete_review"),

]
