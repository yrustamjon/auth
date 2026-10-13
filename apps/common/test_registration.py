from django.test import TestCase, Client
from apps.common.models import AdminUser, Organization, Device, Users, Roles
from apps.device.browser_enrollment import submit_identity

class RegistrationTests(TestCase):
    password = 'Strong!New-password729'

    def register(self, kind='company', **extra):
        return self.client.post('/api/register/', dict(kind=kind, username='new-owner', password=self.password,
            fio='New Owner', company_name='Example Company', **extra), content_type='application/json')

    def scan(self):
        data=self.client.post('/api/devices/browser-enrollment/session/', {}, content_type='application/json').json()
        submit_identity(session_id=data['session_id'],scan_token=data['scan_token'],platform='linux',
            device_id='machine-729',identifiers={'machine_id':'machine-729','product_uuid':'uuid-729'},hostname='My PC')
        return data['session_id']

    def test_personal_requires_owned_completed_pc_session_and_creates_isolated_workspace(self):
        self.assertEqual(self.register('personal').status_code,400)
        self.assertFalse(AdminUser.objects.filter(username='new-owner').exists())
        scan=self.scan()
        response=self.register('personal', enrollment_session_id=scan)
        self.assertEqual(response.status_code,201,response.content)
        owner=AdminUser.objects.get(username='new-owner')
        org=owner.organizations.get()
        self.assertEqual(org.kind,'personal')
        self.assertEqual(org.approval_status,'approved')
        self.assertTrue(org.is_active)
        self.assertFalse(owner.is_staff or owner.is_superadmin)
        self.assertEqual(Device.objects.get(organization=org).pc_id,'machine-729')
        self.assertEqual(Users.objects.get(organization=org).username,owner.username)
        self.assertEqual(self.client.session['current_org_id'],org.id)

    def test_company_waits_for_system_approval(self):
        response=self.register()
        self.assertEqual(response.status_code,201,response.content)
        owner=AdminUser.objects.get(username='new-owner');org=owner.organizations.get()
        self.assertFalse(org.is_active)
        self.assertEqual(org.approval_status,'pending')
        self.assertEqual(self.client.get('/api/users/').status_code,403)
        self.assertEqual(self.client.get('/api/registration/status/').json()['status'],'pending')
        self.assertEqual(self.client.post(f'/api/registration/{org.id}/decision/',{'action':'approve'},content_type='application/json').status_code,403)
        system=AdminUser.objects.create_user('system-reviewer',self.password,organization=org,is_superadmin=True)
        self.client.force_login(system)
        self.assertEqual(self.client.post(f'/api/registration/{org.id}/decision/',{'action':'approve'},content_type='application/json').status_code,200)
        org.refresh_from_db();self.assertTrue(org.is_active)
        self.assertEqual(org.approval_status,'approved')
        self.client.force_login(owner)
        session=self.client.session;session['current_org_id']=org.id;session.save()
        self.assertEqual(self.client.get('/api/users/').status_code,200)

    def test_duplicate_or_weak_password_leaves_no_workspace(self):
        response=self.client.post('/api/register/',{'kind':'company','username':'weak','password':'123','company_name':'Weak'},content_type='application/json')
        self.assertEqual(response.status_code,400)
        self.assertFalse(Organization.objects.filter(name='Weak').exists())
        self.assertEqual(self.register().status_code,201)
        self.client.logout();count=Organization.objects.count()
        self.assertEqual(self.register().status_code,400)
        self.assertEqual(Organization.objects.count(),count)

    def test_personal_cannot_access_global_admin_or_other_tenant_records(self):
        scan=self.scan();self.assertEqual(self.register('personal',enrollment_session_id=scan).status_code,201)
        other=Organization.objects.create(name='Other',slug='other-private')
        role=Roles.objects.create(organization=other,name='Other Role')
        user=Users.objects.create(organization=other,role=role,username='other',fio='Other',lavozim='Other')
        for path in ['/api/system/admins/','/api/organizations/']:
            self.assertEqual(self.client.get(path).status_code,403,path)
        self.assertEqual(self.client.delete(f'/api/users/{user.id}/').status_code,404)
        self.assertEqual(self.client.patch(f'/api/roles/{role.id}/',{'name':'Stolen'},content_type='application/json').status_code,404)
        self.assertTrue(Users.objects.filter(pk=user.pk).exists())

    def test_csrf_required_and_foreign_pc_cannot_be_consumed(self):
        csrf=Client(enforce_csrf_checks=True)
        self.assertEqual(csrf.post('/api/register/',{},content_type='application/json').status_code,403)
        scan=self.scan();self.client.logout()
        self.assertEqual(self.register('personal',enrollment_session_id=scan).status_code,404)

    def test_pending_company_cannot_bypass_review_by_logging_in(self):
        self.assertEqual(self.register().status_code,201)
        self.client.logout()
        result=self.client.post('/api/admin/login',{'username':'new-owner','password':self.password},content_type='application/json')
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.json()['redirect'],'/registration/status')
        self.assertEqual(self.client.get('/api/devices').status_code,403)

    def test_rejected_company_stays_inactive_and_decision_cannot_repeat(self):
        self.assertEqual(self.register().status_code,201)
        owner=AdminUser.objects.get(username='new-owner');org=owner.organizations.get()
        system=AdminUser.objects.create_user('reviewer',self.password,organization=org,is_superadmin=True)
        self.client.force_login(system)
        path=f'/api/registration/{org.id}/decision/'
        self.assertEqual(self.client.post(path,{'action':'reject','note':'Contact details needed'},content_type='application/json').status_code,200)
        self.assertEqual(self.client.post(path,{'action':'approve'},content_type='application/json').status_code,409)
        org.refresh_from_db();self.assertFalse(org.is_active);self.assertEqual(org.approval_status,'rejected')
        self.assertEqual(org.reviewed_by,system)

    def test_company_pc_requires_member_admin_and_company_review(self):
        self.assertEqual(self.register().status_code,201)
        owner=AdminUser.objects.get(username='new-owner');org=owner.organizations.get()
        from apps.device.browser_enrollment import permitted_admin, EnrollmentError
        with self.assertRaises(EnrollmentError):permitted_admin(owner,org)
        org.approval_status='approved';org.is_active=True;org.save()
        permitted_admin(owner,org)
        other=Organization.objects.create(name='Another',slug='company-another')
        outsider=AdminUser.objects.create_user('outsider',self.password,organization=other)
        with self.assertRaises(EnrollmentError):permitted_admin(outsider,org)
