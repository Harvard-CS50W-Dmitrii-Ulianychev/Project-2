from auctions.models import Watchlist

from django.db.models import Count

def watchlist_items(request):
    num_items = 0
    if request.user.is_authenticated:
        watchlist = Watchlist.objects.filter(user=request.user).annotate(num_listings=Count('listings'))
        if watchlist.exists():
            num_items = watchlist.first().num_listings
    return {'num_items': num_items}
