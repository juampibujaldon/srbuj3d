from django.contrib import admin
from .models import *
from django.contrib.auth import get_user_model
User = get_user_model()
# Register your models here.

admin.site.register(Admin)
admin.site.register(Register)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(Cart)
admin.site.register(Payment)
admin.site.register(STLModel)