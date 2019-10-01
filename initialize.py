import os


def add_initial_deputy_governors():
    DeputyGovernor.objects.get_or_create(full_name='Голицын Евгений Викторович',
                                         position='Заместитель Губернатора – руководителя Аппарата Губернатора'
                                                  ' и Правительства Челябинской области',
                                         full_name_document='Е.В. Голицыну',
                                         position_document='Заместителю Губернатора – руководителю Аппарата'
                                                           ' Губернатора и Правительства Челябинской области')
    DeputyGovernor.objects.get_or_create(full_name='Мамин Виктор Викторович',
                                         position='Первый заместитель Губернатора Челябинской области',
                                         full_name_document='В.В. Мамину',
                                         position_document='Первому заместителю Губернатора Челябинской области')


def add_initial_settings():
    ActiveSetting.objects.get_or_create(hotel_cost=400, daily_allowance=200)


def clear_database():
    BusinessTrip.objects.all().delete()


if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'business_trip.settings')
    import django

    django.setup()

    from core.models import BusinessTrip, ActiveSetting, DeputyGovernor
    clear_database()
    add_initial_deputy_governors()
