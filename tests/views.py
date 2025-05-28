from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test # user_passes_test ni qo'shamiz
from django.contrib import messages
from django.utils import timezone
from .models import TestSchedule, Question, AnswerOption, TestResult, Group
from users.models import StudentProfile # StudentProfile ni import qilishni unutmang
from .forms import ImportQuestionsForm
import pandas as pd
# PDF generatsiya qilish uchun kerakli importlar
from django.http import HttpResponse # Bu yangi import
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape # landscape ni qo'shdik gorizontal PDF uchun
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch # inch birligini qo'shdik

# Testlar ro'yxatini ko'rsatish view'i
@login_required
def test_list_view(request):
    student_profile = request.user

    current_time = timezone.now()
    tests = TestSchedule.objects.filter(
        group=student_profile.group
    ).exclude(
        close_time__lt=current_time
    ).order_by('open_time')

    test_data = []
    for test in tests:
        # Talaba bu testni topshirganmi?
        # Agar topshirgan bo'lsa, TestResult ob'ektini ham olamiz
        # get() ishlatamiz, chunki bitta talaba bitta testni faqat bir marta topshiradi
        test_result = TestResult.objects.filter(student=student_profile, test=test).first()
        has_taken = test_result is not None # Agar natija ob'ekti mavjud bo'lsa, topshirilgan

        test_data.append({
            'test': test,
            'has_taken': has_taken,
            'result_id': test_result.id if test_result else None, # Natija ID'sini ham qo'shamiz
        })

    context = {
        'test_data': test_data,
    }
    return render(request, 'tests/test_list.html', context)

# Test topshirish view'i
@login_required
def take_test_view(request, test_id):
    student = request.user
    test_schedule = get_object_or_404(TestSchedule, id=test_id)

    # Test faol yoki hali boshlanmaganligini tekshiramiz
    current_time = timezone.now()
    if not (test_schedule.open_time <= current_time < test_schedule.close_time):
        messages.error(request, "Test faol emas yoki vaqti tugagan.")
        return redirect('test_list')

    # Talaba testni allaqachon topshirganmi?
    if TestResult.objects.filter(student=student, test=test_schedule).exists():
        messages.warning(request, "Siz bu testni allaqachon topshirgansiz.")
        # Agar topshirilgan bo'lsa, natija sahifasiga yo'naltiramiz
        existing_result = TestResult.objects.get(student=student, test=test_schedule)
        return redirect('test_result_detail', result_id=existing_result.id)

    questions = test_schedule.questions.all().prefetch_related('answer_options')

    # Agar testda savollar bo'lmasa
    if not questions.exists():
        messages.warning(request, "Ushbu test uchun savollar mavjud emas.")
        return redirect('test_list')

    if request.method == 'POST':
        score = 0
        correct_answers_count = 0
        total_questions = questions.count()

        for question in questions:
            selected_answer_id = request.POST.get(f'question_{question.id}')
            if selected_answer_id:
                try:
                    selected_option = AnswerOption.objects.get(id=selected_answer_id, question=question)
                    if selected_option.is_correct:
                        score += 3 # Har bir to'g'ri javobga 1 ball
                        correct_answers_count += 3
                except AnswerOption.DoesNotExist:
                    pass # Agar javob topilmasa, hech narsa qilmaymiz

        # Natijani saqlash
        test_result = TestResult.objects.create(
            student=student,
            test=test_schedule,
            score=score
        )
        test_result.save() # save() metodi baho va rangni avtomatik hisoblaydi

        messages.success(request, f"Test muvaffaqiyatli topshirildi! Siz {score} ball to'pladingiz.")
        return redirect('test_result_detail', result_id=test_result.id) # Natija sahifasiga yo'naltiramiz
    else:
        context = {
            'test_schedule': test_schedule,
            'questions': questions,
        }
        return render(request, 'tests/take_test.html', context)


# Test natijasini ko'rsatish view'i
@login_required
def test_result_detail_view(request, result_id):
    test_result = get_object_or_404(TestResult, id=result_id, student=request.user) # Faqat o'zining natijasini ko'rishi uchun

    context = {
        'test_result': test_result,
    }
    return render(request, 'tests/test_result_detail.html', context)

# Admin tekshiruvi funksiyasi
def is_admin(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin) # Faqat adminlar kirishi mumkin
def export_results_pdf_view(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="test_natijalari.pdf"'

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4)) # Gorizontal A4 o'lchami
    styles = getSampleStyleSheet()
    story = []

    # Sarlavha
    story.append(Paragraph("Umumiy Test Natijalari Ro'yxati", styles['h1']))
    story.append(Spacer(1, 0.2 * inch))

    # Ma'lumotlar bazasidan barcha natijalarni olish
    # StudentProfile modelidagi 'full_name', 'passport_number', 'phone_number' maydonlaridan foydalanamiz
    results = TestResult.objects.all().order_by('student__group__name', 'student__full_name', 'test__title')

    if not results:
        story.append(Paragraph("Hech qanday test natijalari topilmadi.", styles['Normal']))
    else:
        # Jadval ustunlari
        data = [['F.I.Sh.', 'Pasport', 'Telefon', 'Guruh', 'Test nomi', 'Ball', 'Baho', 'Topshirilgan vaqt']]

        for res in results:
            student_full_name = res.student.full_name
            student_passport = res.student.passport_number
            student_phone = res.student.phone_number
            student_group = res.student.group.name if res.student.group else 'Noma\'lum'
            test_title = res.test.title
            score = str(res.score)
            grade = res.grade
            completion_time = res.completion_time.strftime("%Y-%m-%d %H:%M")

            data.append([
                student_full_name,
                student_passport,
                student_phone,
                student_group,
                test_title,
                score,
                grade,
                completion_time
            ])

        # Jadvalni yaratish
        table = Table(data)

        # Jadval stili
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen), # Sarlavha qatori foni
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black), # Sarlavha matni rangi

            ('ALIGN', (0, 0), (-1, -1), 'CENTER'), # Barcha matnni markazga
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), # Sarlavha shrifti
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

            ('BACKGROUND', (0, 1), (-1, -1), colors.beige), # Qolgan qatorlar foni
            ('GRID', (0, 0), (-1, -1), 1, colors.black), # Ramka
            ('BOX', (0, 0), (-1, -1), 1, colors.black), # Tashqi ramka
            ('LEFTPADDING', (0,0), (-1,-1), 3),
            ('RIGHTPADDING', (0,0), (-1,-1), 3),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))

        # Jadval ustunlari kengligini sozlash (qulay ko'rinishi uchun)
        # A4 landscape 841.89 x 595.27 points
        col_widths = [2.2*inch, 1*inch, 1.2*inch, 1*inch, 1.8*inch, 0.5*inch, 0.5*inch, 1.2*inch]
        table._argW = col_widths

        story.append(table)

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response

@user_passes_test(is_admin)
def import_questions_from_file_view(request, test_id):
    test_schedule = get_object_or_404(TestSchedule, id=test_id)

    if request.method == 'POST':
        form = ImportQuestionsForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']

            try:
                # Fayl formatini aniqlash va o'qish
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                elif uploaded_file.name.endswith(('.xls', '.xlsx')):
                    df = pd.read_excel(uploaded_file)
                else:
                    messages.error(request, "Fayl formati noto'g'ri. Faqat Excel (.xls, .xlsx) yoki CSV (.csv) fayllari qabul qilinadi.")
                    return render(request, 'tests/import_questions.html', {'form': form, 'test_schedule': test_schedule})

                # Kerakli ustunlar mavjudligini tekshirish
                required_columns = ['Question Text', 'Option 1', 'Option 2', 'Option 3', 'Option 4', 'Correct Option Number']
                if not all(col in df.columns for col in required_columns):
                    messages.error(request, f"Faylda quyidagi majburiy ustunlar yo'q: {', '.join(required_columns)}. Iltimos, fayl tuzilishini tekshiring.")
                    return render(request, 'tests/import_questions.html', {'form': form, 'test_schedule': test_schedule})

                questions_count = 0
                for index, row in df.iterrows():
                    question_text = row['Question Text']
                    option1 = row['Option 1']
                    option2 = row['Option 2']
                    option3 = row['Option 3']
                    option4 = row['Option 4']
                    correct_option_number = int(row['Correct Option Number'])

                    # Savolni yaratish
                    question = Question.objects.create(
                        test_schedule=test_schedule,
                        question_text=question_text
                    )
                    questions_count += 1

                    # Javob variantlarini yaratish
                    AnswerOption.objects.create(question=question, answer_text=option1, is_correct=(correct_option_number == 1))
                    AnswerOption.objects.create(question=question, answer_text=option2, is_correct=(correct_option_number == 2))
                    AnswerOption.objects.create(question=question, answer_text=option3, is_correct=(correct_option_number == 3))
                    AnswerOption.objects.create(question=question, answer_text=option4, is_correct=(correct_option_number == 4))

                # Testning savollar sonini yangilash
                test_schedule.num_questions = test_schedule.questions.count()
                test_schedule.save()

                messages.success(request, f"{questions_count} ta savol muvaffaqiyatli import qilindi!")
                return redirect('admin:tests_testschedule_change', test_schedule.id) # Admin test detail sahifasiga qaytish

            except Exception as e:
                messages.error(request, f"Faylni qayta ishlashda xatolik yuz berdi: {e}. Iltimos, fayl tarkibi va formatini tekshiring.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
    else:
        form = ImportQuestionsForm()

    context = {
        'form': form,
        'test_schedule': test_schedule,
        'title': f"'{test_schedule.title}' testi uchun savollarni import qilish",
    }
    return render(request, 'tests/import_questions.html', context)