from datetime import timedelta

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.utils import timezone

from .models import Newsletter, Subscriber, _default_token_expiry
from .wagtail_hooks import _audience_queryset


# ── Subscriber signup ────────────────────────────────────────────────────────

class SubscriberSignupTests(TestCase):

    def test_signup_creates_pending_subscriber(self):
        self.client.post('/newsletter/subscribe/', {
            'email': 'test@example.com',
            'language_preference': 'any',
            'website': '',
        })
        sub = Subscriber.objects.get(email='test@example.com')
        self.assertEqual(sub.status, Subscriber.STATUS_PENDING)
        self.assertIsNone(sub.confirmed_at)

    def test_signup_sends_confirmation_email(self):
        self.client.post('/newsletter/subscribe/', {
            'email': 'test@example.com',
            'language_preference': 'any',
            'website': '',
        })
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Confirm', mail.outbox[0].subject)

    def test_honeypot_blocks_bots(self):
        self.client.post('/newsletter/subscribe/', {
            'email': 'bot@example.com',
            'language_preference': 'any',
            'website': 'http://spam.com',
        })
        self.assertFalse(Subscriber.objects.filter(email='bot@example.com').exists())

    def test_pending_subscriber_gets_fresh_token_on_resubmit(self):
        sub = Subscriber.objects.create(email='test@example.com')
        old_token = sub.confirm_token
        self.client.post('/newsletter/subscribe/', {
            'email': 'test@example.com',
            'language_preference': 'any',
            'website': '',
        })
        sub.refresh_from_db()
        self.assertNotEqual(sub.confirm_token, old_token)

    def test_confirmed_subscriber_redirects_to_already_subscribed(self):
        Subscriber.objects.create(
            email='test@example.com',
            status=Subscriber.STATUS_CONFIRMED,
            confirmed_at=timezone.now(),
        )
        response = self.client.post('/newsletter/subscribe/', {
            'email': 'test@example.com',
            'language_preference': 'any',
            'website': '',
        })
        self.assertRedirects(response, '/newsletter/already-subscribed/')


# ── Confirmation ─────────────────────────────────────────────────────────────

class ConfirmationTests(TestCase):

    def test_valid_token_confirms_subscriber(self):
        sub = Subscriber.objects.create(email='test@example.com')
        response = self.client.get(f'/newsletter/confirm/{sub.confirm_token}/')
        self.assertRedirects(response, '/newsletter/confirmed/')
        sub.refresh_from_db()
        self.assertEqual(sub.status, Subscriber.STATUS_CONFIRMED)
        self.assertIsNotNone(sub.confirmed_at)

    def test_valid_token_sends_welcome_email(self):
        sub = Subscriber.objects.create(email='test@example.com')
        self.client.get(f'/newsletter/confirm/{sub.confirm_token}/')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Welcome', mail.outbox[0].subject)
        self.assertIn('/newsletter/unsubscribe/', mail.outbox[0].body)

    def test_expired_token_returns_410(self):
        sub = Subscriber.objects.create(
            email='test@example.com',
            token_expires_at=timezone.now() - timedelta(hours=1),
        )
        response = self.client.get(f'/newsletter/confirm/{sub.confirm_token}/')
        self.assertEqual(response.status_code, 410)
        sub.refresh_from_db()
        self.assertEqual(sub.status, Subscriber.STATUS_PENDING)

    def test_invalid_token_returns_404(self):
        response = self.client.get('/newsletter/confirm/nonexistenttoken123/')
        self.assertEqual(response.status_code, 404)

    def test_already_confirmed_redirects(self):
        sub = Subscriber.objects.create(
            email='test@example.com',
            status=Subscriber.STATUS_CONFIRMED,
            confirmed_at=timezone.now(),
        )
        response = self.client.get(f'/newsletter/confirm/{sub.confirm_token}/')
        self.assertRedirects(response, '/newsletter/confirmed/')


# ── Unsubscribe ──────────────────────────────────────────────────────────────

class UnsubscribeTests(TestCase):

    def test_unsubscribe_changes_status(self):
        sub = Subscriber.objects.create(
            email='test@example.com',
            status=Subscriber.STATUS_CONFIRMED,
            confirmed_at=timezone.now(),
        )
        response = self.client.get(f'/newsletter/unsubscribe/{sub.unsubscribe_token}/')
        self.assertEqual(response.status_code, 200)
        sub.refresh_from_db()
        self.assertEqual(sub.status, Subscriber.STATUS_UNSUBSCRIBED)
        self.assertIsNotNone(sub.unsubscribed_at)

    def test_unsubscribe_is_idempotent(self):
        sub = Subscriber.objects.create(
            email='test@example.com',
            status=Subscriber.STATUS_UNSUBSCRIBED,
            confirmed_at=timezone.now(),
            unsubscribed_at=timezone.now(),
        )
        self.client.get(f'/newsletter/unsubscribe/{sub.unsubscribe_token}/')
        sub.refresh_from_db()
        self.assertEqual(sub.status, Subscriber.STATUS_UNSUBSCRIBED)


# ── Audience filtering ───────────────────────────────────────────────────────

class AudienceFilterTests(TestCase):

    def setUp(self):
        now = timezone.now()
        Subscriber.objects.create(email='en@example.com', status=Subscriber.STATUS_CONFIRMED, language_preference='en', confirmed_at=now)
        Subscriber.objects.create(email='km@example.com', status=Subscriber.STATUS_CONFIRMED, language_preference='km', confirmed_at=now)
        Subscriber.objects.create(email='any@example.com', status=Subscriber.STATUS_CONFIRMED, language_preference='any', confirmed_at=now)
        Subscriber.objects.create(email='pending@example.com', status=Subscriber.STATUS_PENDING)

    def _newsletter(self, audience):
        return Newsletter(subject='Test', body='Body', audience=audience)

    def test_all_audience_excludes_pending(self):
        qs = _audience_queryset(self._newsletter(Newsletter.AUDIENCE_ALL))
        self.assertEqual(qs.count(), 3)
        self.assertNotIn('pending@example.com', qs.values_list('email', flat=True))

    def test_english_audience_includes_any_preference(self):
        qs = _audience_queryset(self._newsletter(Newsletter.AUDIENCE_ENGLISH))
        emails = list(qs.values_list('email', flat=True))
        self.assertIn('en@example.com', emails)
        self.assertIn('any@example.com', emails)
        self.assertNotIn('km@example.com', emails)

    def test_khmer_audience_includes_any_preference(self):
        qs = _audience_queryset(self._newsletter(Newsletter.AUDIENCE_KHMER))
        emails = list(qs.values_list('email', flat=True))
        self.assertIn('km@example.com', emails)
        self.assertIn('any@example.com', emails)
        self.assertNotIn('en@example.com', emails)


# ── Newsletter send safety ───────────────────────────────────────────────────

class NewsletterSendTests(TestCase):

    def setUp(self):
        self.staff = User.objects.create_user('staff', 'staff@example.com', 'password', is_staff=True, is_superuser=True)
        self.client.login(username='staff', password='password')

    def _confirmed_subscriber(self, email='sub@example.com'):
        return Subscriber.objects.create(
            email=email,
            status=Subscriber.STATUS_CONFIRMED,
            language_preference='any',
            confirmed_at=timezone.now(),
        )

    def _newsletter(self):
        return Newsletter.objects.create(subject='Test', body='Hello world')

    def test_sent_newsletter_cannot_resend(self):
        sub = self._confirmed_subscriber()
        nl = self._newsletter()
        nl.status = Newsletter.STATUS_SENT
        nl.sent_at = timezone.now()
        nl.recipient_count = 1
        nl.save()
        self.client.post(f'/admin/newsletter/{nl.pk}/send-confirm/')
        nl.refresh_from_db()
        self.assertEqual(nl.recipient_count, 1)
        self.assertEqual(nl.status, Newsletter.STATUS_SENT)

    def test_zero_recipient_newsletter_not_sent(self):
        nl = self._newsletter()
        nl.audience = Newsletter.AUDIENCE_ENGLISH
        nl.save()
        # No English subscribers exist
        self.client.post(f'/admin/newsletter/{nl.pk}/send-confirm/')
        nl.refresh_from_db()
        self.assertEqual(nl.status, Newsletter.STATUS_DRAFT)

    def test_newsletter_marks_sent_after_successful_send(self):
        self._confirmed_subscriber()
        nl = self._newsletter()
        self.client.post(f'/admin/newsletter/{nl.pk}/send-confirm/')
        nl.refresh_from_db()
        self.assertEqual(nl.status, Newsletter.STATUS_SENT)
        self.assertEqual(nl.recipient_count, 1)
        self.assertIsNotNone(nl.sent_at)


# ── Model helpers ─────────────────────────────────────────────────────────────

class SubscriberModelTests(TestCase):

    def test_save_auto_sets_confirmed_at(self):
        sub = Subscriber.objects.create(email='test@example.com')
        self.assertIsNone(sub.confirmed_at)
        sub.status = Subscriber.STATUS_CONFIRMED
        sub.save()
        sub.refresh_from_db()
        self.assertIsNotNone(sub.confirmed_at)

    def test_is_token_valid_returns_false_when_expired(self):
        sub = Subscriber(token_expires_at=timezone.now() - timedelta(hours=1))
        self.assertFalse(sub.is_token_valid())

    def test_is_token_valid_returns_true_when_fresh(self):
        sub = Subscriber(token_expires_at=timezone.now() + timedelta(hours=47))
        self.assertTrue(sub.is_token_valid())
