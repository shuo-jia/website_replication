from django.contrib import admin
from . import models as custom_models


# Register your models here.
class CompositeIndexAdmin(admin.ModelAdmin):
    search_fields = ['code', 'name']


class SectorMovementAdmin(admin.ModelAdmin):
    search_fields = ['name']


class StockPriceAdmin(admin.ModelAdmin):
    search_fields = ['code', 'name']


class StockFollowAdmin(admin.ModelAdmin):
    search_fields = ['code']


class StockPriceHistoryAdmin(admin.ModelAdmin):
    search_fields = ['code', 'date']


admin.site.register(custom_models.CompositeIndex, CompositeIndexAdmin)
admin.site.register(custom_models.SectorMovement, SectorMovementAdmin)
admin.site.register(custom_models.StockPrice, StockPriceAdmin)
admin.site.register(custom_models.StockFollow, StockFollowAdmin)
admin.site.register(custom_models.StockPriceHistory, StockPriceHistoryAdmin)
admin.site.register(custom_models.StockProfitPredict)
