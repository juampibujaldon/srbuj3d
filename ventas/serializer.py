from rest_framework import serializers
from .models import *
from .models import Order

class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'nombre', 'descripcion', 'precio', 'stock']

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'

class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['id', 'user', 'product', 'cantidad']
        read_only_fields = ['user']
        
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sell #! Payment
        fields = '__all__'

class STLModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = STLModel
        fields = '__all__'


class SellSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sell
        fields = '__all__'

class OrderPanelSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='product.nombre', read_only=True)
    producto_imagen = serializers.ImageField(source='product.imagen', read_only=True)
    cliente_nombre = serializers.CharField(source='user.get_full_name', read_only=True)
    envio_tipo = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id',
            'producto_nombre',
            'producto_imagen',
            'cliente_nombre',
            'fecha',
            'estado',
            'envio_tipo',
        ]

    def get_envio_tipo(self, obj):
        # Suponiendo que tienes un campo 'direccion' o 'ciudad' en el usuario o la orden
        if hasattr(obj, 'direccion_envio') and 'san rafael' in obj.direccion_envio.lower():
            return 'envío local'
        return 'envío nacional'

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = '__all__'

class WishlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = '__all__'
        read_only_fields = ['user']