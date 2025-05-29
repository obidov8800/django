# tests/forms.py

from django import forms
from .models import Group

class DuplicateTestForm(forms.Form):
    """
    Testlarni nusxalash uchun forma.
    Qaysi guruhlarga nusxalashni tanlash imkonini beradi.
    """
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Nusxalash uchun guruh(lar)ni tanlang",
        help_text="Tanlangan test(lar) ushbu guruh(lar)ga nusxalanadi."
    )


class DuplicateTestForm(forms.Form):
    """
    Testlarni nusxalash uchun forma.
    Qaysi guruhlarga nusxalashni tanlash imkonini beradi.
    """
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Nusxalash uchun guruh(lar)ni tanlang",
        help_text="Tanlangan test(lar) ushbu guruh(lar)ga nusxalanadi."
    )

class ImportQuestionsForm(forms.Form): # YANGI FORMA
    """
    Excel/CSV faylidan savollarni import qilish uchun forma.
    """
    file = forms.FileField(
        label="Savollar faylini yuklash",
        help_text="Excel (.xlsx, .xls) yoki CSV (.csv) formatidagi faylni yuklang. Ustunlar: 'Question Text', 'Option 1', 'Option 2', 'Option 3', 'Option 4', 'Correct Option Number (1-4)' bo'lishi kerak."
    )