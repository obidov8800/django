# tests/models.py

from django.db import models
from users.models import StudentProfile
from django.utils import timezone

class Group(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    resit_group = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class TestSchedule(models.Model):
    title = models.CharField(max_length=255)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='test_schedules')
    # pdf_file = models.FileField(upload_to='test_pdfs/', blank=True, null=True) # BU QATORNI O'CHIRING!
    num_questions = models.IntegerField(default=20)
    open_time = models.DateTimeField()
    close_time = models.DateTimeField()
    # questions = models.ManyToManyField(Question, blank=True) # BU QATORNI O'CHIRING!

    def __str__(self):
        return f"{self.title} ({self.group.name})"

    @property
    def is_active(self):
        now = timezone.now()
        return self.open_time <= now < self.close_time

    @property
    def is_upcoming(self):
        now = timezone.now()
        return now < self.open_time

    @property
    def is_finished(self):
        now = timezone.now()
        return now >= self.close_time

class Question(models.Model):
    # Bu maydon Question modelini qaysi TestSchedulega tegishli ekanligini belgilaydi
    test_schedule = models.ForeignKey(TestSchedule, on_delete=models.CASCADE, related_name='questions', null=True, blank=True)
    question_text = models.TextField()

    def __str__(self):
        return self.question_text

class AnswerOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answer_options')
    answer_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.answer_text} ({'Correct' if self.is_correct else 'Incorrect'})"

class TestResult(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='test_results')
    test = models.ForeignKey(TestSchedule, on_delete=models.CASCADE, related_name='results')
    score = models.IntegerField()
    completion_time = models.DateTimeField(auto_now_add=True)
    grade = models.CharField(max_length=50, blank=True, null=True)
    grade_color = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.student.full_name} - {self.test.title}: {self.score}"

    def save(self, *args, **kwargs):
        if self.score >= 76:
            self.grade = '5'
            self.grade_color = 'blue'
        elif self.score >= 60:
            self.grade = '4'
            self.grade_color = 'yellow' # Rangni "yellow" ga o'zgartirdik
        elif self.score >= 30:
            self.grade = '2'
            self.grade_color = 'black'
        else:
            self.grade = 'You failed the test'
            self.grade_color = 'red'
        super().save(*args, **kwargs)