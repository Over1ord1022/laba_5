from django import forms
import re
from .models import StatStudent

#Форма добавления оценки
class StudentForm(forms.Form):
    SAVE_CHOICES = [
        ('db', 'Сохранить в базу данных'),
        ('xml', 'Сохранить в XML файл'),
    ]

    name = forms.CharField(
        label='ФИО студента',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    subject = forms.CharField(
        label='Предмет',
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    grade = forms.CharField(
        label='Оценка',
        max_length=10,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    date = forms.DateField(
        label='Дата оценки',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    teacher = forms.CharField(
        label='Преподаватель',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    cafedra = forms.CharField(
        label='Кафедра',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    save_to = forms.ChoiceField(
        label='Куда сохранить',
        choices=SAVE_CHOICES,
        initial='db',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )

    #Валидация
    def clean_name(self):
        name = self.cleaned_data['name']
        if not re.match(r'^[а-яА-Яa-zA-Z\s\-\.]+$', name):
            raise forms.ValidationError('ФИО может содержать только буквы, пробелы, дефисы и точки')
        return name

    def clean_grade(self):
        grade = self.cleaned_data['grade']
        if not re.match(r'^[1-5]|\d-\d|[A-F]|зачет|незачет$', grade.lower()):
            raise forms.ValidationError('Некорректный формат оценки')
        return grade

#Форма для редактирования контакта
class StudentEditForm(forms.ModelForm):
    class Meta:
        model = StatStudent
        fields = ['name', 'subject', 'grade', 'date', 'teacher', 'cafedra']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'grade': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'teacher': forms.TextInput(attrs={'class': 'form-control'}),
            'cafedra': forms.TextInput(attrs={'class': 'form-control'}),
        }

#Форма для отображения данных
class DataSourceForm(forms.Form):
    SOURCE_CHOICES = [
        ('db', 'База данных'),
        ('xml', 'XML файлы'),
    ]
    
    source = forms.ChoiceField(
        label='Источник данных',
        choices=SOURCE_CHOICES,
        initial='db',
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'source-selector'})
    )

#Форма загрузки xml-файла
class UploadXMLForm(forms.Form):
    xml_file = forms.FileField(
        label='XML файл с успеваемостью',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xml'})
    )