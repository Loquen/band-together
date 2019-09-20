from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.admin.views.decorators import staff_member_required
from .models import Venue, Event, Profile, Ticket
from .forms import EventForm
from django.conf import settings
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

def home(request):
  return render(request, 'home.html')

def signup(request):
  error_message = ''
  if request.method == 'POST':
    # This is how to create a 'user' form object
    # that includes the data from the browser
    form = UserCreationForm(request.POST)
    if form.is_valid():
      # This will add the user to the database
      user = form.save()
      # This is how we log a user in via code
      login(request, user)
      return redirect('home')
    else:
      error_message = 'Invalid sign up - try again'
  # A bad POST or a GET request, so render signup.html with an empty form
  form = UserCreationForm()
  context = {'form': form, 'error_message': error_message}
  return render(request, 'registration/signup.html', context)

@login_required
def event_index(request):
  events = Event.objects.all()
  return render(request, 'events/index.html', { 'events': events })

@login_required
def event_detail(request, event_id):
  event = Event.objects.get(id=event_id)
  return render(request, 'events/detail.html', { 'event': event, 'key': settings.STRIPE_PUBLISHABLE_KEY })

@staff_member_required
def event_create(request):
  if request.method == "POST":
    form = EventForm(request.POST, user=request.user)
    if form.is_valid():
      event = form.save(commit=False)
      event.total_tickets = event.venue.capacity
      event.save()
      return redirect('index')
  else:
    form = EventForm(user=request.user)
    return render(request, 'main_app/event_form.html', {'form': form})
  
class EventUpdate(LoginRequiredMixin, UpdateView):
  model = Event
  fields = ['artists', 'description', 'date']

class EventDelete(LoginRequiredMixin, DeleteView):
  model = Event
  success_url = '/events/'

@staff_member_required
def venue_index(request):
  venues = Venue.objects.filter(user=request.user)
  return render(request, 'venues/venue_index.html', {'venue_list': venues})

class VenueCreate(LoginRequiredMixin, CreateView):
  model = Venue
  fields = ['name', 'address', 'capacity', 'accessibility']
  success_url = '/venues/'

  def form_valid(self, form):
    form.instance.user = self.request.user
    return super().form_valid(form)

class VenueUpdate(LoginRequiredMixin, UpdateView):
  model = Venue
  fields = ['name','capacity', 'accessibility']
  success_url = '/venues/'


class VenueDelete(LoginRequiredMixin, DeleteView):
  model = Venue
  success_url = '/venues/'

@login_required
def ticket_create(request, event_id):
  charge = stripe.Charge.create(
      amount=500,
      currency='usd',
      description='A Ticket',
      source=request.POST['stripeToken']
  )
  event = Event.objects.get(id=event_id)
  ticket = Ticket(event=event, user=request.user)
  ticket.save()
  event.total_tickets -= 1
  event.save()
  return redirect('/profile/')

@login_required
def profile(request):
  tickets = Ticket.objects.filter(user=request.user)
  return render(request, 'profile.html', { 'tickets': tickets })