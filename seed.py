"""Demo data so the app works the moment you run it. Run: python manage.py shell < seed.py"""
from accounts.models import User
from operations.models import Branch
from core.models import RateCard, RestrictedItem

if not Branch.objects.exists():
    ktm = Branch.objects.create(name='Bharosa — Kathmandu (Head Office)', location='Kathmandu',
                                address='Dhumbarahi Chowk, Kathmandu', phone='+977 01-4XXXXXX',
                                email='ktm@bharosacourier.com')
    pkr = Branch.objects.create(name='Bharosa — Pokhara', location='Pokhara',
                                address='Lakeside, Pokhara', phone='+977 061-5XXXXX')

    User.objects.create_superuser('owner', 'owner@bharosacourier.com', 'bharosa123',
                                  role=User.Roles.SUPERADMIN, first_name='Jungey')
    User.objects.create_user('manager.ktm', 'mgr@bharosacourier.com', 'bharosa123',
                             role=User.Roles.BRANCH_ADMIN, branch=ktm, first_name='KTM Manager')
    User.objects.create_user('staff.ktm', 'staff@bharosacourier.com', 'bharosa123',
                             role=User.Roles.STAFF, branch=ktm, first_name='KTM Staff')

    rates = [('United States', '🇺🇸', 1950, '5–7 days', 'FedEx · DHL Express'),
             ('United Kingdom', '🇬🇧', 1700, '4–6 days', 'DHL Express · DPD'),
             ('Australia', '🇦🇺', 1800, '5–7 days', 'DHL Express · SkyNet'),
             ('UAE', '🇦🇪', 1250, '3–5 days', 'Aramex · SkyNet'),
             ('Japan', '🇯🇵', 1850, '4–6 days', 'FedEx · DHL Express'),
             ('Germany', '🇩🇪', 1750, '5–8 days', 'DPD · DHL Express'),
             ('Canada', '🇨🇦', 2000, '6–8 days', 'FedEx · DHL Express'),
             ('South Korea', '🇰🇷', 1700, '4–6 days', 'DHL Express · SkyNet')]
    for c, f, r, d, ca in rates:
        RateCard.objects.create(country=c, flag=f, rate_per_kg=r, delivery_days=d, carriers=ca)

    RestrictedItem.objects.create(country='United States', item='Liquids over 1L', note='Air freight restriction')
    RestrictedItem.objects.create(country='Australia', item='Plant seeds & soil', note='Strict biosecurity laws')
    RestrictedItem.objects.create(country='UAE', item='Religious idols & artifacts', note='Check customs guidance')
    print('Seeded: 2 branches, 3 users (owner / manager.ktm / staff.ktm — password bharosa123), 8 rates.')
else:
    print('Already seeded.')
