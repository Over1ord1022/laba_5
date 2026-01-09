import os
import uuid
from django.db import models
import xml.etree.ElementTree as ET
from django.conf import settings
from xml.etree.ElementTree import ParseError
from .models import StatStudent

#Data Base


def save_statstudent_to_db(statstudent_data):
    try:
        # Проверяем на дубликат
        duplicate = StatStudent.objects.filter(
            name=statstudent_data['name'],
            subject=statstudent_data['subject'],
            grade=statstudent_data['grade'],
            date=statstudent_data['date'],
            teacher=statstudent_data.get('teacher', ''),
            cafedra=statstudent_data.get('cafedra', '')
        ).exists()
        
        if duplicate:
            return False, "Студент уже существует в базе данных"
        
        # Создаем новую оценку
        statstudent = StatStudent.objects.create(
            name=statstudent_data['name'],
            subject=statstudent_data['subject'],
            grade=statstudent_data['grade'],
            date=statstudent_data['date'],
            teacher=statstudent_data.get('teacher', ''),
            cafedra=statstudent_data.get('cafedra', '')
        )
        return True, "Оценка успешно сохранена в базу данных"
    
    except Exception as e:
        return False, f"Ошибка при сохранении в БД: {str(e)}"


def search_statstudent_in_db(query):
    if not query:
        return StatStudent.objects.all()
    
    return StatStudent.objects.filter(
        models.Q(name__istartswith=query) |
        models.Q(subject__istartswith=query) |
        models.Q(grade__istartswith=query) |
        models.Q(date__istartswith=query) |
        models.Q(teacher__istartswith=query) |
        models.Q(cafedra__istartswith=query)
    ).order_by('-date')

def get_all_statstudent_from_db():
    return StatStudent.objects.all().order_by('-date')

#XML

# Возвращает путь к директории для XML файлов успеваемости
def get_grades_xml_dir():
    return os.path.join(settings.MEDIA_ROOT, 'grades_xml')

# Создает директорию для XML файлов успеваемости
def ensure_grades_dir():
    grades_dir = get_grades_xml_dir()
    if not os.path.exists(grades_dir):
        os.makedirs(grades_dir)
    return grades_dir

# Генерирует уникальное имя для XML файла
def generate_xml_filename():
    return f"grades_{uuid.uuid4().hex[:8]}.xml"

# Сохраняет оценку студента в XML файл
def save_grade_to_xml(grade_data):
    grades_dir = ensure_grades_dir()
    file_path = os.path.join(grades_dir, 'grades.xml')

    try:
        if os.path.exists(file_path):
            # Если файл существует, добавляем новую оценку
            tree = ET.parse(file_path)
            root = tree.getroot()
        else:
            # Создаем новый файл
            root = ET.Element('StudentsGrades')
            tree = ET.ElementTree(root)

        # Создаем элемент оценки
        grade = ET.Element('Grade')
        
        ET.SubElement(grade, 'StudentName').text = grade_data['name']
        ET.SubElement(grade, 'Subject').text = grade_data['subject']
        ET.SubElement(grade, 'GradeValue').text = grade_data['grade']
        ET.SubElement(grade, 'Date').text = grade_data['date'].isoformat()
        if grade_data.get('teacher'):
            ET.SubElement(grade, 'Teacher').text = grade_data['teacher']
        if grade_data.get('cafedra'):
            ET.SubElement(grade, 'Cafedra').text = grade_data['cafedra']

        root.append(grade)

        # Сохраняем файл
        tree.write(file_path, encoding='utf-8', xml_declaration=True)
        return True

    except Exception as e:
        print(f"Error saving to XML: {e}")
        return False

# Получает все оценки из основного XML файла
def get_all_grades_from_xml():
    grades_dir = get_grades_xml_dir()
    file_path = os.path.join(grades_dir, 'grades.xml')
    grades = []

    if not os.path.exists(file_path):
        return grades

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        for grade_elem in root.findall('Grade'):
            grade = {
                'name': grade_elem.find('StudentName').text if grade_elem.find('StudentName') is not None else '',
                'subject': grade_elem.find('Subject').text if grade_elem.find('Subject') is not None else '',
                'grade': grade_elem.find('GradeValue').text if grade_elem.find('GradeValue') is not None else '',
                'date': grade_elem.find('Date').text if grade_elem.find('Date') is not None else '',
                'teacher': grade_elem.find('Teacher').text if grade_elem.find('Teacher') is not None else '',
                'cafedra': grade_elem.find('Cafedra').text if grade_elem.find('Cafedra') is not None else '',
            }
            grades.append(grade)

    except (ParseError, ET.ParseError) as e:
        print(f"Error parsing XML: {e}")

    return grades

# Проверяет валидность XML файла
def validate_xml_file(file_path):
    try:
        ET.parse(file_path)
        return True
    except (ParseError, ET.ParseError):
        return False

# Извлекает оценки из загруженного XML файла
def get_grades_from_uploaded_xml(file_path):
    grades = []
    if not validate_xml_file(file_path):
        return grades

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        for grade_elem in root.findall('.//Grade'):
            grade = {}
            name_elem = grade_elem.find('StudentName')
            subject_elem = grade_elem.find('Subject')
            grade_elem_val = grade_elem.find('GradeValue')
            date_elem = grade_elem.find('Date')
            teacher_elem = grade_elem.find('Teacher')
            cafedra_elem = grade_elem.find('Cafedra')

            if name_elem is not None:
                grade['name'] = name_elem.text
            if subject_elem is not None:
                grade['subject'] = subject_elem.text
            if grade_elem_val is not None:
                grade['grade'] = grade_elem_val.text
            if date_elem is not None:
                grade['date'] = date_elem.text
            if teacher_elem is not None:
                grade['teacher'] = teacher_elem.text
            if cafedra_elem is not None:
                grade['cafedra'] = cafedra_elem.text

            if grade:  # Добавляем только если есть основные поля
                grades.append(grade)

    except Exception as e:
        print(f"Error reading uploaded XML: {e}")

    return grades

# Возвращает список всех XML файлов в директории
def get_all_xml_files():
    grades_dir = ensure_grades_dir()
    xml_files = []

    for filename in os.listdir(grades_dir):
        if filename.endswith('.xml'):
            file_path = os.path.join(grades_dir, filename)
            file_info = {
                'filename': filename,
                'filepath': file_path,
                'size': os.path.getsize(file_path),
                'is_valid': validate_xml_file(file_path)
            }
            xml_files.append(file_info)

    return xml_files