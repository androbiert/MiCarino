# love_app/views.py
from django.shortcuts import render, redirect , get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm 
from django.contrib import messages
from .models import Message,Discussion
from .forms import MessageForm
from django.contrib.auth.models import User
from .forms import ProfileUpdateForm
from django.db.models import Q




from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ProfileUpdateForm

@login_required
def view_profile(request, user_id):
    profile_user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        if request.user.id != user_id:
            messages.error(request, 'لا يمكنك تحديث ملف شخصي لمستخدم آخر.')
            return redirect('view_profile', user_id=user_id)
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile_user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث الملف الشخصي بنجاح!')
            return redirect('view_profile', user_id=user_id)
        else:
            messages.error(request, 'حدث خطأ أثناء تحديث الملف الشخصي.')
    else:
        form = ProfileUpdateForm(instance=profile_user.profile)
    return render(request, 'main/profile.html', {
        'form': form,
        'profile': profile_user.profile,
        'profile_user': profile_user,
        'is_owner': request.user.id == user_id
    })
# @login_required
# def view_profile(request, user_id):
#     profile_user = get_object_or_404(User, id=user_id)
#     return render(request, 'main/profile.html', {'profile_user': profile_user})


def home(request):
    return render(request, 'main/home.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'main/login.html')

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'main/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def start_discussion(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    discussion = Discussion.objects.filter(
        participants=request.user
    ).filter(participants=other_user).first()

    if not discussion:
        discussion = Discussion.objects.create()
        discussion.participants.add(request.user, other_user)
    
    return redirect('discussion_detail', discussion_id=discussion.id)

@login_required
def discussion_detail(request, discussion_id):
    discussion = get_object_or_404(Discussion, id=discussion_id, participants=request.user)
    messages = discussion.messages.order_by('timestamp')
    other_participant = discussion.get_other_participant(request.user)

    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            Message.objects.create(
                discussion=discussion,
                sender=request.user,
                content=form.cleaned_data['content'],
                image=form.cleaned_data['image']
            )
            return redirect('discussion_detail', discussion_id=discussion_id)
    else:
        form = MessageForm()

    return render(request, 'main/discussion_detail.html', {
        'discussion': discussion,
        'messages': messages,
        'other_participant': other_participant,
        'form': form
    })
@login_required
def discussion_list(request):
    # Handle search query
    query = request.GET.get('q', '')
    users = []
    if query:
        users = User.objects.filter(username__icontains=query).exclude(id=request.user.id)

    # Fetch discussions
    discussions = Discussion.objects.filter(participants=request.user).prefetch_related('participants')
    discussion_data = []
    for discussion in discussions:
        other_participant = discussion.get_other_participant(request.user)
        discussion_data.append({
            'discussion': discussion,
            'other_participant': other_participant,
        })

    return render(request, 'main/discussion_list.html', {
        'discussion_data': discussion_data,
        'users': users,
        'query': query
    })

@login_required
def search_users(request):
    query = request.GET.get('q', '')
    users = User.objects.filter(username__icontains=query).exclude(id=request.user.id)
    return render(request, 'main/discussion_list.html', {
        'users': users,
        'query': query,
        'discussion_data': []  # Empty discussion data to avoid breaking the template
    })
@login_required
def start_discussion(request, user_id):
    if request.user.id == user_id:
        messages.error(request, 'لا يمكنك بدء مناقشة مع نفسك.')
        return redirect('discussion_list')
    other_user = get_object_or_404(User, id=user_id)
    discussion = Discussion.objects.filter(
        participants=request.user
    ).filter(participants=other_user).first()

    if not discussion:
        discussion = Discussion.objects.create()
        discussion.participants.add(request.user, other_user)
    
    return redirect('discussion_detail', discussion_id=discussion.id)

from django.http import JsonResponse
from django.template.loader import render_to_string
from django.http import JsonResponse

from django.http import JsonResponse

@login_required
def discussion_detail(request, discussion_id):
    discussion = get_object_or_404(Discussion, id=discussion_id, participants=request.user)
    messages = discussion.messages.order_by('timestamp')
    other_participant = discussion.get_other_participant(request.user)

    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = Message.objects.create(
                discussion=discussion,
                sender=request.user,
                content=form.cleaned_data['content'],
                image=form.cleaned_data['image']
            )
            # ✅ Return JSON for AJAX
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message_id': message.id,
                    'content': message.content,
                    'image': message.image.url if message.image else None,
                    'timestamp': message.timestamp.strftime("%H:%M"),
                    'sender_id': message.sender.id,
                    'sender_username': message.sender.username,
                    'sender_profile_image': message.sender.profile.image.url if message.sender.profile.image else '/media/profile_images/default.png'
                })
            return redirect('discussion_detail', discussion_id=discussion_id)

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Invalid form'}, status=400)

    return render(request, 'main/discussion_detail.html', {
        'discussion': discussion,
        'messages': messages,
        'other_participant': other_participant
    })


@login_required
def discussion_messages(request, discussion_id):
    discussion = get_object_or_404(Discussion, id=discussion_id, participants=request.user)
    last_id = request.GET.get('last_id', 0)
    messages = discussion.messages.filter(id__gt=last_id).order_by('timestamp')
    messages_data = [{
        'id': msg.id,
        'sender_id': msg.sender.id,
        'sender_username': msg.sender.username,
        'sender_profile_image': msg.sender.profile.image.url,
        'content': msg.content,
        'image': msg.image.url if msg.image else '',
        'timestamp': msg.timestamp.strftime('%H:%M')
    } for msg in messages]
    return JsonResponse({'messages': messages_data})