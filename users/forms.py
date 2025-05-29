# users/forms.py

from django import forms
from .models import StudentProfile # Faqat StudentProfile modelini import qilamiz!
from django.contrib.auth.forms import UserCreationForm
from tests.models import Group

class StudentRegistrationForm(UserCreationForm):
    """
    Talabani ro'yxatdan o'tkazish uchun maxsus forma.
    """
    # AbstractUser dan meros olinganligi sababli 'username' va 'password' avtomatik mavjud.
    # Bizning qo'shimcha maydonlarimiz:
    full_name = forms.CharField(max_length=255, label="To'liq ism (F.I.Sh.)")
    passport_number = forms.CharField(max_length=9, label="Pasport raqami")
    phone_number = forms.CharField(max_length=13, label="Telefon raqami",
                                   help_text="+998XXXXXXXXX formatida kiriting (masalan, +998901234567)")
    address = forms.CharField(max_length=255, label="Yashash manzili")
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        empty_label="Guruhni tanlang",
        label="Guruh",
        required=True # BU QATORNI QO'SHING
    )
    profile_picture = forms.ImageField(label="Profil rasmi", required=True)

    class Meta(UserCreationForm.Meta):
        model = StudentProfile
        # 'password' va 'password2' UserCreationForm dan avtomatik keladi
        fields = ('username', 'full_name', 'passport_number', 'phone_number', 'address', 'group', 'profile_picture',)

    # Custom validatsiya: Pasport raqami va telefon raqami uchun modeldagi validatorlar ishlaydi.
    # Agar siz formaga maxsus validatsiya qo'shmoqchi bo'lsangiz, clean_field_name() metodlarini qo'shishingiz mumkin.
    # Misol:
    # def clean_phone_number(self):
    #     phone_number = self.cleaned_data['phone_number']
    #     if not phone_number.startswith('+998'):
    #         raise forms.ValidationError("Telefon raqami +998 bilan boshlanishi kerak.")
    #     # ... qolgan validatsiya mantiqi
    #     return phone_number

    # __init__ metodini override qilish orqali barcha maydonlarga Bootstrap classlari berish
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['password', 'password2']: # Parol maydonlariga o'zgartirish kiritmaslik
                field.widget.attrs['class'] = 'form-control'
                # Agar maydon ModelChoiceField bo'lsa, maxsus style berish
                if isinstance(field, forms.ModelChoiceField):
                    field.widget.attrs['class'] += ' form-select'
                # Agar ImageField bo'lsa
                if isinstance(field, forms.ImageField):
                    field.widget.attrs['class'] = 'form-control-file' # yoki faqat 'form-control'