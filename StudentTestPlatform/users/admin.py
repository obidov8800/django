from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import StudentProfile # Faqat StudentProfile ni import qiling!

# UserAdmin ni kengaytiramiz, chunki StudentProfile AbstractUser dan meros olgan
class StudentProfileAdmin(UserAdmin):
    # Qo'shimcha maydonlarni admin panelida ko'rsatish uchun
    fieldsets = UserAdmin.fieldsets + (
        (('Shaxsiy ma\'lumotlar'), {'fields': ('full_name', 'passport_number', 'phone_number', 'address', 'group', 'profile_picture')}),
    )
    # Ro'yxatda ko'rsatiladigan maydonlar
    list_display = ('username', 'full_name', 'phone_number', 'group', 'is_staff', 'is_active')
    # Filterlar
    list_filter = ('is_active', 'is_staff', 'group')
    # Qidiruv maydonlari
    search_fields = ('username', 'full_name', 'passport_number', 'phone_number')
    ordering = ('username',)

# Modelni admin paneliga ro'yxatdan o'tkazamiz
admin.site.register(StudentProfile, StudentProfileAdmin)

# BU FAYLDA GROUP GA OID HECH QANDAY KOD YOKI IMPORT QATORI BO'LMASLIGI KERAK!