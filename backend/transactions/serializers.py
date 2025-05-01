from rest_framework import serializers
from .models import TransactionType, Transaction, TransactionDetail
from bank_accounts.serializers import BankAccountSerializer
from bank_accounts.models import BankAccount



class TransactionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionType
        fields = '__all__'
        read_only_fields = ('type_id',)



class TransactionDetailSerializer(serializers.ModelSerializer):
    bank_account = BankAccountSerializer(read_only=True)
    bank_account_id = serializers.PrimaryKeyRelatedField(
        queryset=BankAccount.objects.all(),
        source='bank_account',
        write_only=True
    )

    class Meta:
        model = TransactionDetail
        fields = [
            'id',
            'transaction',
            'bank_account',
            'bank_account_id',
            'amount'
        ]
        read_only_fields = ('id', 'transaction')
        extra_kwargs = {
            'transaction': {'required': False}
        }



class TransactionSerializer(serializers.ModelSerializer):
    type = TransactionTypeSerializer(read_only=True) 
    type_id = serializers.PrimaryKeyRelatedField(
        queryset=TransactionType.objects.all(),
        source='type',
        write_only=True
    )
    
    details = TransactionDetailSerializer(many=True)

    class Meta:
        model = Transaction
        fields = [
            'transaction_id',
            'type',
            'type_id',
            'created_at',
            'status',
            'description',
            'details'
        ]
        read_only_fields = ('transaction_id', 'created_at')

    def create(self, validated_data):
        details_data = validated_data.pop('details') 
        transaction = Transaction.objects.create(**validated_data)
        
        for detail_data in details_data:
            TransactionDetail.objects.create(
                transaction=transaction,
                bank_account=detail_data['bank_account'],
                amount=detail_data['amount']
            )
        
        return transaction
