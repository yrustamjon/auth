from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import *

@receiver(post_migrate) # agar migration qilinsa ishlaydi yani db yaralganida
def create_default_organization(sender,**kwargs):
    if not Organization.objects.filter(is_default=True).exists(): 
        Organization.objects.create(
            name = "System",
            slug = "system",
            is_default = True,
        )