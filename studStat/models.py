from django.db import models

class StatStudent(models.Model):
    name = models.CharField(max_length=100, verbose_name='ФИО студента')
    subject = models.CharField(max_length=20, verbose_name='Предмет')
    grade = models.CharField(max_length=20, verbose_name='Оценка')
    date = models.DateField(verbose_name='Дата оценки')
    teacher = models.CharField(blank=True, null=True, max_length=100, verbose_name='Преподаватель')
    cafedra = models.CharField(blank=True, null=True, max_length=100, verbose_name='Кафедра')
    
    class Meta: #метаданные таблицы
        db_table = 'studstat'
        verbose_name = 'Оценка'
        verbose_name_plural = 'Оценки'
        unique_together = ['name', 'subject', 'grade', 'date']  # Для проверки дубликатов
    
    def __str__(self):
        return self.name