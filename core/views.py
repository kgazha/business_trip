from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, DetailView, ListView
from django.views.generic.edit import FormMixin, ModelFormMixin
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import permission_required, login_required
from django.forms.models import model_to_dict, fields_for_model
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Max
import pymorphy2

from .forms import BusinessTripForm, HeadOfDepartmentForm, DeputyGovernorForm,\
    PersonnelDepartmentForm, PurchasingDepartmentForm
from .models import BusinessTrip, BusinessTripQueue, Departments,\
    Document, DeputyGovernor, ActiveSetting,\
    EmailSending, Order, ApplicationFunding
from .utilities import get_file_stream, send_email


morph = pymorphy2.MorphAnalyzer()


def get_morphed_word(word, case):
    morphed = morph.parse(word)[0].inflect({case})
    if morphed:
        if word[0].isupper():
            return morphed.word.capitalize()
        else:
            return morphed.word
    return word


class BusinessTripView(View):

    form_class = BusinessTripForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        request_created = False
        if request.session.get('request_created'):
            request_created = request.session.pop('request_created')
        return render(request, 'business_trip_form.html', {'form': form,
                                                           'request_created': request_created,
                                                           'is_authenticated': request.user.is_authenticated})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            request.session['request_created'] = True
            instance = form.save(commit=False)
            instance.save()
            head_of_department_queue = BusinessTripQueue(queue=Departments.HEAD_OF_DEPARTMENT[0],
                                                         business_trip=instance)
            head_of_department_queue.save()
            send_email_by_queue(queue=Departments.HEAD_OF_DEPARTMENT[0])
        else:
            context = {'form': form,
                       'is_authenticated': request.user.is_authenticated}
            return render(request, 'business_trip_form.html', context=context)
        return HttpResponseRedirect('/')


class LoginView(View):
    form_class = AuthenticationForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, 'login.html', {'form': form,
                                              'is_authenticated': request.user.is_authenticated})

    def post(self, request, *args, **kwargs):
        form = self.form_class(data=request.POST)
        if request.POST['username'] and request.POST['password']:
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
            else:
                return render(request, 'login.html', {'form': form,
                                                      'is_authenticated': request.user.is_authenticated})
        return redirect('/business_trips/')


def logout_view(request):
    logout(request)
    return redirect('/')


def get_tabs(user_permissions):
    tabs = {'Все заявки': 'all'}
    for d in Departments.get_departments():
        if Departments().__getattribute__(d)[0] in user_permissions:
            tabs.update({Departments().__getattribute__(d)[1]: Departments().__getattribute__(d)[0].lower()})
    return tabs


class BusinessTripManagementView(ListView):

    model = BusinessTrip
    template_name = 'business_trip_management.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_permissions = get_user_permissions(self.request.user)
        allowed_tabs = get_tabs(user_permissions)
        business_trip_header = ['ФИО', 'Место командировки', 'Должность',
                                'Дата начала командировки', 'Дата окончания командировки']
        queue = self.request.GET.get('queue')
        if queue not in allowed_tabs.values():
            queue = 'all'
        status = self.request.GET.get('status')
        if not status:
            status = BusinessTripQueue.NEW
        elif True in [status.upper() in s for s in BusinessTripQueue.STATUS_CHOICES]:
            status = status.upper()
        if queue == 'all':
            business_trips = BusinessTripQueue.objects.values("business_trip", "status").annotate(Max("date_added"))
        else:
            if status:
                business_trips = BusinessTripQueue.objects.filter(queue=queue.upper(), status=status) \
                    .values("business_trip", "status").annotate(Max("date_added"))
            else:
                business_trips = BusinessTripQueue.objects.filter(queue=queue.upper())\
                    .values("business_trip", "status")
        business_trip_ids = [_['business_trip'] for _ in business_trips]
        business_trip_list = BusinessTrip.objects.filter(id__in=business_trip_ids)
        paginator = Paginator(business_trip_list, 5)
        page = self.request.GET.get('page')
        business_trip_objects = paginator.get_page(page)
        business_trip_content = []
        for obj in business_trip_objects:
            business_trip_content.append([
                obj.id,
                ' '.join([obj.second_name, obj.first_name, obj.patronymic]),
                obj.location,
                obj.position,
                str(obj.start_date),
                str(obj.end_date),
            ])
        href_args = ''
        if queue and status:
            href_args = 'queue=' + queue + '&status=' + status
        elif queue:
            href_args = 'queue=' + queue
        context['href_args'] = href_args
        context['current_queue'] = queue
        context['tabs'] = allowed_tabs
        context['business_trip_header'] = business_trip_header
        context['business_trip_content'] = business_trip_content
        context['is_authenticated'] = self.request.user.is_authenticated
        if queue == Departments.HEAD_OF_DEPARTMENT[0].lower():
            context['statuses'] = BusinessTripQueue.STATUS_CHOICES
        else:
            context['statuses'] = BusinessTripQueue.STATUS_CHOICES[:-1]
        context['active_status'] = status.lower()
        context['business_trip_objects'] = business_trip_objects
        return context


def get_user_permissions(user):
    permissions = []
    for department in Departments.get_departments():
        if user.has_perm('core.' + department):
            permissions.append(department)
    return permissions


def send_email_by_queue(queue):
    email_sending = EmailSending.objects.filter(queue=queue.upper(),
                                                active=True)
    for obj in email_sending:
        body = 'В очереди "%s" новая заявка' % getattr(Departments, obj.queue)[1]
        send_email(obj.user.email, "noreply", "Заявка на командировку", body)


class WorkFlow:
    HEAD_OF_DEPARTMENT = [Departments.DEPUTY_GOVERNOR[0],
                          Departments.PURCHASING_DEPARTMENT[0]]
    DEPUTY_GOVERNOR = [Departments.PERSONNEL_DEPARTMENT[0]]
    PERSONNEL_DEPARTMENT = [Departments.BOOKKEEPING[0]]
    PURCHASING_DEPARTMENT = [Departments.BOOKKEEPING[0]]
    BOOKKEEPING = []

    def __init__(self, business_trip, current_queue):
        self.business_trip = business_trip
        self.current_queue = current_queue

    def _all_previous_queues_completed(self, next_queue_name):
        for dep in [d for d in Departments.get_departments() if d != self.current_queue.queue]:
            if next_queue_name in getattr(self, dep):
                queue = BusinessTripQueue.objects.filter(queue=dep, business_trip=self.business_trip)
                if queue:
                    if queue[0].status == BusinessTripQueue.COMPLETED:
                        continue
                return False
        return True

    def compete_work(self):
        self.current_queue.status = BusinessTripQueue.COMPLETED
        self.current_queue.save()
        for next_queue_name in getattr(self, self.current_queue.queue):
            if not self._all_previous_queues_completed(next_queue_name):
                break
            BusinessTripQueue.objects.get_or_create(queue=next_queue_name,
                                                    business_trip=self.business_trip)
            send_email_by_queue(queue=next_queue_name)


class QueueView(View):
    def __init__(self, *args, **kwargs):
        self.business_trip = None
        self.business_trip_form = None
        self.business_trip_queue = None
        self.status = None
        self.queue = None
        self.context = {}
        super(QueueView, self).__init__(*args, **kwargs)

    def get(self, *args, **kwargs):
        pass

    def post(self, *args, **kwargs):
        pass

    def set_business_trip(self, pk):
        self.business_trip = get_object_or_404(BusinessTrip, id=pk)

    def set_business_trip_queue(self):
        self.business_trip_queue = get_object_or_404(BusinessTripQueue,
                                                     business_trip=self.business_trip,
                                                     queue=self.queue)

    def update_context_status(self):
        if not self.business_trip_queue:
            self.set_business_trip_queue()
        self.context.update({'status': self.business_trip_queue.status})

    def update_context_business_trip_form(self):
        business_trip_form = BusinessTripForm(prefix='bt', initial=model_to_dict(self.business_trip))
        business_trip_form.disable_fields()
        self.context.update({'business_trip_form': business_trip_form})

    def set_initial_data(self, pk):
        self.set_business_trip(pk)
        self.set_business_trip_queue()
        self.update_context_status()
        self.update_context_business_trip_form()


class HeadOfDepartmentView(QueueView):
    form_class = HeadOfDepartmentForm
    template_name = 'queue.html'

    def get(self, request, pk, *args, **kwargs):
        self.queue = Departments.HEAD_OF_DEPARTMENT[0]
        self.set_initial_data(pk)
        form = self.form_class(initial=model_to_dict(self.business_trip))
        for field in form.fields:
            if self.business_trip_queue.status != BusinessTripQueue.NEW:
                form.fields[field].widget.attrs['disabled'] = True
                form.fields[field].label = ''
        self.context.update({'object_id': pk,
                             'form': form,
                             'queue': self.queue.lower(),
                             'is_authenticated': request.user.is_authenticated})
        return render(request, self.template_name, self.context)

    def post(self, request, pk):
        business_trip = get_object_or_404(BusinessTrip, id=pk)
        business_trip_queue = get_object_or_404(BusinessTripQueue,
                                                business_trip=business_trip,
                                                queue=Departments.HEAD_OF_DEPARTMENT[0])
        form = self.form_class(request.POST)
        if form.is_valid():
            action = request.POST.get('action', None)
            if action == 'complete':
                business_trip.deputy_governor = form.cleaned_data['deputy_governor']
                business_trip.save()
                wf = WorkFlow(business_trip, business_trip_queue)
                wf.compete_work()
                messages.add_message(request, messages.INFO, 'Заявка согласована')
            elif action == 'reject':
                business_trip_queue.status = BusinessTripQueue.REJECTED
                business_trip_queue.save()
            return HttpResponseRedirect('/business_trips/head_of_department/' + str(business_trip.id) + '/')


def get_order_initial_data(business_trip, field):
    """The morphological rules for the order fields are defined here."""
    if field == 'full_name':
        full_name = ' '.join([get_morphed_word(business_trip.second_name, 'accs'),
                              get_morphed_word(business_trip.first_name, 'accs'),
                              get_morphed_word(business_trip.patronymic, 'accs')])
        return full_name
    elif field == 'position':
        morphed_position = ' '.join([get_morphed_word(word, 'gent') for word in business_trip.position.split()])
        return morphed_position
    elif field == 'full_name_genitive':
        full_name_prepositional = '%s %s.%s.' % (get_morphed_word(business_trip.second_name, 'gent'),
                                                 get_morphed_word(business_trip.first_name, 'gent')[0],
                                                 get_morphed_word(business_trip.patronymic, 'gent')[0])
        return full_name_prepositional
    elif field == 'period':
        period = get_period(business_trip.start_date, business_trip.end_date)
        morphed_period = ' '.join([get_morphed_word(word, 'gent') for word in period.split()])
        return morphed_period
    return getattr(business_trip, field)


@permission_required('core.BOOKKEEPING', login_url='/login/', raise_exception=True)
def bookkeeping_view(request, pk):
    business_trip = get_object_or_404(BusinessTrip, id=pk)
    business_trip_form = BusinessTripForm(prefix='bt', initial=model_to_dict(business_trip))
    business_trip_form.disable_fields()
    business_trip_queue = get_object_or_404(BusinessTripQueue,
                                            business_trip=business_trip,
                                            queue=Departments.BOOKKEEPING[0])
    if request.method == 'POST':
        action = request.POST.get('action', None)
        if action == 'complete':
                wf = WorkFlow(business_trip, business_trip_queue)
                wf.compete_work()
                messages.add_message(request, messages.INFO, 'Заявка обработана')
    status = business_trip_queue.status
    return render(request, 'queue.html', {'object_id': pk,
                                          'form': '',
                                          'business_trip_form': business_trip_form,
                                          'queue': 'bookkeeping',
                                          'status': status,
                                          'is_authenticated': request.user.is_authenticated})


class DeputyGovernorView(QueueView):
    form_class = DeputyGovernorForm
    template_name = 'queue.html'

    def get(self, request, pk, *args, **kwargs):
        self.queue = Departments.DEPUTY_GOVERNOR[0]
        self.set_initial_data(pk)
        form = self.form_class()
        order = Order.objects.get_or_create(
            business_trip=self.business_trip,
            deputy_governor=self.business_trip.deputy_governor.full_name,
            deputy_governor_position=self.business_trip.deputy_governor.position)[0]
        for field in form.fields:
            if getattr(order, field):
                form.fields[field].initial = getattr(order, field)
            else:
                form.fields[field].initial = get_order_initial_data(self.business_trip, field)
            if self.business_trip_queue.status == BusinessTripQueue.COMPLETED:
                form.fields[field].widget.attrs['readonly'] = 'readonly'
        self.context.update({'object_id': pk,
                             'form': form,
                             'queue': self.queue.lower(),
                             'is_authenticated': request.user.is_authenticated})
        return render(request, self.template_name, self.context)

    def post(self, request, pk):
        self.set_business_trip(pk)
        self.set_business_trip_queue()
        form = self.form_class(request.POST)
        if form.is_valid():
            self.update_order(form)
            action = request.POST.get('action', None)
            if action == 'complete':
                wf = WorkFlow(self.business_trip, self.business_trip_queue)
                wf.compete_work()
                messages.add_message(request, messages.INFO, 'Заявка согласована')
                return HttpResponseRedirect('/business_trips/deputy_governor/' + str(self.business_trip.id) + '/')
            elif action == 'download':
                return HttpResponseRedirect('/download/' + str(pk) + '/order/')

    def update_order(self, form):
        order = Order.objects.get_or_create(business_trip=self.business_trip)[0]
        for field in form.fields:
            setattr(order, field, form.cleaned_data[field])
        order.save()


class PersonnelDepartmentView(QueueView):
    form_class = PersonnelDepartmentForm
    template_name = 'queue.html'

    def get(self, request, pk, *args, **kwargs):
        self.queue = Departments.PERSONNEL_DEPARTMENT[0]
        self.set_initial_data(pk)
        form = self.form_class()
        order = Order.objects.get_or_create(business_trip=self.business_trip)[0]
        for field in form.fields:
            if getattr(order, field):
                form.fields[field].initial = getattr(order, field)
            if self.business_trip_queue.status == BusinessTripQueue.COMPLETED:
                form.fields[field].widget.attrs['disabled'] = True
        self.context.update({'object_id': pk,
                             'form': form,
                             'queue': self.queue.lower(),
                             'is_authenticated': request.user.is_authenticated})
        return render(request, self.template_name, self.context)

    def post(self, request, pk):
        business_trip = get_object_or_404(BusinessTrip, id=pk)
        business_trip_queue = get_object_or_404(BusinessTripQueue,
                                                business_trip=business_trip,
                                                queue=Departments.PERSONNEL_DEPARTMENT[0])
        order = Order.objects.get_or_create(business_trip=business_trip)[0]
        form = self.form_class(request.POST, request.FILES, instance=order)
        if form.is_valid():
            action = request.POST.get('action', None)
            if action == 'complete':
                form.save()
                wf = WorkFlow(business_trip, business_trip_queue)
                wf.compete_work()
                messages.add_message(request, messages.INFO, 'Заявка согласована')
                return HttpResponseRedirect('/business_trips/personnel_department/' + str(business_trip.id) + '/')


def get_application_funding_initial_data(business_trip, field):
    active_settings = ActiveSetting.objects.first()
    if field == 'daily_allowance':
        business_trip_days = (business_trip.end_date - business_trip.start_date).days
        if business_trip.end_date == business_trip.start_date:
            business_trip_days = 1
        return active_settings.daily_allowance * business_trip_days
    elif field == 'deputy_governor':
        return business_trip.deputy_governor.full_name_document
    elif field == 'deputy_governor_position':
        return business_trip.deputy_governor.position_document
    elif field == 'hotel_cost':
        hotel_cost = active_settings.hotel_cost * business_trip.hotel_days
        return hotel_cost
    return None


class PurchasingDepartmentView(QueueView):
    form_class = PurchasingDepartmentForm
    template_name = 'queue.html'

    def get(self, request, pk, *args, **kwargs):
        self.queue = Departments.PURCHASING_DEPARTMENT[0]
        self.set_initial_data(pk)
        form = self.form_class()
        application_funding = ApplicationFunding.objects.get_or_create(business_trip=self.business_trip)[0]
        for field in form.fields:
            if getattr(application_funding, field):
                form.fields[field].initial = getattr(application_funding, field)
            elif get_application_funding_initial_data(self.business_trip, field):
                form.fields[field].initial = get_application_funding_initial_data(self.business_trip, field)
            if self.business_trip_queue.status == BusinessTripQueue.COMPLETED:
                form.fields[field].widget.attrs['readonly'] = 'readonly'
        self.context.update({'object_id': pk,
                             'form': form,
                             'queue': self.queue.lower(),
                             'is_authenticated': request.user.is_authenticated})
        return render(request, self.template_name, self.context)

    def post(self, request, pk):
        business_trip = get_object_or_404(BusinessTrip, id=pk)
        business_trip_queue = get_object_or_404(BusinessTripQueue,
                                                business_trip=business_trip,
                                                queue=Departments.PURCHASING_DEPARTMENT[0])
        active_settings = ActiveSetting.objects.first()
        application_funding = ApplicationFunding.objects.get_or_create(business_trip=business_trip)[0]
        application_funding.deputy_governor = business_trip.deputy_governor.full_name_document
        application_funding.deputy_governor_position = business_trip.deputy_governor.position_document
        application_funding.hotel_cost = active_settings.hotel_cost * int(business_trip.hotel_days)
        # application_funding.save()
        form = self.form_class(request.POST, request.FILES, instance=application_funding)
        if form.is_valid():
            action = request.POST.get('action', None)
            if action == 'complete':
                wf = WorkFlow(business_trip, business_trip_queue)
                wf.compete_work()
                messages.add_message(request, messages.INFO, 'Заявка отправлена на согласование')
            else:
                messages.add_message(request, messages.INFO, 'Информация обновлена')
            form.save()
            return HttpResponseRedirect('/business_trips/purchasing_department/' + str(business_trip.id) + '/')


def convert_month(month):
    months = {'01': 'январь',
              '02': 'февраль',
              '03': 'март',
              '04': 'апрель',
              '05': 'май',
              '06': 'июнь',
              '07': 'июль',
              '08': 'август',
              '09': 'сентябрь',
              '10': 'октябрь',
              '11': 'ноябрь',
              '12': 'декабрь'}
    return months[month]


def get_cleaned_day(day):
    if day.startswith('0'):
        return day.strip('0')
    return day


# TODO : Add decorator for date conversion
def get_period(start_date, end_date):
    start_date = start_date.strftime("%Y-%m-%d")
    end_date = end_date.strftime("%Y-%m-%d")
    start_day = get_cleaned_day(start_date.split('-')[2])
    end_day = get_cleaned_day(end_date.split('-')[2])
    if start_date == end_date:
        period = start_day \
                 + ' ' + convert_month(start_date.split('-')[1]) + ' ' \
                 + start_date.split('-')[0] \
                 + ' года'
        return period
    if start_date.split('-')[0] == end_date.split('-')[0]:
        if start_date.split('-')[1] == end_date.split('-')[1]:
            period = 'с ' + start_day \
                     + ' по ' \
                     + end_day \
                     + ' ' + convert_month(end_date.split('-')[1]) + ' ' \
                     + end_date.split('-')[0] \
                     + ' года'
            return period
        period = 'с ' + start_day \
                 + ' ' + convert_month(start_date.split('-')[1]) + ' ' \
                 + ' по ' \
                 + end_day \
                 + ' ' + convert_month(end_date.split('-')[1]) + ' ' \
                 + end_date.split('-')[0] \
                 + ' года'
        return period
    period = 'с ' + start_day \
             + ' ' + convert_month(start_date.split('-')[1]) + ' ' \
             + start_date.split('-')[0] \
             + ' года по ' \
             + end_day \
             + ' ' + convert_month(end_date.split('-')[1]) + ' ' \
             + end_date.split('-')[0] \
             + ' года'
    return period


def fill_funding_application_template(funding_application):
    data = {"BlankTarget": "", "Adresat": "", "Theme": "",
            "DocContent": "", "AuthorPost": "", "Author": ""}
    hotel_days_total = int(funding_application.business_trip.hotel_days) * 200
    data['BlankTarget'] = "Заявка"
    data['Adresat'] = funding_application.deputy_governor_position + '<br/>' + funding_application.deputy_governor
    data['Theme'] = "Заявка на финансирование командировки"
    data['DocContent'] = "Для командировки в {0}".format(funding_application.business_trip.location)
    period = get_period(funding_application.business_trip.start_date, funding_application.business_trip.end_date)
    morphed_period = ' '.join([get_morphed_word(word, 'gent') for word in period.split()])
    data['DocContent'] += " {0} ".format(morphed_period)
    data['DocContent'] += "прошу выдать денежные средства" \
                          " в размере:\n 1. Транспортные расходы - {0} руб.\n" \
                          "2. Проживание в гостинице - {1} руб.\n" \
                          "3. Суточные - {2} суток - {3} руб.\n".format(funding_application.fare,
                                                                        funding_application.hotel_cost,
                                                                        funding_application.business_trip.hotel_days,
                                                                        hotel_days_total)
    data['Author'] = funding_application.business_trip.full_name_short()
    data['AuthorPost'] = funding_application.business_trip.position
    return data


def fill_order_template(order):
    data = dict(BlankTarget="", Adresat="", Theme="", DocContent="", AuthorPost="", Author="")
    data['BlankTarget'] = "Распоряжение"
    data['Theme'] = "О командировании %s" % order.full_name_genitive
    data['DocContent'] = "Командировать {0}, {1},".format(order.full_name, order.position)
    morphed_period = ' '.join([get_morphed_word(word, 'gent') for word in order.period.split()])
    data['DocContent'] += " {0} ".format(morphed_period)
    data['DocContent'] += "в {0} в связи ".format(order.location)
    if order.purpose.lower().startswith('с'):
        data['DocContent'] += "со {0}".format(order.purpose)
    else:
        data['DocContent'] += "с {0}".format(order.purpose)
    data['Author'] = order.deputy_governor
    data['AuthorPost'] = order.deputy_governor_position
    return data


def download_link(request, pk, document_type):
    business_trip = get_object_or_404(BusinessTrip, id=pk)
    if document_type.lower() not in list(map(lambda x: x[0].lower(), Document.DOCUMENT_CHOICES)):
        raise HttpResponse(status=404)
    elif document_type.lower() == Document.ORDER.lower():
        obj = get_object_or_404(Order, business_trip=business_trip)
        data = fill_order_template(obj)
    else:
        obj = get_object_or_404(ApplicationFunding, business_trip=business_trip)
        data = fill_funding_application_template(obj)
    stream = get_file_stream(data)
    response = HttpResponse(stream)
    response['Content-Type'] = 'application/pdf'
    response['Content-disposition'] = 'attachment ; filename = {}'.format('test.pdf')
    return response


class BusinessTripDetailedView(FormMixin, DetailView):

    model = BusinessTrip
    template_name = 'business_trip_detail.html'
    form_class = BusinessTripForm

    def get_context_data(self, **kwargs):
        context = super(BusinessTripDetailedView, self).get_context_data(**kwargs)
        if not self.request.user.is_authenticated:
            return redirect('/login/')
        context['form'] = BusinessTripForm(initial=model_to_dict(context['object']))
        context['is_authenticated'] = self.request.user.is_authenticated
        # if context['object'].funding_application_status:
        #     context['funding_application_status'] = 'Документ сформирован'
        # else:
        #     context['funding_application_status'] = 'Документ не сформирован'
        # if context['object'].order_status:
        #     context['order_status'] = 'Документ сформирован'
        # else:
        #     context['order_status'] = 'Документ не сформирован'
        for field in context['form'].fields:
            context['form'].fields[field].widget.attrs['disabled'] = True
        return context
