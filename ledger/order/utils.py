from oscar.apps.order.utils import OrderCreator as CoreOrderCreator
from django.conf import settings
from oscar.core.loading import get_model

Line = get_model('order', 'Line')

class OrderCreator(CoreOrderCreator):

    def place_order(self, basket, total,  # noqa (too complex (12))
                    shipping_method, shipping_charge, user=None,
                    shipping_address=None, billing_address=None,
                    order_number=None, status=None, **kwargs):
        """
        Placing an order involves creating all the relevant models based on the
        basket and session data.
        """
        if basket.is_empty:
            raise ValueError(_("Empty baskets cannot be submitted"))
        if not order_number:
            generator = OrderNumberGenerator()
            order_number = generator.order_number(basket)
        if not status and hasattr(settings, 'OSCAR_INITIAL_ORDER_STATUS'):
            status = getattr(settings, 'OSCAR_INITIAL_ORDER_STATUS')
        try:
            Order._default_manager.get(number=order_number)
        except Order.DoesNotExist:
            pass
        else:
            raise ValueError(_("There is already an order with number %s")
                             % order_number)

        # Ok - everything seems to be in order, let's place the order
        order = self.create_order_model(
            user, basket, shipping_address, shipping_method, shipping_charge,
            billing_address, total, order_number, status, **kwargs)
        for line in basket.all_lines():
            self.create_line_models(order, line)
            if not basket.custom_ledger:
                self.update_stock_records(line)

        # Record any discounts associated with this order
        for application in basket.offer_applications:
            # Trigger any deferred benefits from offers and capture the
            # resulting message
            application['message'] \
                = application['offer'].apply_deferred_benefit(basket, order,
                                                              application)
            # Record offer application results
            if application['result'].affects_shipping:
                # Skip zero shipping discounts
                shipping_discount = shipping_method.discount(basket)
                if shipping_discount <= D('0.00'):
                    continue
                # If a shipping offer, we need to grab the actual discount off
                # the shipping method instance, which should be wrapped in an
                # OfferDiscount instance.
                application['discount'] = shipping_discount
            self.create_discount_model(order, application)
            self.record_discount(application)

        for voucher in basket.vouchers.all():
            self.record_voucher_usage(order, voucher, user)

        # Send signal for analytics to pick up
        order_placed.send(sender=self, order=order, user=user)

        return order    

    def create_line_models(self, order, basket_line, extra_line_fields=None):
        """
        Create the batch line model.
        You can set extra fields by passing a dictionary as the
        extra_line_fields value
        """
        product = basket_line.product
        stockrecord = basket_line.stockrecord
        if not stockrecord and not basket.custom_ledger:
            raise exceptions.UnableToPlaceOrder(
                "Baket line #%d has no stockrecord" % basket_line.id)
        if not basket.custom_ledger:
            partner = stockrecord.partner
        else:
            partner = None
        line_data = {
            'order': order,
            # Partner details
            'partner': partner if partner else None,
            'partner_name': partner.name if partner else None,
            'partner_sku': stockrecord.partner_sku  if partner else None,
            'stockrecord': stockrecord  if stockrecord else None,
            # Product details
            'product': product,
            'title': product.get_title(),
            'upc': product.upc,
            'quantity': basket_line.quantity,
            'oracle_code': product.oracle_code,
            # Price details
            'line_price_excl_tax':
            basket_line.line_price_excl_tax_incl_discounts,
            'line_price_incl_tax':
            basket_line.line_price_incl_tax_incl_discounts,
            'line_price_before_discounts_excl_tax':
            basket_line.line_price_excl_tax,
            'line_price_before_discounts_incl_tax':
            basket_line.line_price_incl_tax,
            # Reporting details
            'unit_cost_price': stockrecord.cost_price if stockrecord else basket_line.unit_price_incl_tax,
            'unit_price_incl_tax': basket_line.unit_price_incl_tax,
            'unit_price_excl_tax': basket_line.unit_price_excl_tax,
            'unit_retail_price': stockrecord.price_retail if stockrecord else basket_line.unit_price_incl_tax,
            # Shipping details
            'est_dispatch_date':
            basket_line.purchase_info.availability.dispatch_date
        }
        extra_line_fields = extra_line_fields or {}
        if hasattr(settings, 'OSCAR_INITIAL_LINE_STATUS'):
            if not (extra_line_fields and 'status' in extra_line_fields):
                extra_line_fields['status'] = getattr(
                    settings, 'OSCAR_INITIAL_LINE_STATUS')
        if extra_line_fields:
            line_data.update(extra_line_fields)

        order_line = Line._default_manager.create(**line_data)
        self.create_line_price_models(order, order_line, basket_line)
        self.create_line_attributes(order, order_line, basket_line)
        self.create_additional_line_models(order, order_line, basket_line)

        return order_line
