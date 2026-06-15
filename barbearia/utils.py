"""
Utilitários de agendamento — geração de slots de 30 em 30 minutos.

A regra de negócio: o sistema trabalha APENAS com marcações em blocos fixos
de 30 minutos (08:00, 08:30, 09:00, …). Os horários disponíveis são determinados
pela Grade de Horários cadastrada para o barbeiro no dia da semana solicitado,
subtraindo os slots já ocupados (agendamentos ativos e bloqueios).
"""

from datetime import datetime, timedelta

from django.utils import timezone


def gerar_slots_disponiveis(data_obj, barbeiro, servico=None):
    """
    Retorna uma lista de ``datetime`` (naive, horário local) com todos os
    slots livres de 30 em 30 minutos para o barbeiro na data indicada.

    Parâmetros
    ----------
    data_obj : date
        Data para a qual gerar os slots.
    barbeiro : Barbeiro
        Instância do modelo Barbeiro.
    servico : Servico | None
        Se fornecido, considera a duração do serviço ao verificar conflitos.

    Retorna
    -------
    list[datetime]
        Slots disponíveis em ordem cronológica, somente no futuro.
    """
    # Importações locais evitam circular import pois utils pode ser importado
    # antes das apps estarem completamente carregadas.
    from .models import GradeHorario, Agendamento, HorarioBloqueado

    PASSO = 30  # minutos — blocos fixos do sistema

    # ── 1. Busca a grade do barbeiro para este dia da semana ──────────────────
    dia_semana = data_obj.weekday()  # 0 = Segunda … 6 = Domingo
    try:
        grade = GradeHorario.objects.get(barbeiro=barbeiro, dia_semana=dia_semana, ativo=True)
    except GradeHorario.DoesNotExist:
        return []  # barbeiro não trabalha neste dia

    # ── 2. Gera todos os slots da grade ──────────────────────────────────────
    duracao = servico.duracao_minutos if servico else PASSO
    inicio = datetime.combine(data_obj, grade.hora_inicio)
    fim = datetime.combine(data_obj, grade.hora_fim)

    todos_slots = []
    cur = inicio
    while cur + timedelta(minutes=duracao) <= fim:
        todos_slots.append(cur)
        cur += timedelta(minutes=PASSO)

    if not todos_slots:
        return []

    # ── 3. Monta conjunto de slots ocupados ──────────────────────────────────
    ocupados: set[datetime] = set()

    # 3a. Agendamentos ativos
    for ag in Agendamento.objects.filter(
        barbeiro=barbeiro,
        data_hora__date=data_obj,
        status__in=['agendado', 'confirmado', 'em_atendimento'],
    ).select_related('servico'):
        dur_ag = ag.servico.duracao_minutos if ag.servico else PASSO
        ag_local = timezone.localtime(ag.data_hora).replace(tzinfo=None)
        t = ag_local
        while t < ag_local + timedelta(minutes=dur_ag):
            ocupados.add(t)
            t += timedelta(minutes=PASSO)

    # 3b. Horários bloqueados
    for bl in HorarioBloqueado.objects.filter(barbeiro=barbeiro, data_inicio__date=data_obj):
        bl_start = timezone.localtime(bl.data_inicio).replace(tzinfo=None)
        bl_end = timezone.localtime(bl.data_fim).replace(tzinfo=None)
        t = bl_start
        while t < bl_end:
            ocupados.add(t)
            t += timedelta(minutes=PASSO)

    # ── 4. Filtra passados e ocupados ────────────────────────────────────────
    agora_naive = timezone.localtime(timezone.now()).replace(tzinfo=None)
    return [s for s in todos_slots if s not in ocupados and s > agora_naive]
