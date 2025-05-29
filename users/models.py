# users/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
import re

# Custom validator funksiyalari (avvalgidek qoldiring)
def validate_passport_number(value):
    if not re.fullmatch(r'^[A-Z]{2}\d{7}$', value):
        raise ValidationError(
            'Pasport raqami formati noto\'g\'ri. Misol: AA1234567 (2 ta bosh harf, 7 ta raqam).'
        )

def validate_phone_number(value):
    if not value.startswith('+998'):
        raise ValidationError(
            'Telefon raqami +998 bilan boshlanishi kerak.'
        )
    if not re.fullmatch(r'^\+998\d{9}$', value):
        raise ValidationError(
            'Telefon raqami formati noto\'g\'ri. Misol: +998XXYYYYYYY (998 dan keyin 9 ta raqam).'
        )

class StudentProfile(AbstractUser):
    full_name = models.CharField(max_length=255, verbose_name="To'liq ism (F.I.Sh.)")
    passport_number = models.CharField(
        max_length=9,
        unique=True,
        validators=[validate_passport_number],
        verbose_name="Pasport raqami"
    )
    phone_number = models.CharField(
        max_length=13,
        unique=True,
        validators=[validate_phone_number],
        verbose_name="Telefon raqami"
    )
    address = models.CharField(max_length=255, verbose_name="Yashash manzili")

    # Ushbu qatorni diqqat bilan tekshiring.
    # Agar hali ham xato bersa, `null=True, blank=True` qatorlarini va `on_delete` ni vaqtincha olib tashlab ko'ring.
    # Ammo hozircha quyidagicha qoldiramiz.
    group = models.ForeignKey(
        'tests.Group',
        on_delete=models.SET_NULL, # Agar Group o'chirilsa, bu maydon NULL bo'ladi.
        null=True, # Ma'lumotlar bazasida NULL bo'lishiga ruxsat beradi.
        blank=True, # Formada bo'sh qoldirishga ruxsat beradi.
        verbose_name="Guruh"
    )

    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        null=True,
        blank=True,
        verbose_name="Profil rasmi"
    )

    class Meta:
        verbose_name = "Talaba profili"
        verbose_name_plural = "Talaba profillari"

    def __str__(self):
        return self.full_name or self.username