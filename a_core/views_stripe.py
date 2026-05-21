import json
import logging
import stripe
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


@require_POST
def create_checkout_session(request):
    try:
        data = json.loads(request.body)
        amount_aud = float(data.get('amount', 0))
        frequency = data.get('frequency', 'one-time')

        if amount_aud < 1:
            return JsonResponse({'error': 'Minimum donation is $1'}, status=400)

        if amount_aud > 100000:
            return JsonResponse({'error': 'Maximum donation is $100,000'}, status=400)

        # Stripe amounts are in cents
        amount_cents = int(round(amount_aud * 100))

        base_url = request.build_absolute_uri('/').rstrip('/')

        if frequency == 'monthly':
            # Recurring donation via subscription
            price = stripe.Price.create(
                currency='aud',
                unit_amount=amount_cents,
                recurring={'interval': 'month'},
                product_data={'name': 'Monthly Donation to CAWC NSW'},
            )
            session = stripe.checkout.Session.create(
                mode='subscription',
                line_items=[{'price': price.id, 'quantity': 1}],
                success_url=base_url + '/donate/success/?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=base_url + '/donate/cancel/',
            )
        else:
            session = stripe.checkout.Session.create(
                mode='payment',
                line_items=[{
                    'price_data': {
                        'currency': 'aud',
                        'unit_amount': amount_cents,
                        'product_data': {'name': 'Donation to CAWC NSW'},
                    },
                    'quantity': 1,
                }],
                success_url=base_url + '/donate/success/?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=base_url + '/donate/cancel/',
            )

        return JsonResponse({'url': session.url})

    except stripe.StripeError as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.SignatureVerificationError) as e:
        logger.warning('Stripe webhook rejected: %s', e)
        return JsonResponse({'error': 'Invalid payload or signature'}, status=400)

    event_type = event['type']
    data = event['data']['object']

    if event_type == 'checkout.session.completed':
        amount = data.get('amount_total', 0) / 100
        mode = data.get('mode')
        email = data.get('customer_details', {}).get('email', 'unknown')
        logger.info('Donation received — mode=%s amount=AUD%.2f email=%s', mode, amount, email)

    elif event_type == 'invoice.paid':
        amount = data.get('amount_paid', 0) / 100
        email = data.get('customer_email', 'unknown')
        logger.info('Recurring donation paid — amount=AUD%.2f email=%s', amount, email)

    elif event_type == 'invoice.payment_failed':
        email = data.get('customer_email', 'unknown')
        logger.warning('Recurring donation payment failed — email=%s', email)

    elif event_type == 'customer.subscription.deleted':
        customer_id = data.get('customer', 'unknown')
        logger.info('Subscription cancelled — customer=%s', customer_id)

    else:
        logger.debug('Unhandled Stripe event: %s', event_type)

    return JsonResponse({'status': 'ok'})


def donation_success(request):
    return render(request, 'donate/success.html')


def donation_cancel(request):
    return render(request, 'donate/cancel.html')
