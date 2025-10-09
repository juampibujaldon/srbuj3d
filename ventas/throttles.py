from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class FileUploadRateThrottle(UserRateThrottle):
    scope = "order_file_upload"


class ShippingQuoteRateThrottle(UserRateThrottle):
    scope = "shipping_quote"


class ShippingQuoteAnonRateThrottle(AnonRateThrottle):
    scope = "shipping_quote_anon"
