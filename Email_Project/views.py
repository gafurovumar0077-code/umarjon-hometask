from django.shortcuts import render, redirect
from django.core.mail import send_mail
from .models import *
from random import randint
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required

def registration(request):
    if request.method == 'POST':
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get('password')
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_active=False
        )
        user.save()
        
        code = str(randint(10000000, 99999999))
        EmailConfirm.objects.update_or_create(
            user=user,
            code=code
        )
        send_mail(
            "Comfirm your email",
            f"Your code: {code}",
            'norep1y@softclub.tj',
            [user.email]
        )
        return redirect('confirm_email')
    return render(request, "registration.html")



def confirm_email(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        code = request.POST.get('code')
        user = User.objects.filter(username=username).first()
        code_obj = EmailConfirm.objects.filter(user=user).first()
        
        if code_obj and code_obj.code == code:
            user.is_active = True
            user.save()
            login(request, user)
            return redirect('profile')
        else:
            return redirect("confirm_email")
    return render(request, 'confirm_email.html')


def login_user(request):
    if request.method == 'POST':
        data = request.POST
        user = authenticate(request, username = data['username'], password = data['password'])
        if user is not None:
            login(request, user)
            return redirect('profile')
        else:
            return redirect("login")
    
    return render(request, "login.html")



@login_required
def show_profile(request):
    query = request.GET.get('q', '')
    tasks = Task.objects.filter(user=request.user, title__icontains=query)
    return render(request, 'profile.html', {'tasks': tasks, 'query': query})


@login_required
def create_task(request):
    if request.method == 'POST':
        Task.objects.create(
            user=request.user,
            title=request.POST['title'],
            description=request.POST.get('description'),
            is_completed=request.POST.get('is_completed') == 'on'
        )
        return redirect('profile')

    return render(request, 'create_task.html')


@login_required
def read_task(request, task_id):
    task = Task.objects.filter(pk=task_id, user=request.user).first()
    if task is None:
        return redirect('profile')
    return render(request, 'read_task.html', {'task': task})



@login_required
def task_update(request, task_id):
    tasks = Task.objects.filter(pk=task_id, user=request.user)
    task = tasks.first()
    if task is None:
        return redirect('profile')
    if request.method == 'POST':
        tasks.update(
            title=request.POST['title'],
            description=request.POST.get('description'),
            is_completed=request.POST.get('is_completed') == 'on'
        )
        return redirect('profile')
    return render(request, 'update_task.html', {'task': task})
    



@login_required
def task_delete(request, task_id):
    if request.method == 'POST':
        Task.objects.filter(pk=task_id, user=request.user).delete()
    return redirect('profile')

