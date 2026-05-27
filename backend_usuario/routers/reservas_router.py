from fastapi import APIRouter, Depends, HTTPException, Header
from datetime import datetime, timedelta
from database import obter_conexao
from schemas.reservas_schema import ReservaCreate, ReservaResponse
from repositories.reservas_repository import ReservaRepository

router = APIRouter(prefix="/reservas", tags=["Reservas"])

# Dependência de Autenticação genérica
def obter_usuario_logado(x_user_id: int = Header(..., description="Simulação de Token JWT")):
    """
    Simula a extração da identidade do usuário logado a partir do cabeçalho
    (que seria normalmente obtida de um token JWT na vida real).
    """
    return x_user_id

@router.post("", response_model=ReservaResponse, status_code=201)
def comprar_reserva(
    reserva: ReservaCreate, 
    conexao = Depends(obter_conexao),
    usuario_logado: int = Depends(obter_usuario_logado)
):
    """
    Endpoint para realizar a compra de uma nova reserva de Zona Azul.
    Valida a identidade do usuário, o vínculo com o veículo, saldo disponível e
    conflitos de horário antes de efetuar a dedução e o registro.
    """
    # Proteção BOLA: O usuário não pode enviar um 'id_usuario' de outra pessoa no payload!
    if reserva.id_usuario != usuario_logado:
        raise HTTPException(status_code=403, detail="Acesso negado. O ID do payload difere da sua identidade JWT.")

    cursor = conexao.cursor()
    repo = ReservaRepository(cursor)
    try:
        cursor.execute("BEGIN;")

        # 1. Validação de Pertencimento
        if not repo.veiculo_pertence_ao_usuario(reserva.id_usuario, reserva.placa):
            raise HTTPException(status_code=403, detail="Veículo não cadastrado na garagem do usuário.")

        id_veiculo = repo.buscar_id_veiculo_por_placa(reserva.placa)
        if not id_veiculo:
            raise HTTPException(status_code=404, detail="Veículo não encontrado no sistema.")

        # 2. Cálculo
        valor_total = round((5.0 / 60.0) * reserva.duracao_minutos, 2)
        hora_inicio = datetime.now()
        hora_fim = hora_inicio + timedelta(minutes=reserva.duracao_minutos)

        # 3. Lock Saldo
        saldo_atual = repo.buscar_saldo_usuario_for_update(reserva.id_usuario)
        if saldo_atual is None:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        if float(saldo_atual) < valor_total:
            raise HTTPException(status_code=402, detail=f"Saldo insuficiente. Necessário: R${valor_total:.2f}")

        # 4. Lock Horário
        if repo.verificar_conflito_horario_for_update(id_veiculo, hora_inicio, hora_fim):
            raise HTTPException(status_code=409, detail="Veículo já possui uma reserva ativa neste período.")

        # 5. Dedução e Inserção
        repo.deduzir_saldo(reserva.id_usuario, valor_total)
        id_reserva = repo.inserir_reserva(
            reserva.id_usuario, id_veiculo, reserva.id_setor, 
            hora_inicio, hora_fim, valor_total
        )

        conexao.commit()
        
        return ReservaResponse(
            mensagem="Reserva efetuada com sucesso!",
            id_reserva=id_reserva,
            valor_pago=valor_total,
            hora_inicio=hora_inicio,
            hora_fim=hora_fim
        )

    except HTTPException:
        conexao.rollback()
        raise
    except Exception as e:
        conexao.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno: {e}")
    finally:
        cursor.close()
