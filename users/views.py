# users/views.py

from django.shortcuts import render, redirect # render va redirect funksiyalari uchun
from django.contrib.auth import login, authenticate, logout # Tizimga kirish/chiqish uchun
from django.contrib.auth.forms import AuthenticationForm # Standart login formasi uchun
from django.contrib.auth.decorators import login_required # Kirish talab qilinadigan view'lar uchun
from django.contrib import messages # Xabarnomalar uchun
from .forms import StudentRegistrationForm # Keyinroq yaratiladigan custom ro'yxatdan o'tish formasi uchun
from .models import StudentProfile # StudentProfile modelimiz uchun
from tests.models import TestResult

# Foydalanuvchini ro'yxatdan o'tkazish view'i
def register_view(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, request.FILES) # request.FILES rasm yuklash uchun
        if form.is_valid():
            user = form.save()
            login(request, user) # Foydalanuvchi ro'yxatdan o'tgandan so'ng avtomatik kirishi mumkin
            messages.success(request, "Ro'yxatdan muvaffaqiyatli o'tdingiz va tizimga kirdingiz!")
            return redirect('home') # 'home' sahifaga yo'naltiramiz (keyinchalik yaratiladi)
        else:
            # Formada xatolar bo'lsa, ularni foydalanuvchiga ko'rsatamiz
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
    else:
        form = StudentRegistrationForm()
    return render(request, 'users/register.html', {'form': form})

# Foydalanuvchini tizimga kiritish view'i
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Xush kelibsiz, {user.username}!")
                return redirect('home') # 'home' sahifaga yo'naltiramiz
            else:
                # authenticate muvaffaqiyatsiz bo'lsa
                messages.error(request, "Foydalanuvchi nomi yoki parol noto'g'ri. Iltimos, qayta urinib ko'ring.")
        else:
            # Forma validatsiyadan o'tmasa, xatolarni ko'rsatamiz
            # Umumiy xatolarni (non_field_errors) alohida ishlaymiz
            for error in form.non_field_errors():
                messages.error(request, error)
            
            # Har bir maydonning xatolarini ko'rsatamiz
            for field, errors in form.errors.items():
                if field != '__all__': # '__all__' maydonini o'tkazib yuboramiz, chunki u form.non_field_errors() tomonidan ishlanadi
                    for error in errors:
                        # try-except bloki qo'shildi, chunki ba'zi hollarda 'label' bo'lmasligi mumkin (masalan, password fields)
                        try:
                            field_label = form.fields[field].label
                        except KeyError:
                            field_label = field.replace('_', ' ').capitalize() # Agar label bo'lmasa, maydon nomidan yasamiz
                        messages.error(request, f"{field_label}: {error}")
            
            # Agar maydonga tegishli xatolardan keyin ham umumiy xabar kerak bo'lsa
            if not form.non_field_errors() and form.errors: # Faqat agar umumiy xatolar bo'lmasa va boshqa maydon xatolari bo'lsa
                messages.error(request, "Login ma'lumotlaringiz noto'g'ri. Iltimos, qayta urinib ko'ring.")

    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

# Foydalanuvchini tizimdan chiqarish view'i
@login_required # Faqat tizimga kirgan foydalanuvchilar kira oladi
def logout_view(request):
    logout(request)
    messages.info(request, "Tizimdan muvaffaqiyatli chiqdingiz.")
    return redirect('login') # 'login' sahifaga qaytamiz

# Talaba profilini ko'rsatish view'i
@login_required # Faqat tizimga kirgan foydalanuvchilar kira oladi
def profile_view(request):
    # Foydalanuvchi StudentProfile modeli ekanligini bilamiz, chunki AUTH_USER_MODEL ni o'zgartirganmiz.
    student_profile = request.user
    student_results = TestResult.objects.filter(student=student_profile).order_by('-completion_time')
    context = {
        'student_profile': student_profile,
        'group_name': student_profile.group.name if student_profile.group else 'Biriktirilmagan',
        'student_results': student_results,
    }
    return render(request, 'users/profile.html', context)

# Asosiy sahifa view'i
@login_required
def home_view(request):
    # Bu yerda siz foydalanuvchi tizimga kirgandan keyin ko'radigan ma'lumotlarni joylashtirishingiz mumkin.
    # Masalan, testlar ro'yxatiga yo'naltirish:
    return redirect('test_list')