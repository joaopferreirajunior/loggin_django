# Generated manually to avoid conflict with existing clinic_image field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0002_userclinic'),
    ]

    operations = [
        # ClinicData - Campos obrigatórios
        migrations.AddField(
            model_name='clinic',
            name='cpf_cnpj',
            field=models.CharField(default='', help_text='CPF ou CNPJ da clínica', max_length=20),
        ),
        migrations.AddField(
            model_name='clinic',
            name='trade_name',
            field=models.CharField(default='', help_text='Nome fantasia da clínica', max_length=255),
        ),
        # phone e email já existiam, apenas alterando para tornar obrigatórios
        migrations.AlterField(
            model_name='clinic',
            name='phone',
            field=models.CharField(default='', help_text='Telefone da clínica', max_length=20),
        ),
        migrations.AlterField(
            model_name='clinic',
            name='email',
            field=models.EmailField(default='', help_text='Email da clínica', max_length=254),
        ),
        
        # Address - Campos opcionais
        migrations.AddField(
            model_name='clinic',
            name='country',
            field=models.CharField(blank=True, help_text='Código do país (ex: BR)', max_length=2, null=True),
        ),
        migrations.AddField(
            model_name='clinic',
            name='zip_code',
            field=models.CharField(blank=True, help_text='CEP', max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='clinic',
            name='street',
            field=models.CharField(blank=True, help_text='Rua/Avenida', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='clinic',
            name='number',
            field=models.CharField(blank=True, help_text='Número', max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='clinic',
            name='district',
            field=models.CharField(blank=True, help_text='Bairro', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='clinic',
            name='city',
            field=models.CharField(blank=True, help_text='Cidade', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='clinic',
            name='state',
            field=models.CharField(blank=True, help_text='Estado (sigla)', max_length=2, null=True),
        ),
        migrations.AddField(
            model_name='clinic',
            name='time_zone',
            field=models.CharField(blank=True, default='America/Sao_Paulo', help_text='Fuso horário (ex: America/Sao_Paulo)', max_length=50, null=True),
        ),
        
        # BankData - Campos opcionais
        migrations.AddField(
            model_name='clinic',
            name='bank_code',
            field=models.CharField(blank=True, help_text='Código do banco (ex: 001 para Banco do Brasil)', max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='clinic',
            name='branch',
            field=models.CharField(blank=True, help_text='Agência bancária', max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='clinic',
            name='branch_digit',
            field=models.CharField(blank=True, help_text='Dígito verificador da agência', max_length=2, null=True),
        ),
        migrations.AddField(
            model_name='clinic',
            name='account_number',
            field=models.CharField(blank=True, help_text='Número da conta bancária', max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='clinic',
            name='account_digit',
            field=models.CharField(blank=True, help_text='Dígito verificador da conta', max_length=2, null=True),
        ),
        migrations.AddField(
            model_name='clinic',
            name='account_type',
            field=models.CharField(blank=True, choices=[('CHECKING', 'Conta Corrente'), ('SAVINGS', 'Conta Poupança')], help_text='Tipo da conta bancária', max_length=10, null=True),
        ),
        
        # clinic_image já existe, então não adicionar
        # Apenas garantir que está com as especificações corretas se necessário
    ]
