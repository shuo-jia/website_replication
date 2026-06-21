from django.contrib import admin
from .models import News


# Register your models here.
class NewsAdmin(admin.ModelAdmin):
    search_fields = ['title', 'publication_date']


admin.site.register(News, NewsAdmin)
