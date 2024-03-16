from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create-listing", views.create_listing, name="create_listing"),
    path("listing/<int:listing_pk>", views.listing, name="listing"),
    path("listing/<int:listing_pk>/watch", views.add_to_watchlist, name="add_to_watchlist"),
    path("listing/<int:listing_pk>/remove", views.remove_from_watchlist, name="remove_from_watchlist"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("listing/<int:listing_pk>/bid", views.place_bid, name="place_bid"),
    path("my-listings", views.my_listings, name="my_listings"),
    path("listing/<int:listing_pk>/delete", views.delete_listing, name="delete_listing"),
    path("listing/<int:listing_pk>/close", views.close_auction, name="close_auction"),
    path("listing/<int:listing_pk>/leave_comment", views.leave_comment, name="leave_comment"),
    path("categories", views.categories, name="categories"),
    path("categories/<int:category_pk>", views.category, name="category")
]

# Add this to serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)