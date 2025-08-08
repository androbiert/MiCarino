# love_app/views.py
from django.shortcuts import render, redirect , get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm 
from django.contrib import messages
from .models import Message,Discussion , DiscussionPresence
from .forms import MessageForm
from django.contrib.auth.models import User
from .forms import ProfileUpdateForm, MessageForm
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.db.models import Max
from django.views.decorators.http import require_POST

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
def discussion_list(request):
    # Handle search query
    query = request.GET.get('q', '')
    users = []
    if query:
        users = User.objects.filter(username__icontains=query).exclude(id=request.user.id)

    # Fetch discussions
    discussions = Discussion.objects.filter(participants=request.user).prefetch_related('participants').annotate(last_message_time=Max('messages__timestamp')) \
        .order_by('-last_message_time', '-created_at')
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


HEARTBEAT_WINDOW = timedelta(seconds=5)  # if user seen in last 20s -> consider them "online" in this discussion

@login_required
def discussion_detail(request, discussion_id):
    discussion = Discussion.objects.filter(
        id=discussion_id,
        participants=request.user
    ).first()

    if not discussion:
        messages.error(request, "المناقشة غير موجودة أو تم حذفها.")
        return redirect('discussion_list')
    # update presence immediately (user opened or refreshed page)
    obj, _ = DiscussionPresence.objects.get_or_create(discussion=discussion, user=request.user)
    obj.last_seen = timezone.now()
    obj.save()

    # mark unread messages from others as read (when user opens the page)
    Message.objects.filter(
        discussion=discussion,
        is_read=False
    ).exclude(sender=request.user).update(is_read=True)

    messages_qs = discussion.messages.order_by('timestamp')
    other_participant = discussion.get_other_participant(request.user)

    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = Message.objects.create(
                discussion=discussion,
                sender=request.user,
                content=form.cleaned_data.get('content', '').strip() or None,
                image=form.cleaned_data.get('image')
            )

            # check if recipient is currently "present" (heartbeat)
            recipient = other_participant
            presence = DiscussionPresence.objects.filter(discussion=discussion, user=recipient).first()
            if presence and timezone.now() - presence.last_seen <= HEARTBEAT_WINDOW:
                # recipient is viewing -> mark as read immediately
                message.is_read = True
                message.save()

            # If AJAX request -> return JSON (including is_read)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message_id': message.id,
                    'content': message.content,
                    'image': message.image.url if message.image else None,
                    'timestamp': message.timestamp.strftime("%H:%M"),
                    'sender_id': message.sender.id,
                    'sender_username': message.sender.username,
                    'sender_profile_image': (
                        message.sender.profile.image.url 
                        if getattr(message.sender, 'profile', None) and message.sender.profile.image 
                        else '/media/profile_images/default.png'
                    ),
                    'is_read': message.is_read
                })

            return redirect('discussion_detail', discussion_id=discussion_id)

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Invalid form'}, status=400)

    return render(request, 'main/discussion_detail.html', {
        'discussion': discussion,
        'messages': messages_qs,
        'other_participant': other_participant
    })

@login_required
def discussion_latest_messages(request, discussion_id):
    discussion = get_object_or_404(Discussion, id=discussion_id, participants=request.user)
    messages_qs = discussion.messages.order_by('-timestamp')[:10]
    messages_data = []
    for msg in reversed(messages_qs):  # reverse to get oldest first
        messages_data.append({
            'id': msg.id,
            'sender_id': msg.sender.id,
            'sender_username': msg.sender.username,
            'sender_profile_image': (
                msg.sender.profile.image.url
                if getattr(msg.sender, 'profile', None) and msg.sender.profile.image
                else '/media/profile_images/default.png'
            ),
            'content': msg.content,
            'image': msg.image.url if msg.image else '',
            'timestamp': msg.timestamp.strftime('%H:%M'),
            'is_read': msg.is_read,
            'likes_count': msg.likes_count(),
            'liked_by_user': request.user in msg.liked_by.all(),
        })
    return JsonResponse({'messages': messages_data})

@login_required
@require_POST
def toggle_message_like(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    if request.user in message.liked_by.all():
        message.liked_by.remove(request.user)
        liked = False
    else:
        message.liked_by.add(request.user)
        liked = True
    return JsonResponse({
    'likes_count': message.likes_count(),
    'liked_by_user': request.user in message.liked_by.all()

    })

def about_developer(request):
    return render(request, 'main/about_developer.html')



@login_required
def discussion_messages(request, discussion_id):
    discussion = get_object_or_404(Discussion, id=discussion_id, participants=request.user)
    last_id = int(request.GET.get('last_id', 0))
    messages_qs = discussion.messages.filter(id__gt=last_id).order_by('timestamp')
    messages_data = []
    for msg in messages_qs:
        messages_data.append({
            'id': msg.id,
            'sender_id': msg.sender.id,
            'sender_username': msg.sender.username,
            'sender_profile_image': (
                msg.sender.profile.image.url if getattr(msg.sender, 'profile', None) and msg.sender.profile.image else '/media/profile_images/default.png'
            ),
            'content': msg.content,
            'image': msg.image.url if msg.image else '',
            'timestamp': msg.timestamp.strftime('%H:%M'),
            'is_read': msg.is_read
        })
    return JsonResponse({'messages': messages_data})


@login_required
def discussion_heartbeat(request, discussion_id):
    discussion = get_object_or_404(Discussion, id=discussion_id, participants=request.user)
    obj, _ = DiscussionPresence.objects.get_or_create(discussion=discussion, user=request.user)
    obj.last_seen = timezone.now()
    obj.save()
    return JsonResponse({'status': 'ok', 'last_seen': obj.last_seen.isoformat()})


@login_required
def delete_discussion(request, discussion_id):
    discussion = get_object_or_404(Discussion, id=discussion_id)
    # check membership properly (participants is M2M)
    if request.user in discussion.participants.all():
        discussion.delete()
        messages.success(request, "تم حذف المناقشة بنجاح.")
    else:
        messages.error(request, "ليس لديك صلاحية لحذف هذه المناقشة.")
    return redirect('discussion_list')


@login_required
def check_new_messages(request):
    count = Message.objects.filter(
        discussion__participants=request.user,
        is_read=False
    ).exclude(sender=request.user).count()
    return JsonResponse({'unread_count': count})

@login_required
def mark_messages_read(request, discussion_id):
    discussion = get_object_or_404(Discussion, id=discussion_id, participants=request.user)

    Message.objects.filter(
        discussion=discussion,
        is_read=False
    ).exclude(sender=request.user).update(is_read=True)

    return JsonResponse({'status': 'success'})

