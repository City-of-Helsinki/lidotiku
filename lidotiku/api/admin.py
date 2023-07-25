from django.contrib import admin
from .models import EcoCounterCounter

@admin.register(EcoCounterCounter)
class EcoCounterCounterAdmin(admin.ModelAdmin):
    pass
