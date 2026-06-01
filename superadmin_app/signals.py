
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from  . models import *


categories = [
    ("School", "School related management details."),
    ("College", "College related management details."),

    ]



@receiver(post_migrate)
def create_category(sender, **kwargs):
    for name, description in categories:
        Category.objects.get_or_create(
            name=name,
            defaults={"description": description}
        )

