import os


def populate():
    add_business_trip(second_name='Зюся', first_name='Сергей', patronymic='Валерьевич',
                      position='пресс-секретарь Губернатора Челябинской области Управления'
                               ' пресс-службы и информации Правительства Челябинской области',
                      location='Уйский муниципальный район и г. Магнитогорск Челябинской области',
                      purpose='информационным сопровождением временно исполняющего обязанности'
                              ' Губернатора Челябинской области',
                      start_date='2019-09-20', end_date='2019-09-22',
                      departure_date_limit='10-00',
                      arrival_date_limit='14-00',
                      who_pays_the_trip=BusinessTrip.WHO_PAYS_THE_TRIP_CHOICES[0][0],
                      receiving_funds=BusinessTrip.RECEIVING_FUNDS_CHOICES[0][0],
                      transport_type='Самолёт',
                      hotel_days=2,
                      deputy_governor=DeputyGovernor.objects.first())


def add_business_trip(second_name, first_name, patronymic, position, location, purpose,
                      start_date, end_date, departure_date_limit, arrival_date_limit,
                      who_pays_the_trip, receiving_funds, transport_type, hotel_days,
                      deputy_governor):
    business_trip = BusinessTrip.objects.create(second_name=second_name,
                                                first_name=first_name,
                                                patronymic=patronymic,
                                                position=position,
                                                location=location,
                                                purpose=purpose,
                                                start_date=start_date,
                                                end_date=end_date,
                                                departure_date_limit=departure_date_limit,
                                                arrival_date_limit=arrival_date_limit,
                                                who_pays_the_trip=who_pays_the_trip,
                                                receiving_funds=receiving_funds,
                                                transport_type=transport_type,
                                                hotel_days=hotel_days,
                                                deputy_governor=deputy_governor)
    BusinessTripQueue.objects.create(business_trip=business_trip,
                                     queue=Departments.HEAD_OF_DEPARTMENT[0])


if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'business_trip.settings')
    import django

    django.setup()

    from core.models import BusinessTrip, DeputyGovernor, BusinessTripQueue, Departments
    populate()
