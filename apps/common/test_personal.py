from django.test import TestCase
from .models import AdminUser, Organization, Users, Device

class PersonalUiTests(TestCase):
    def setUp(self):
        self.org=Organization.objects.create(name='Personal',slug='personal-ui',kind='personal')
        self.owner=AdminUser.objects.create_user('personal-owner','Test-password829',organization=self.org,is_staff=False)
        self.org.registration_owner=self.owner;self.org.save()
        self.user=Users.objects.create(organization=self.org,fio='Owner',username=self.owner.username,lavozim='Egasi')
        Device.objects.create(organization=self.org,pc_id='my-pc',license='UNKNOWN',location='Home',enrollment_status='browser_approved',is_active=False)
        self.client.force_login(self.owner);session=self.client.session;session['current_org_id']=self.org.id;session['panel']='admin';session.save()

    def test_personal_profile_is_owner_scoped_and_login_enters_personal_ui(self):
        result=self.client.get('/api/personal/')
        self.assertEqual(result.status_code,200,result.content)
        self.assertEqual(result.json()['user']['id'],self.user.id)
        self.assertEqual(result.json()['devices'][0]['pc_id'],'my-pc')
        self.client.logout()
        result=self.client.post('/api/admin/login',{'username':self.owner.username,'password':'Test-password829'},content_type='application/json')
        self.assertEqual(result.json()['redirect'],'/personal/computer')

    def test_company_and_other_personal_owner_cannot_read_profile_or_token(self):
        other=Organization.objects.create(name='Company',slug='company-ui')
        outsider=AdminUser.objects.create_user('outside-owner','Test-password829',organization=other)
        self.client.force_login(outsider)
        session=self.client.session;session['current_org_id']=self.org.id;session.save()
        self.assertEqual(self.client.get('/api/personal/').status_code,403)
        self.assertEqual(self.client.get('/api/token/').status_code,403)
        session=self.client.session;session['current_org_id']=other.id;session.save()
        self.assertEqual(self.client.get('/api/personal/').status_code,403)
