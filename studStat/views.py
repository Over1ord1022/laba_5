import os
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.http import FileResponse, Http404
from django.conf import settings
from django.contrib import messages
from django.db import models
from .forms import StudentForm, UploadXMLForm, StudentEditForm, DataSourceForm
from .models import StatStudent
from .utils import (
    save_grade_to_xml, get_all_grades_from_xml,
    validate_xml_file, get_grades_from_uploaded_xml,
    get_all_xml_files, generate_xml_filename, ensure_grades_dir, get_grades_xml_dir,
    save_statstudent_to_db, search_statstudent_in_db, get_all_statstudent_from_db
)

# Форма для ввода оценки студента
def student_form(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            grade_data = form.cleaned_data
            save_to = grade_data.pop('save_to')  # Убираем поле выбора

            if save_to == 'db':
                # Сохраняем в базу данных
                success, message = save_statstudent_to_db(grade_data)
                if success:
                    messages.success(request, message)
                else:
                    messages.error(request, message)
                return redirect('grades_list')
            else:
                # Сохраняем в XML
                if save_grade_to_xml(grade_data):
                    messages.success(request, 'Оценка успешно сохранена в XML файл!')
                    return redirect('grades_list')
                else:
                    messages.error(request, 'Ошибка при сохранении оценки в XML')
    else:
        form = StudentForm()

    return render(request, 'student_form.html', {'form': form})

# Список всех оценок из основного XML файла
def grades_list(request):
    source_form = DataSourceForm(request.GET or None)
    source = request.GET.get('source', 'db') #Получаем выбранный источник данных (или 'db' по умолчанию)

    if source == 'db':
        grades = get_all_statstudent_from_db()
        from_db = True
    else:
        grades = get_all_grades_from_xml()
        from_db = False
    
    context = {
        'grades': grades,
        'has_grades': len(grades) > 0,
        'source_form': source_form,
        'from_db': from_db,
        'current_source': source
    }
    return render(request, 'grades_list.html', context)

#AJAX поиск оценок в базе данных
def ajax_search(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        query = request.GET.get('q', '').strip()
        
        if query:
            # Улучшенный поиск с учетом разных форматов данных
            grades = StatStudent.objects.filter(
                models.Q(name__icontains=query) |
                models.Q(subject__icontains=query) |
                models.Q(grade__icontains=query) |
                models.Q(teacher__icontains=query) |
                models.Q(cafedra__icontains=query) |
                models.Q(date__icontains=query)  # Поиск по дате как строке
            ).order_by('-date')
            
            results = []
            for grade in grades:
                results.append({
                    'id': grade.id,
                    'name': grade.name or '-',
                    'subject': grade.subject or '-',
                    'grade': grade.grade or '-',
                    'date': grade.date.strftime('%Y-%m-%d') if grade.date else '-',
                    'teacher': grade.teacher or '-',
                    'cafedra': grade.cafedra or '-'
                })
            return JsonResponse({'grades': results, 'query': query})
        else:
            # Если запрос пустой, возвращаем все оценки
            grades = get_all_statstudent_from_db()
            results = []
            for grade in grades:
                results.append({
                    'id': grade.id,
                    'name': grade.name or '-',
                    'subject': grade.subject or '-',
                    'grade': grade.grade or '-',
                    'date': grade.date.strftime('%Y-%m-%d') if grade.date else '-',
                    'teacher': grade.teacher or '-',
                    'cafedra': grade.cafedra or '-'
                })
            return JsonResponse({'grades': results})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

# Редактирование оценки
def edit_grade(request, grade_id):
    grade = get_object_or_404(StatStudent, id=grade_id) #Ищем оценку через grade_id
    
    if request.method == 'POST':
        form = StudentEditForm(request.POST, instance=grade)
        if form.is_valid():
            #Проверка на дубликаты
            name = form.cleaned_data['name']
            subject = form.cleaned_data['subject']
            grade_value = form.cleaned_data['grade']
            date = form.cleaned_data['date']
            teacher = form.cleaned_data['teacher']
            cafedra = form.cleaned_data['cafedra']
            duplicate = StatStudent.objects.filter(
                name=name,
                subject=subject,
                grade=grade_value,
                date=date,
                teacher=teacher,
                cafedra=cafedra

            ).exclude(id=grade_id).exists()
            if duplicate:
                messages.error(request, 'Данный студент уже существует')
            else:
                form.save()
                messages.success(request, 'Оценка успешно обновлена!')
                return redirect('grades_list')
        else:
            messages.error(request, 'Данный студент уже существует')
            return redirect('grades_list')
    else:
        form = StudentEditForm(instance=grade)
    
    return render(request, 'edit_grade.html', {
        'form': form,
        'grade': grade
    })

# Удаление контакта
def delete_grade(request, grade_id):
    grade = get_object_or_404(StatStudent, id=grade_id)
    
    if request.method == 'POST':
        grade.delete()
        messages.success(request, 'Оценка успешно удалена!')
        return redirect('grades_list')
    
    return render(request, 'delete_grade.html', {'grade': grade})



# Загрузка XML файла с оценками
def upload_xml(request):
    if request.method == 'POST':
        form = UploadXMLForm(request.POST, request.FILES)
        if form.is_valid():
            xml_file = request.FILES['xml_file']

            # Генерируем безопасное имя файла
            safe_filename = generate_xml_filename()
            upload_dir = ensure_grades_dir()
            file_path = os.path.join(upload_dir, safe_filename)

            # Сохраняем файл
            with open(file_path, 'wb+') as destination:
                for chunk in xml_file.chunks():
                    destination.write(chunk)

            # Проверяем валидность XML
            if validate_xml_file(file_path):
                messages.success(request, f'Файл {xml_file.name} успешно загружен и проверен!')
                return redirect('xml_files_list')
            else:
                # Удаляем невалидный файл
                os.remove(file_path)
                messages.error(request, 'Файл не является валидным XML. Файл удален.')
    else:
        form = UploadXMLForm()

    return render(request, 'upload_xml.html', {'form': form})

# Список всех XML файлов и их содержимого
def xml_files_list(request):
    xml_files = get_all_xml_files()

    # Для каждого файла получаем оценки
    files_data = []
    for file_info in xml_files:
        grades = get_grades_from_uploaded_xml(file_info['filepath'])
        file_info['grades'] = grades
        file_info['grades_count'] = len(grades)
        files_data.append(file_info)

    context = {
        'files_data': files_data,
        'has_files': len(files_data) > 0
    }

    return render(request, 'xml_files_list.html', context)

# Просмотр содержимого конкретного XML файла
def view_xml_file(request, filename):
    grades_dir = ensure_grades_dir()
    file_path = os.path.join(grades_dir, filename)

    if not os.path.exists(file_path):
        messages.error(request, 'Файл не найден')
        return redirect('xml_files_list')

    if not validate_xml_file(file_path):
        messages.error(request, 'Файл не является валидным XML')
        return redirect('xml_files_list')

    grades = get_grades_from_uploaded_xml(file_path)

    context = {
        'filename': filename,
        'grades': grades,
        'has_grades': len(grades) > 0
    }

    return render(request, 'xml_file_detail.html', context)

# Скачивание XML файла
def download_xml_file(request, filename):
    grades_dir = get_grades_xml_dir()
    file_path = os.path.join(grades_dir, filename)

    if not os.path.exists(file_path):
        messages.error(request, 'Файл не найден')
        return redirect('xml_files_list')

    try:
        # Проверяем, что файл является XML
        if not filename.endswith('.xml'):
            messages.error(request, 'Файл не является XML')
            return redirect('xml_files_list')

        # Открываем файл для чтения в бинарном режиме
        response = FileResponse(open(file_path, 'rb'))
        
        # Устанавливаем заголовки для скачивания
        response['Content-Type'] = 'application/xml'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response

    except Exception as e:
        messages.error(request, f'Ошибка при скачивании файла: {str(e)}')
        return redirect('xml_files_list')