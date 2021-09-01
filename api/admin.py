from django.contrib import admin

from .models import Categories, Comment, Genres, Review, Titles, User

admin.site.register(User)
admin.site.register(Categories)
admin.site.register(Genres)
admin.site.register(Titles)
admin.site.register(Review)
admin.site.register(Comment)
