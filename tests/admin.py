# tests/admin.py

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.http import HttpResponseRedirect, HttpResponse # HttpResponse import qilinganligiga ishonch hosil qiling
from django.template.response import TemplateResponse
from django.contrib import messages

# Barcha kerakli modellarni import qilganingizga ishonch hosil qiling
from .models import Group, TestSchedule, Question, AnswerOption, TestResult

# Barcha kerakli formlarni import qilganingizga ishonch hosil qiling
from .forms import DuplicateTestForm, ImportQuestionsForm

# PDF generatsiya qilish uchun kerakli importlar
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch


# AnswerOption modelini Question ostida inline qilish uchun
class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 4
    max_num = 6
    min_num = 2

# Question modelini TestSchedule ostida inline qilish uchun
class QuestionInline(admin.TabularInline):
    model = Question
    inlines = [AnswerOptionInline]
    extra = 5
    max_num = 30
    min_num = 1


@admin.register(TestSchedule)
class TestScheduleAdmin(admin.ModelAdmin):
    list_display = ('title', 'group', 'open_time', 'close_time', 'num_questions', 'is_active', 'is_upcoming', 'is_finished', 'import_questions_link')
    list_filter = ('group', 'open_time', 'close_time')
    search_fields = ('title', 'group__name')
    inlines = [QuestionInline]
    
    actions = ['duplicate_tests', 'export_results_pdf_action']

    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)
        if formset.model == Question:
            test_schedule = formset.instance
            test_schedule.num_questions = test_schedule.questions.count()
            test_schedule.save()

    def import_questions_link(self, obj):
        url = reverse('import_questions', args=[obj.id])
        return format_html('<a href="{}">Savollarni import qilish</a>', url)
    import_questions_link.short_description = "Savol import"
    import_questions_link.allow_tags = True

    def duplicate_tests(self, request, queryset):
        form = None
        if 'apply' in request.POST:
            form = DuplicateTestForm(request.POST)
            if form.is_valid():
                selected_groups = form.cleaned_data['groups']
                duplicated_count = 0
                
                try: # <--- Xatolarni tutish uchun try-except bloki qo'shildi
                    for original_test in queryset:
                        for target_group in selected_groups:
                            new_test = TestSchedule(
                                title=f"{original_test.title} (Nusxa - {target_group.name})",
                                group=target_group,
                                num_questions=original_test.num_questions, # pdf_file olib tashlangan
                                open_time=original_test.open_time,
                                close_time=original_test.close_time
                            )
                            new_test.save()
                            
                            for original_question in original_test.questions.all():
                                new_question = Question(
                                    test_schedule=new_test,
                                    question_text=original_question.question_text
                                )
                                new_question.save()
                                
                                for original_answer_option in original_question.answer_options.all():
                                    new_answer_option = AnswerOption(
                                        question=new_question,
                                        answer_text=original_answer_option.answer_text,
                                        is_correct=original_answer_option.is_correct
                                    )
                                    new_answer_option.save()
                            duplicated_count += 1
                    
                    self.message_user(request, f"{duplicated_count} ta test muvaffaqiyatli nusxalandi.", messages.SUCCESS)
                    return HttpResponseRedirect(request.get_full_path())
                except Exception as e:
                    # Agar nusxalash jarayonida xato yuzaga kelsa, uni xabar qilib ko'rsatamiz
                    self.message_user(request, f"Testlarni nusxalashda xatolik yuz berdi: {e}", messages.ERROR)
                    # Xatoni server loglariga ham yozib qo'yish yaxshi amaliyot (buning uchun logging moduli kerak bo'ladi)
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.exception("Test duplication failed:")
            else:
                # Forma validatsiyadan o'tmasa, xabarni ko'rsatamiz
                self.message_user(request, "Nusxalash uchun hech bo'lmaganda bitta guruh tanlashingiz kerak.", messages.ERROR)
                # Forma xatolarini ham ko'rsatish mumkin, agar template da ko'rsatmasangiz
                for field, errors in form.errors.items():
                    for error in errors:
                        self.message_user(request, f"{form.fields[field].label}: {error}", messages.ERROR)


        if not form:
            form = DuplicateTestForm()
        
        context = {
            'title': "Tanlangan testlarni nusxalash",
            'queryset': queryset,
            'form': form,
            'action_name': 'duplicate_tests',
            'media': self.media,
            'opts': self.model._meta,
        }
        
        return TemplateResponse(request, 'admin/duplicate_tests_confirmation.html', context)
    
    duplicate_tests.short_description = "Tanlangan testlarni nusxalash"


    def export_results_pdf_action(self, request, queryset):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("Test Natijalari Hisoboti", styles['h1']))
        elements.append(Spacer(1, 0.2 * inch))

        data = [['Talaba F.I.Sh.', 'Pasport', 'Telefon', 'Guruh', 'Test Nomi', 'Ball', 'Baho', 'Topshirilgan Vaqt']]

        for test_schedule in queryset:
            test_results = TestResult.objects.filter(test=test_schedule).order_by('student__full_name')
            
            elements.append(Paragraph(f"Test: {test_schedule.title} ({test_schedule.group.name})", styles['h2']))
            elements.append(Spacer(1, 0.1 * inch))

            if not test_results.exists():
                elements.append(Paragraph("Bu test uchun natijalar mavjud emas.", styles['Normal']))
                elements.append(Spacer(1, 0.2 * inch))
                continue

            for res in test_results:
                student_full_name = res.student.full_name
                student_passport = res.student.passport_number
                student_phone = res.student.phone_number
                student_group = res.student.group.name if res.student.group else 'N/A'
                test_title = res.test.title
                score = res.score
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

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('LEFTPADDING', (0,0), (-1,-1), 3),
            ('RIGHTPADDING', (0,0), (-1,-1), 3),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))
        elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="test_natijalari_hisoboti.pdf"'
        return response

    export_results_pdf_action.short_description = "Tanlangan testlar natijalarini PDFga eksport qilish"


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'resit_group')
    search_fields = ('name',)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('test_schedule', 'question_text')
    list_filter = ('test_schedule',)
    search_fields = ('question_text',)
    inlines = [AnswerOptionInline]

@admin.register(AnswerOption)
class AnswerOptionAdmin(admin.ModelAdmin):
    list_display = ('question', 'answer_text', 'is_correct')
    list_filter = ('question', 'is_correct')
    search_fields = ('answer_text',)

@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'test', 'score', 'grade', 'completion_time')
    list_filter = ('test', 'student__group', 'grade')
    search_fields = ('student__full_name', 'test__title')
    readonly_fields = ('completion_time',)
    
    actions = ['export_selected_results_pdf_action']

    def export_selected_results_pdf_action(self, request, queryset):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("Tanlangan Test Natijalari Hisoboti", styles['h1']))
        elements.append(Spacer(1, 0.2 * inch))

        data = [['Talaba F.I.Sh.', 'Pasport', 'Telefon', 'Guruh', 'Test Nomi', 'Ball', 'Baho', 'Topshirilgan Vaqt']]
        
        for res in queryset:
            student_full_name = res.student.full_name
            student_passport = res.student.passport_number
            student_phone = res.student.phone_number
            student_group = res.student.group.name if res.student.group else 'N/A'
            test_title = res.test.title
            score = res.score
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

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('LEFTPADDING', (0,0), (-1,-1), 3),
            ('RIGHTPADDING', (0,0), (-1,-1), 3),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))
        elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="tanlangan_test_natijalari.pdf"'
        return response

    export_selected_results_pdf_action.short_description = "Tanlangan natijalarni PDFga eksport qilish"