from django.db import models
from django.contrib.auth.models import User


class Departments:
    HEAD_OF_DEPARTMENT = ('HEAD_OF_DEPARTMENT', 'Начальник управления')
    DEPUTY_GOVERNOR = ('DEPUTY_GOVERNOR', 'Заместитель губернатора')
    PERSONNEL_DEPARTMENT = ('PERSONNEL_DEPARTMENT', 'Отдел кадров')
    PURCHASING_DEPARTMENT = ('PURCHASING_DEPARTMENT', 'Отдел закупок')
    BOOKKEEPING = ('BOOKKEEPING', 'Бухгалтерия')

    @staticmethod
    def get_departments():
        return [k for k in Departments.__dict__.keys() if not k.startswith('_') and k != 'get_departments']


class DeputyGovernor(models.Model):
    full_name = models.CharField(max_length=255, verbose_name='ФИО')
    position = models.CharField(max_length=255, verbose_name='Должность')
    full_name_document = models.CharField(max_length=255, verbose_name='ФИО (Р.П.)')
    position_document = models.CharField(max_length=255, verbose_name='Должность (Р.П.)')
    date_added = models.DateField(auto_now_add=True)
    date_modified = models.DateField(auto_now=True)

    def __str__(self):
        return self.full_name


class BusinessTrip(models.Model):
    WHO_PAYS_THE_TRIP_CHOICES = [
        ('GOVERNMENT', 'Правительство Челябинской области'),
        ('HOST_PARTY', 'Принимающая сторона'),
    ]
    RECEIVING_FUNDS_CHOICES = [
        ('SALARY_CARD', 'Перечислить на мою зарплатную карту'),
        ('CASH', 'Наличные'),
    ]
    second_name = models.CharField(max_length=100, verbose_name='Фамилия')
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    patronymic = models.CharField(max_length=100, verbose_name='Отчество')
    position = models.CharField(max_length=255, verbose_name='Должность')
    location = models.CharField(max_length=255, verbose_name='Место командировки')
    purpose = models.CharField(max_length=255, verbose_name='Цель командировки (в связи с ...)')
    start_date = models.DateField(verbose_name='Дата начала командировки с учетом времени нахождения в пути')
    end_date = models.DateField(verbose_name='Дата окончания командировки с учетом времени нахождения в пути')
    departure_date_limit = models.CharField(max_length=255,
                                            verbose_name='Вылет в место командировки не позднее (время)')
    arrival_date_limit = models.CharField(max_length=255, verbose_name='Вылет обратно не позднее (время)')
    who_pays_the_trip = models.CharField(max_length=255, verbose_name='Кто оплачивает командировку',
                                         choices=WHO_PAYS_THE_TRIP_CHOICES)
    receiving_funds = models.CharField(max_length=255, verbose_name='Способ получения денежных средств',
                                       choices=RECEIVING_FUNDS_CHOICES)
    transport_type = models.CharField(max_length=255, verbose_name='Вид транспорта')
    hotel_days = models.CharField(max_length=255, verbose_name='Количество дней в гостинице')
    deputy_governor = models.ForeignKey(DeputyGovernor, null=True, blank=True, on_delete=models.DO_NOTHING)
    date_added = models.DateField(auto_now_add=True, verbose_name='Дата создания заявки')
    date_modified = models.DateField(auto_now=True, verbose_name='Дата изменения заявки')

    class Meta:
        permissions = [
            (Departments.HEAD_OF_DEPARTMENT[0], "Заявки начальника управления"),
            (Departments.DEPUTY_GOVERNOR[0], "Заявки заместителя губернатора"),
            (Departments.PERSONNEL_DEPARTMENT[0], "Заявки в отделе кадров"),
            (Departments.PURCHASING_DEPARTMENT[0], "Заявки в отделе закупок"),
            (Departments.BOOKKEEPING[0], "Заявки в бухгалтерии"),
        ]
        ordering = ['-id']

    def __str__(self):
        return "%s %s %s" % (self.second_name, self.first_name, self.patronymic)

    def full_name_short(self):
        return "%s.%s. %s" % (self.first_name[0], self.patronymic[0], self.second_name)


class PassportData(models.Model):
    business_trip = models.ForeignKey(BusinessTrip, on_delete=models.CASCADE)
    series = models.CharField(max_length=255, verbose_name='Серия')
    number = models.CharField(max_length=255, verbose_name='Номер')
    issued = models.CharField(max_length=255, verbose_name='Кем выдан')
    date = models.CharField(max_length=255, verbose_name='Дата выдачи')
    code = models.CharField(max_length=255, verbose_name='Код подразделения')
    date_added = models.DateField(auto_now_add=True)
    date_modified = models.DateField(auto_now=True)


class Order(models.Model):
    business_trip = models.ForeignKey(BusinessTrip, on_delete=models.CASCADE)
    full_name_genitive = models.CharField(max_length=255, verbose_name='ФИО (О командировании ...)')
    full_name = models.CharField(max_length=255, verbose_name='ФИО (Командировать ...)')
    position = models.CharField(max_length=255, verbose_name='Должность')
    period = models.CharField(max_length=255, verbose_name='Период командировки')
    location = models.CharField(max_length=255, verbose_name='Место командировки')
    purpose = models.CharField(max_length=255, verbose_name='Цель командировки (в связи с ...)')
    deputy_governor = models.CharField(max_length=255, null=True, verbose_name='Заместитель губернатора')
    deputy_governor_position = models.CharField(max_length=255, null=True,
                                                verbose_name='Должность заместителя губернатора')
    upload = models.FileField(upload_to='scans', null=True, verbose_name='')
    date_added = models.DateField(auto_now_add=True)
    date_modified = models.DateField(auto_now=True)


class ApplicationFunding(models.Model):
    business_trip = models.ForeignKey(BusinessTrip, on_delete=models.CASCADE)
    deputy_governor = models.CharField(max_length=255, blank=True, null=True, verbose_name='Заместитель губернатора')
    deputy_governor_position = models.CharField(max_length=255, blank=True, null=True,
                                                verbose_name='Должность заместителя губернатора')
    fare = models.CharField(max_length=255, null=True, verbose_name='Транспортные расходы')
    hotel_cost = models.CharField(max_length=255, null=True, verbose_name='Сумма проживания в гостинице')
    daily_allowance = models.CharField(max_length=255, null=True, verbose_name='Суточные')
    date_added = models.DateField(auto_now_add=True)
    date_modified = models.DateField(auto_now=True)


class SingletonModel(models.Model):

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class ActiveSetting(SingletonModel):
    hotel_cost = models.IntegerField(verbose_name='Лимит на гостиницу')
    # daily_allowance = models.IntegerField(verbose_name='Суточные')


class Document:
    FUNDING_APPLICATION = 'FUNDING_APPLICATION'
    ORDER = 'ORDER'
    DOCUMENT_CHOICES = [
        (FUNDING_APPLICATION, 'Заявка на финансирование'),
        (ORDER, 'Распоряжение'),
    ]


class EmailSending(models.Model):
    QUEUE = [(Departments().__getattribute__(d)[0], Departments().__getattribute__(d)[1])
             for d in Departments.get_departments()]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    queue = models.CharField(max_length=255, verbose_name='Очередь', choices=QUEUE)
    active = models.BooleanField(default=True)
    date_added = models.DateField(auto_now_add=True)
    date_modified = models.DateField(auto_now=True)

    def __str__(self):
        return '%s %s' % (self.user, self.queue)


class BusinessTripQueue(models.Model):
    NEW = 'NEW'
    COMPLETED = 'COMPLETED'
    REJECTED = 'REJECTED'
    STATUS_CHOICES = [
        (NEW, 'Новые'),
        (COMPLETED, 'Выполненные'),
        (REJECTED, 'Отклоненные'),
    ]
    QUEUE = [(Departments().__getattribute__(d)[0], Departments().__getattribute__(d)[1])
             for d in Departments.get_departments()]
    queue = models.CharField(max_length=255, verbose_name='Очередь', choices=QUEUE)
    business_trip = models.ForeignKey(BusinessTrip, on_delete=models.CASCADE)
    status = models.CharField(max_length=255, verbose_name='Статус', default=NEW)
    date_added = models.DateField(auto_now_add=True)
    date_modified = models.DateField(auto_now=True)
