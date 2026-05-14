from django.db import models

class Funcionario(models.Model):
    # DADOS PESSOAIS E PROFISSIONAIS
    registro_interno = models.CharField(max_length=50, unique=True, verbose_name="Registro Interno")
    nome = models.CharField(max_length=200, verbose_name="Nome Completo")
    cargo = models.CharField(max_length=100)
    data_admissao = models.DateField(verbose_name="Data de Admissão")
    cpf = models.CharField(max_length=14, unique=True, verbose_name="CPF")
    rg = models.CharField(max_length=20, verbose_name="RG")
    
    # CONTATO
    telefone = models.CharField(max_length=20)
    email = models.EmailField()
    
    # ENDEREÇO
    cep = models.CharField(max_length=9, verbose_name="CEP")
    endereco = models.CharField(max_length=255, verbose_name="Endereço Completo")
    numero = models.CharField(max_length=20, verbose_name="Número")
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    
    # DADOS BANCÁRIOS
    banco = models.CharField(max_length=100, verbose_name="Nome do Banco")
    agencia = models.CharField(max_length=20, verbose_name="Agência")
    conta = models.CharField(max_length=30, verbose_name="Conta com Dígito")

    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome} - {self.cargo}"

class Documento(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=150, verbose_name="Título do Documento")
    arquivo = models.FileField(upload_to='documentos/')
    data_upload = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} ({self.funcionario.nome})"
    
class Entregador(models.Model):
    nome = models.CharField(max_length=200, verbose_name="Nome Completo")
    cpf = models.CharField(max_length=14, unique=True, verbose_name="CPF")
    telefone = models.CharField(max_length=20)
    cnh = models.CharField(max_length=20, verbose_name="Número da CNH")
    veiculo = models.CharField(max_length=50, verbose_name="Veículo (Ex: Moto, Carro, Van)")
    placa = models.CharField(max_length=10, verbose_name="Placa do Veículo")
    foto = models.ImageField(upload_to='fotos_entregadores/', null=True, blank=True, verbose_name="Foto")
    ativo = models.BooleanField(default=True, verbose_name="Está ativo?")
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome} - {self.veiculo}"